"""
analysis/token_dist.py

Measure the token-length distribution of Committed's training examples so
max_seq_length is chosen from real percentiles, not guessed. Prints tables to
the terminal and saves a figure + text summary under analysis/results/.

Run:  uv run --no-sync python analysis/token_dist.py
Then paste the printed tables back into the chat.
"""

from committed.inference.prompt import build_messages

import random
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless; we only save files, no window
import matplotlib.pyplot as plt
from datasets import load_dataset
from transformers import AutoTokenizer

MODEL = "Qwen/Qwen3-1.7B"
DATASET = "marzoukbaig14/committed-train"
SPLIT = "train"
SAMPLE = 8000              # rows to sample for speed; None = whole split
SEED = 3407
CANDIDATE_CAPS = (512, 768, 1024, 1536, 2048)
OUTDIR = Path("analysis/results")

# The prompt the model actually sees. REPLACE with your real frozen prompt (the
# baseline one) so the counts match what training feeds. If you have
# src/committed/inference/prompt.py, import and use that builder instead.
INSTRUCTION = (
    "Write a Conventional Commits message for the following diff.\n\n"
    "Diff:\n{diff}"
)


def build_lengths(tok, diff, message):
    msgs = build_messages(diff)
    prompt_str = tok.apply_chat_template(
        msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    full_str = tok.apply_chat_template(
        msgs + [{"role": "assistant", "content": message}],
        tokenize=False, enable_thinking=False)
    p_len = len(tok(prompt_str, add_special_tokens=False)["input_ids"])
    f_len = len(tok(full_str, add_special_tokens=False)["input_ids"])
    return p_len, f_len, f_len - p_len

def pct(arr, ps=(50, 90, 95, 99, 100)):
    return {p: int(np.percentile(arr, p)) for p in ps}


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(MODEL)
    ds = load_dataset(DATASET, split=SPLIT)
    if SAMPLE and SAMPLE < len(ds):
        random.seed(SEED)
        ds = ds.select(random.sample(range(len(ds)), SAMPLE))

    prompt, full, target = [], [], []
    for row in ds:
        p, f, t = build_lengths(tok, row["diff"], row["message"])
        prompt.append(p); full.append(f); target.append(t)
    full_arr = np.array(full)

    # ---- text report ----
    lines = [f"sampled {len(full)} rows from {DATASET}:{SPLIT}", ""]
    for name, arr in [("full (prompt+target)", full), ("prompt only", prompt), ("target only", target)]:
        p = pct(arr)
        lines.append(f"{name:22s}  p50={p[50]:5d}  p90={p[90]:5d}  p95={p[95]:5d}  p99={p[99]:5d}  max={p[100]:5d}")
    lines += ["", "coverage at candidate max_seq_length:"]
    for cap in CANDIDATE_CAPS:
        lines.append(f"  {cap:5d}: keeps {100 * np.mean(full_arr <= cap):5.1f}% of examples")
    report = "\n".join(lines)
    print(report)
    (OUTDIR / "token_dist.txt").write_text(report)

    # ---- figure: length histogram + coverage curve ----
    p95, p99 = np.percentile(full_arr, 95), np.percentile(full_arr, 99)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    ax1.hist(full_arr, bins=60, color="#1D9E75", alpha=0.85)
    ax1.axvline(p95, color="#BA7517", linestyle="--", label=f"p95 = {int(p95)}")
    ax1.axvline(p99, color="#A32D2D", linestyle="--", label=f"p99 = {int(p99)}")
    ax1.set_title("full example length (prompt + target)")
    ax1.set_xlabel("tokens"); ax1.set_ylabel("examples"); ax1.legend()

    caps = np.arange(256, full_arr.max() + 64, 32)
    cov = [100 * np.mean(full_arr <= c) for c in caps]
    ax2.plot(caps, cov, color="#185FA5")
    for c in CANDIDATE_CAPS:
        ax2.axvline(c, color="#888780", linestyle=":", linewidth=0.8)
    ax2.set_title("coverage vs max_seq_length")
    ax2.set_xlabel("max_seq_length (tokens)"); ax2.set_ylabel("% examples kept")
    ax2.set_ylim(0, 101)

    fig.tight_layout()
    fig.savefig(OUTDIR / "token_dist.png", dpi=130)
    print(f"\nsaved: {OUTDIR / 'token_dist.png'}  and  {OUTDIR / 'token_dist.txt'}")


if __name__ == "__main__":
    main()