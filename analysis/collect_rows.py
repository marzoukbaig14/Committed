"""
collect_rows.py — Full filter pass over CommitChronicle's train split.

Streams the entire train split once, runs the real filter (committed.data.filter),
and writes every kept row to data/committed_raw.jsonl (gitignored scratch). This is
the long pass — it reads all ~7.66M raw commits. Run it, let it stream, and watch the
periodic progress lines so you can see it is alive (not hung).

The output here is the UNBALANCED pool. Balancing (per-language cap) and the
train/val/eval split happen next in build.py, against the TRUE counts this prints at
the end — not the biased first-200k estimate.

Language is counted by FILE EXTENSION, never by CommitChronicle's repo `language`
column (which the filter ignores entirely, ADR 0022). The summary reports both the
mapped language and the raw extension so the extension-based counting is visible.

Run:  uv run python analysis/collect_rows.py
Out:  data/committed_raw.jsonl   + a printed per-language / per-extension / per-type summary
"""

import json
import os
import time
from collections import Counter

from datasets import load_dataset

# _single_file_path is the filter's own path helper — reused here (not re-implemented)
# so the extension count is taken from the exact same path the filter used.
from committed.data.filter import build_row, _single_file_path

OUT_PATH = "data/committed_raw.jsonl"
REPORT_EVERY = 500_000          # progress cadence, in raw records scanned

os.makedirs("data", exist_ok=True)

ds = load_dataset("JetBrains-Research/commit-chronicle", split="train", streaming=True)

langs = Counter()    # mapped language (from extension)
exts = Counter()     # raw file extension (pre-mapping)
types = Counter()    # conventional-commit type
kept = 0
scanned = 0
start = time.time()

# Write rows incrementally so a crash still leaves a usable partial file.
with open(OUT_PATH, "w") as out:
    for record in ds:
        scanned += 1
        row = build_row(record)
        if row is not None:
            out.write(json.dumps(row) + "\n")
            kept += 1
            langs[row["language"]] += 1
            # raw extension, taken from the same path the filter resolved
            ext = os.path.splitext(_single_file_path(record))[1].lower() or "(none)"
            exts[ext] += 1
            # commit type = text before the first '(' or ':' in the normalized message
            ctype = row["message"].split("(")[0].split(":")[0]
            types[ctype] += 1
        if scanned % REPORT_EVERY == 0:
            mins = (time.time() - start) / 60
            print(f"  scanned {scanned:>10,} | kept {kept:>7,} "
                  f"| {kept / scanned * 100:5.2f}% | {mins:5.1f} min", flush=True)

mins = (time.time() - start) / 60
print(f"\nDONE: kept {kept:,} of {scanned:,} ({kept / scanned * 100:.3f}%) in {mins:.1f} min")
print(f"written to {OUT_PATH}\n")

print("by language (mapped from extension):")
for lang, n in langs.most_common():
    print(f"  {lang:14} {n:7,}  ({100 * n / kept:4.1f}%)")

print("\nby raw extension:")
for ext, n in exts.most_common():
    print(f"  {ext:10} {n:7,}  ({100 * n / kept:4.1f}%)")

print("\nby commit type:")
for t, n in types.most_common():
    print(f"  {t:10} {n:7,}  ({100 * n / kept:4.1f}%)")

# HF streaming teardown can hang; exit cleanly now that the file is closed and flushed.
os._exit(0)