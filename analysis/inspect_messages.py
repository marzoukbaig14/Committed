import itertools
import os
import statistics
from collections import Counter
from datasets import load_dataset  # the HuggingFace purpose built Lib

# load the dataset
ds = load_dataset("JetBrains-Research/commit-chronicle", split="train", streaming=True)

data_iter = iter(ds)

# print the dataset columns and message-related field types
print("Dataset column names:")
if hasattr(ds, "column_names"):
    print(" ", ds.column_names)
else:
    print("  (column names unavailable from streaming dataset)")

sample = next(data_iter)
print("\nSample field names and types:")
for key, value in sample.items():
    print(f"  {key}: {type(value).__name__}")

message_fields = [k for k in sample.keys() if "message" in k.lower()]
print("\nMessage-related fields:")
for key in message_fields:
    print(f"  {key}: {type(sample[key]).__name__}")

subject_lengths = Counter()
N = 10000  # how many rows to analyze for the subject line length distribution and colon presence
colon_orig = colon_clean = 0

for i, row in enumerate(itertools.chain([sample], data_iter)):
    if i >= N:
        break
    orig, clean = row["original_message"], row["message"]
    subject = clean.splitlines()[0] if isinstance(clean, str) else str(clean)
    subject_lengths[len(subject)] += 1
    colon_orig += (": " in orig)
    colon_clean += (": " in clean)
    # Legacy debug output: keep these commented for reference
    # print(f"--- {i}  lang={row['language']}  files={len(row['mods'])} ---")
    # print(f"  original: {orig!r}")
    # print(f"  message : {clean!r}")
    # print(f" author: {row['author']}  date={row['date']}")
    # print()

print(f"Of {N}: ': ' present in {colon_orig} originals, {colon_clean} cleaned")

if subject_lengths:
    count = sum(subject_lengths.values())
    elems = list(subject_lengths.elements())
    print(f"\nSubject length distribution (first {count} rows):")
    print(f"  min={min(subject_lengths)}, max={max(subject_lengths)}, mean={statistics.mean(elems):.1f}, median={statistics.median(elems)}")
    print("  most common lengths:")
    for length, freq in subject_lengths.most_common(20):
        print(f"    {length:3d} chars: {freq}")
os._exit(0)