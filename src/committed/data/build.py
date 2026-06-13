"""
build.py — Balance the row pool and create the 90/5/5 train/val/eval split.

Runs AFTER collect_rows.py produces data/committed_raw.jsonl.
Reads the pool, applies the per-language cap and floor (ADR 0025), then
writes train/val/eval JSONL splits to data/.

Build-time parameters (ADR 0025 defaults, all reversible):
  CAP   = 6,000   rows per language  (downsample above this)
  FLOOR = 500     rows per language  (drop below this)

Run:
  uv run python src/committed/data/build.py --dry-run       # plan only, no output files
  uv run python src/committed/data/build.py                  # full build
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_CAP = 6_000
DEFAULT_FLOOR = 500
DEFAULT_POOL = Path("data/committed_raw.jsonl")
DEFAULT_OUT = Path("data")
VAL_FRAC = 0.05
EVAL_FRAC = 0.05
SEED = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _commit_type(message: str) -> str:
    """Type prefix from a normalized CC message (text before '(' or ':')."""
    return message.split("(")[0].split(":")[0]


# ---------------------------------------------------------------------------
# Cap / floor
# ---------------------------------------------------------------------------

def apply_cap_and_floor(
    rows: list[dict],
    cap: int = DEFAULT_CAP,
    floor: int = DEFAULT_FLOOR,
    seed: int = SEED,
) -> list[dict]:
    """Drop languages with fewer than `floor` pool rows; randomly downsample
    languages with more than `cap` rows.  Deterministic given the same seed."""
    lang_counts = Counter(r["language"] for r in rows)
    kept_langs = {lang for lang, n in lang_counts.items() if n >= floor}

    by_lang: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row["language"] in kept_langs:
            by_lang[row["language"]].append(row)

    rng = random.Random(seed)
    result: list[dict] = []
    for lang_rows in by_lang.values():
        if len(lang_rows) > cap:
            result.extend(rng.sample(lang_rows, cap))
        else:
            result.extend(lang_rows)
    return result


# ---------------------------------------------------------------------------
# Stratified split
# ---------------------------------------------------------------------------

def _split_by_key(
    rows: list[dict],
    key_fn,
    val_frac: float,
    eval_frac: float,
    seed: int,
) -> tuple[list[dict], list[dict], list[dict]]:
    rng = random.Random(seed)
    by_key: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_key[key_fn(row)].append(row)

    train: list[dict] = []
    val: list[dict] = []
    eval_: list[dict] = []
    for group in by_key.values():
        shuffled = group[:]
        rng.shuffle(shuffled)
        n = len(shuffled)
        if n < 3:
            train.extend(shuffled)
            continue
        n_eval = max(1, round(n * eval_frac))
        n_val = max(1, round(n * val_frac))
        eval_.extend(shuffled[:n_eval])
        val.extend(shuffled[n_eval : n_eval + n_val])
        train.extend(shuffled[n_eval + n_val :])
    return train, val, eval_


def make_split(
    rows: list[dict],
    val_frac: float = VAL_FRAC,
    eval_frac: float = EVAL_FRAC,
    seed: int = SEED,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Return (train, val, eval_) via a type-stratified split.

    Stratify by commit type only: type is heavily skewed (fix ~51%) and we report
    per-type metrics, so it must be balanced across splits. Language is already
    balanced by the per-language cap (ADR 0025), so a plain split gives each
    language a proportional eval slice without finer stratification — which also
    avoids the thin type×language cell problem entirely.
    """
    def key_fn(r):
        return _commit_type(r["message"])
    print("stratification key: type")
    return _split_by_key(rows, key_fn, val_frac, eval_frac, seed)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_summary(label: str, rows: list[dict]) -> None:
    if not rows:
        print(f"\n{label}  (0 rows)")
        return
    lang_counts = Counter(r["language"] for r in rows)
    type_counts = Counter(_commit_type(r["message"]) for r in rows)
    print(f"\n{label}  ({len(rows):,} rows)")
    print("  by language:")
    for lang, n in lang_counts.most_common():
        print(f"    {lang:<14} {n:>7,}  ({100 * n / len(rows):4.1f}%)")
    print("  by commit type:")
    for t, n in type_counts.most_common():
        print(f"    {t:<10} {n:>7,}  ({100 * n / len(rows):4.1f}%)")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    print(f"  wrote {len(rows):,} rows → {path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pool", default=DEFAULT_POOL, type=Path,
                    help="input JSONL pool (default: data/committed_raw.jsonl)")
    ap.add_argument("--out", default=DEFAULT_OUT, type=Path,
                    help="output directory for train/val/eval JSONL (default: data/)")
    ap.add_argument("--cap", default=DEFAULT_CAP, type=int,
                    help=f"per-language row cap (default: {DEFAULT_CAP})")
    ap.add_argument("--floor", default=DEFAULT_FLOOR, type=int,
                    help=f"per-language row floor (default: {DEFAULT_FLOOR})")
    ap.add_argument("--dry-run", action="store_true",
                    help="print plan and counts; write no output files")
    args = ap.parse_args()

    print(f"reading pool from {args.pool} …")
    rows: list[dict] = []
    with open(args.pool, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    print(f"  pool: {len(rows):,} rows")

    balanced = apply_cap_and_floor(rows, cap=args.cap, floor=args.floor)
    _print_summary(f"after cap={args.cap:,} / floor={args.floor}", balanced)

    train, val, eval_ = make_split(balanced)
    print(f"\nsplit: train {len(train):,}  val {len(val):,}  eval {len(eval_):,}")

    if args.dry_run:
        print("\n(dry run — no files written)")
        return

    _write_jsonl(args.out / "train.jsonl", train)
    _write_jsonl(args.out / "val.jsonl", val)
    _write_jsonl(args.out / "eval.jsonl", eval_)


if __name__ == "__main__":
    main()
