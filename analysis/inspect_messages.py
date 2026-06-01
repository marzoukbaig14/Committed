import os
from datasets import load_dataset # the HuggingFace purpose built Lib

# laod the dataset 
ds = load_dataset("JetBrains-Research/commit-chronicle", split="train", streaming=True)

N = 20
colon_orig = colon_clean = 0

for i, row in enumerate(ds):
    if i >= N:
        break
    orig, clean = row["original_message"], row["message"]
    colon_orig += (": " in orig)
    colon_clean += (": " in clean)
    print(f"--- {i}  lang={row['language']}  files={len(row['mods'])} ---")
    print(f"  original: {orig!r}")
    print(f"  message : {clean!r}")
    print()

print(f"Of {N}: ': ' present in {colon_orig} originals, {colon_clean} cleaned")
os._exit(0)