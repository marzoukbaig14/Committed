"""Token-length distribution of raw diffs and messages, in Qwen3 tokens (Day 2).
Sets the diff token cap you choose on Day 3.
Run: uv run python notebooks/diff_token_dist.py
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")                       # no display in a Codespace; render to a PNG
import matplotlib.pyplot as plt
from datasets import load_dataset
from transformers import AutoTokenizer

DATASET = "JetBrains-Research/commit-chronicle"
MODEL = "Qwen/Qwen3-1.7B"
N_ALL = 5000          # general sample across all 20 languages (plenty for percentiles)
TARGET_PY1 = 4000     # Python single-file commits to collect (the population we'll train on)
MAX_SCAN = 200_000    # hard stop so we never stream forever

tok = AutoTokenizer.from_pretrained(MODEL)
ds = load_dataset(DATASET, split="train", streaming=True).shuffle(seed=0, buffer_size=10_000)

def full_diff(ex):
    return "\n".join(m["diff"] for m in ex["mods"] if m["diff"])

def n_tokens(text):
    return len(tok(text, add_special_tokens=False)["input_ids"])

diff_all, msg_all = [], []
diff_py1, msg_py1 = [], []
scanned = 0
for ex in ds:
    scanned += 1
    is_py1 = ex["language"] == "Python" and len(ex["mods"]) == 1
    in_all = len(diff_all) < N_ALL
    if is_py1 or in_all:                       # only tokenize rows we actually keep
        d, m = n_tokens(full_diff(ex)), n_tokens(ex["message"])
        if in_all:
            diff_all.append(d); msg_all.append(m)
        if is_py1:
            diff_py1.append(d); msg_py1.append(m)
    if scanned % 20_000 == 0:                  # progress, so a long scan doesn't look frozen
        print(f"  scanned {scanned}... python-1file collected: {len(diff_py1)}", flush=True)
    if len(diff_py1) >= TARGET_PY1 or scanned >= MAX_SCAN:
        break

def describe(name, arr):
    a = np.array(arr)
    if a.size == 0:
        print(f"{name:<28} n=0  (none collected)"); return
    p = np.percentile(a, [50, 75, 90, 95, 99])
    print(f"{name:<28} n={a.size:>5}  med={p[0]:>6.0f}  p75={p[1]:>6.0f}  "
          f"p90={p[2]:>6.0f}  p95={p[3]:>6.0f}  p99={p[4]:>6.0f}  max={a.max():>7.0f}")

print(f"\nScanned {scanned} commits. Tokenizer: {MODEL}.\n")
describe("diff tokens (all langs)", diff_all)
describe("message tokens (all langs)", msg_all)
print()
describe("diff tokens (python, 1-file)", diff_py1)
describe("message tokens (python, 1-file)", msg_py1)

fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].hist(np.clip(diff_py1, 0, 2000), bins=60)
ax[0].set_title("Python 1-file diff tokens (clipped 2000)"); ax[0].set_xlabel("tokens"); ax[0].set_ylabel("commits")
ax[1].hist(np.clip(msg_py1, 0, 80), bins=40)
ax[1].set_title("Python 1-file message tokens (clipped 80)"); ax[1].set_xlabel("tokens")
fig.tight_layout()
fig.savefig("notebooks/token_distribution.png", dpi=120)
print("\nWrote notebooks/token_distribution.png — open it from the VS Code file explorer.")

sys.stdout.flush()
os._exit(0)   # skip interpreter teardown to avoid the cosmetic streaming-thread crash