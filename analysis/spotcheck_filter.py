"""
spotcheck_filter.py — Eyeball the filter's real output before any full build.

Why this isn't a fixed 10k scan: CommitChronicle's `default` train split is ordered
by project, and the head of the stream is a single non-Python repo. A small shuffle
window never escapes it, so a fixed 10k scan can come back with almost no Python.
There is no per-language config to load (configs are `default` / `subset_cmg`, and
language is a column, not a config). So instead we scan DEEPER until we've collected
TARGET_KEPT rows (or hit SCAN_CAP as a safety valve) — which naturally traverses past
the non-Python head into Python projects.

PREREQUISITE: filter.py is filled in.
Run:    uv run python analysis/spotcheck_filter.py
Output: printed AND saved to analysis/results/spotcheck.txt
"""

import os
from pathlib import Path

from datasets import load_dataset

from committed.data.filter import build_row

TARGET_KEPT = 40         # how many kept rows to collect for review
SCAN_CAP = 300_000       # safety cap on raw records scanned (bounds wall-clock)
OUT = Path("analysis/results/spotcheck.txt")

ds = load_dataset("JetBrains-Research/commit-chronicle", split="train", streaming=True)
ds = ds.shuffle(buffer_size=10_000, seed=0)   # local mixing; the deep scan does the real work

kept = []
scanned = 0
for record in ds:
    scanned += 1
    row = build_row(record)
    if row is not None:
        kept.append(row)
        if len(kept) >= TARGET_KEPT:
            break
    if scanned >= SCAN_CAP:
        break

rate = (100 * len(kept) / scanned) if scanned else 0.0
lines = [f"kept {len(kept)} rows after scanning {scanned} ({rate:.2f}% kept)", ""]
for row in kept:
    lines.append("=" * 70)
    lines.append(f"MESSAGE: {row['message']}")
    lines.append("DIFF (first 600 chars):")
    lines.append(row["diff"][:600])
    lines.append("")

report = "\n".join(lines)
print(report)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(report)
print(f"[saved to {OUT}]")

# Streaming throws a cosmetic fatal error at interpreter exit; bail cleanly.
os._exit(0)