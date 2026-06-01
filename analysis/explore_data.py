"""Explore CommitChronicle before writing any filters (Day 2, load + inspect).
Run: uv run python notebooks/explore_data.py
Read-only inspection. No filtering logic here — that's Day 3, and it's yours.
"""
from itertools import islice
from datasets import load_dataset

DATASET = "JetBrains-Research/commit-chronicle"

# streaming=True returns an IterableDataset: rows are pulled over the network on
# demand, so we never download the full 14.4 GB just to look at a few rows.
ds = load_dataset(DATASET, split="train", streaming=True)

# The stream is ordered by repository (long runs from one project). Sampling the
# head would only see the first repos, so shuffle a buffer first. buffer_size is
# how many rows are held in memory to sample from: bigger = more representative.
ds = ds.shuffle(seed=0, buffer_size=10_000)

sample = list(islice(ds, 25))  # one network pass; reused below

print("=" * 80)
print("STRUCTURE OF 3 EXAMPLES")
print("=" * 80)
for ex in sample[:3]:
    print("keys:", list(ex.keys()))
    print("language:", ex["language"], "| license:", ex["license"], "| repo:", ex["repo"])
    print("message:", repr(ex["message"]))
    print("n mods (files changed):", len(ex["mods"]))
    first = ex["mods"][0]
    print("first mod keys:", list(first.keys()))
    print("first mod change_type:", first["change_type"], "| new_path:", first["new_path"])
    print("first mod diff (first 400 chars):")
    print(first["diff"][:400])
    print("-" * 80)

print("=" * 80)
print("SKIM: 25 messages + shape signals")
print("=" * 80)
single_file = python = 0
for ex in sample:
    n = len(ex["mods"])
    single_file += (n == 1)
    python += (ex["language"] == "Python")
    flag = "1-file" if n == 1 else f"{n}-file"
    print(f"[{ex['language']:<12}] [{flag:>7}] {ex['message'][:80]!r}")
print("-" * 80)
print(f"of 25: single-file={single_file}, python={python}")