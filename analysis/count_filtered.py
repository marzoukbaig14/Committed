"""
count_filtered.py — Estimate the filtered dataset size before the full build.

Streams N raw records, runs the real filter, and reports the pass rate plus a
projection over the full train split. This is an ESTIMATE — the exact count falls
out of the full build pass (which filters every record anyway), so don't run two
full passes. Use this first to check we land near the 15-25k target before
committing to the long run, especially now that the per-repo `language` field
turned out to overcount Python.

CommitChronicle is ordered by project, so a small window is dominated by a few
repos — bigger SCAN = better estimate. 200k spans a few hundred repos; bump it
toward 500k-1M if you want the projection tighter (it just takes longer).

Run:  uv run python analysis/count_filtered.py
"""

import os

from datasets import load_dataset

from committed.data.filter import build_row

TRAIN_SIZE = 7_660_000   # full train split (CommitChronicle dataset card)
SCAN = 200_000           # raw records to scan for the estimate

ds = load_dataset("JetBrains-Research/commit-chronicle", split="train", streaming=True)

passed = 0
scanned = 0
for record in ds:
    scanned += 1
    if build_row(record) is not None:
        passed += 1
    if scanned >= SCAN:
        break

rate = passed / scanned if scanned else 0.0
print(f"passed {passed:,} of {scanned:,} scanned = {rate * 100:.3f}%")
print(f"projected over {TRAIN_SIZE:,} train commits  =  ~{int(rate * TRAIN_SIZE):,} rows")

os._exit(0)