"""
spotcheck_filter.py — Eyeball the filter's real output before any full build.

Runs your finished filter over a shuffled slice of CommitChronicle and prints a
random sample of kept rows so you can read them by hand: are good commits kept,
junk/bots dropped, and do the targets look like things you'd want the model to
produce? (This is also where you see the cleaned-message tokens, for the parked
message-vs-original_message decision.)

PREREQUISITE: filter.py is filled in — this just runs your logic.
Run:    uv run python analysis/spotcheck_filter.py
Output: printed to the terminal AND saved to analysis/results/spotcheck.txt
"""

import os
import random
from pathlib import Path

from datasets import load_dataset

from committed.data.filter import filter_stream

RAW_LIMIT = 10_000   # how many raw records to scan
N_SAMPLES = 30       # how many kept rows to print/save for review
OUT = Path("analysis/results/spotcheck.txt")

# Load streaming. Match this to the working load in inspect_messages.py if it differs.
ds = load_dataset("JetBrains-Research/commit-chronicle", split="train", streaming=True)

# Shuffle before sampling: CommitChronicle is stored by-project, so the HEAD of the
# stream is one repo's commits in a block (why author 331280 kept repeating in your
# earlier scan). Without this, a spot-check sees one repo, not the dataset.
ds = ds.shuffle(buffer_size=10_000, seed=0)

# Run YOUR filter over the slice.
rows = list(filter_stream(ds, limit=RAW_LIMIT))

# Build the report once, then both print and save it.
lines = [
    f"kept {len(rows)} rows from {RAW_LIMIT} scanned "
    f"({100 * len(rows) / RAW_LIMIT:.1f}%)",
    "",
]
for row in random.sample(rows, min(N_SAMPLES, len(rows))):
    lines.append("=" * 70)
    lines.append(f"MESSAGE: {row['message']}")
    lines.append("DIFF (first 600 chars):")
    lines.append(row["diff"][:600])
    lines.append("")

report = "\n".join(lines)
print(report)                                  # read live in the terminal

OUT.parent.mkdir(parents=True, exist_ok=True)  # durable copy alongside your other scans
OUT.write_text(report)
print(f"[saved to {OUT}]")

# Streaming throws a cosmetic fatal error at interpreter exit; bail cleanly.
os._exit(0)