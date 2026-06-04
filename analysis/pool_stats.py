"""
pool_stats.py - distribution stats for the collected row pool.

Reads a JSONL row pool (default: data/committed_raw.jsonl) where each line is one
filtered commit row produced by collect_rows.py:
    {diff, message, reasoning_trace, repo, license, language}

Reports the *size and shape* of the pool so we can:
  - sanity-check the filter output (are subjects / diffs the size we expect?),
  - see the real language mix (by extension-derived `language`, per ADR 0022,
    NOT the per-repo language attribute),
  - see commit-type coverage (eval needs every type represented),
  - confirm the diff token cap (TOKEN_CAP) is doing what we think it does.

Read-only analysis; it writes nothing. Point --path at any pool file, partial or full.
"""

import argparse
import json
import re
from collections import Counter

import numpy as np
from transformers import AutoTokenizer

# Tokenizer must match the model we fine-tune (MASTER.md), so token counts here
# line up with TOKEN_CAP and the training sequence length.
MODEL_NAME = "Qwen/Qwen3-1.7B"

# Percentile grid reused for every numeric distribution below.
PCTS = [0, 10, 25, 50, 75, 90, 95, 99, 100]


def load_rows(path):
    """Read a JSONL pool file into a list of dicts (one per kept commit)."""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def percentile_table(values, label):
    """Print a labeled percentile summary for a list of numbers."""
    arr = np.array(values)
    print(f"\n{label}  (n={len(arr):,})")
    print(f"  mean {arr.mean():.1f}   std {arr.std():.1f}")
    cells = "  ".join(f"p{p}={np.percentile(arr, p):.0f}" for p in PCTS)
    print(f"  {cells}")


def text_histogram(values, bins, label, width=40):
    """Print a simple text-bar histogram so the shape is visible at a glance."""
    counts, edges = np.histogram(values, bins=bins)
    top = counts.max() if counts.max() else 1
    print(f"\n{label}")
    for i, c in enumerate(counts):
        bar = "#" * int(width * c / top)
        print(f"  {edges[i]:>7.0f}-{edges[i + 1]:<7.0f} | {c:>7,} {bar}")


def commit_type(message):
    """Extract the conventional-commit type prefix (the word before '(' or ':')."""
    m = re.match(r"^([a-z]+)", message)
    return m.group(1) if m else "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default="data/committed_raw.jsonl",
                    help="JSONL row pool to analyze")
    ap.add_argument("--sample", type=int, default=0,
                    help="if >0, tokenize only this many random diffs (faster preview)")
    args = ap.parse_args()

    rows = load_rows(args.path)
    print(f"loaded {len(rows):,} rows from {args.path}")

    # --- subject (message) length, in characters ---
    # Filter bounds are 5-200 chars (ADR 0020); this shows where the mass sits.
    subj_chars = [len(r["message"]) for r in rows]
    percentile_table(subj_chars, "subject length (chars)")
    text_histogram(subj_chars, bins=np.linspace(0, 200, 21),
                   label="subject length histogram (chars)")

    # --- diff size, in lines (cheap: no tokenizer needed) ---
    diff_lines = [r["diff"].count("\n") + 1 for r in rows]
    percentile_table(diff_lines, "diff size (lines)")

    # --- diff size, in tokens (the budget that actually constrains the model) ---
    # Tokenizer-only load works without PyTorch installed.
    print("\nloading tokenizer (Qwen3-1.7B) for token counts...")
    tok = AutoTokenizer.from_pretrained(MODEL_NAME)

    diffs = [r["diff"] for r in rows]
    if args.sample and args.sample < len(diffs):
        idx = np.random.default_rng(0).choice(len(diffs), args.sample, replace=False)
        diffs = [diffs[i] for i in idx]
        print(f"  (tokenizing a random sample of {len(diffs):,} diffs)")

    # Batch-encode for speed; count tokens per diff without special tokens.
    diff_tokens = []
    BATCH = 1000
    for i in range(0, len(diffs), BATCH):
        enc = tok(diffs[i:i + BATCH], add_special_tokens=False)
        diff_tokens.extend(len(ids) for ids in enc["input_ids"])
    percentile_table(diff_tokens, "diff size (tokens)")
    text_histogram(diff_tokens, bins=np.linspace(0, max(diff_tokens), 21),
                   label="diff size histogram (tokens)")

    # --- language mix (extension-derived `language` field, per ADR 0022) ---
    langs = Counter(r.get("language", "?") for r in rows)
    print("\nlanguage mix (by file extension):")
    for lang, c in langs.most_common():
        print(f"  {lang:<14} {c:>8,}  {100 * c / len(rows):5.1f}%")

    # --- commit-type mix (eval needs coverage across types) ---
    types = Counter(commit_type(r["message"]) for r in rows)
    print("\ncommit-type mix:")
    for t, c in types.most_common():
        print(f"  {t:<10} {c:>8,}  {100 * c / len(rows):5.1f}%")


if __name__ == "__main__":
    main()