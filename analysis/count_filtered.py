"""
count_filtered.py — Estimate the filtered dataset size and language mix.

Streams N raw records, runs the real filter, and reports the pass rate, a
projection over the full train split, and the per-language breakdown of kept rows
(so the all-languages coverage and balance are visible before the build). This is
an ESTIMATE — the exact count falls out of the build pass; don't run two full passes.

Bigger SCAN = better estimate (CommitChronicle is ordered by project). 200k spans a
few hundred repos; bump toward 500k-1M to tighten it.

Run:  uv run python analysis/count_filtered.py
"""

import os
from collections import Counter

from datasets import load_dataset

from committed.data.filter import build_row

TRAIN_SIZE = 7_660_000   # full train split (CommitChronicle dataset card)
SCAN = 200_000           # raw records to scan for the estimate

ds = load_dataset("JetBrains-Research/commit-chronicle", split="train", streaming=True)

passed = 0
scanned = 0
langs = Counter()
for record in ds:
    scanned += 1
    row = build_row(record)
    if row is not None:
        passed += 1
        langs[row["language"]] += 1
    if scanned >= SCAN:
        break

rate = passed / scanned if scanned else 0.0
print(f"passed {passed:,} of {scanned:,} scanned = {rate * 100:.3f}%")
print(f"projected over {TRAIN_SIZE:,} train commits  =  ~{int(rate * TRAIN_SIZE):,} rows\n")
print("kept rows by language:")
for lang, n in langs.most_common():
    share = 100 * n / passed if passed else 0.0
    print(f"  {lang:14} {n:6,}  ({share:4.1f}%)")

os._exit(0)