"""
Pull a small sample of test-split examples for eyeballing the judge BEFORE a full run.

Writes {id, diff, message} where `message` is the GOLD commit message, used as a stand-in
candidate. This lets you validate the judge's reasoning against the rubric now, before any model
generations exist. Plumbing — not core eval logic.

Usage:
  uv run python scripts/make_judge_check.py            # 12 seeded-random test examples
  uv run python scripts/make_judge_check.py --n 20 --seed 7
"""

import argparse
import json
import random

from datasets import load_dataset


def main() -> None:
    ap = argparse.ArgumentParser(description="Sample test-split (diff, gold) pairs to a JSONL.")
    ap.add_argument("--dataset", default="marzoukbaig14/committed-train")
    ap.add_argument("--split", default="test")
    ap.add_argument("--n", type=int, default=12, help="How many examples to pull.")
    ap.add_argument("--seed", type=int, default=0, help="Shuffle seed (fixed = reproducible sample).")
    ap.add_argument("--out", default="judge_check_input.jsonl")
    args = ap.parse_args()

    ds = load_dataset(args.dataset, split=args.split)
    idx = list(range(len(ds)))
    random.seed(args.seed)
    random.shuffle(idx)
    picks = idx[: args.n]

    with open(args.out, "w") as f:
        for i in picks:
            row = ds[i]
            f.write(json.dumps({"id": str(i), "diff": row["diff"], "message": row["message"]}) + "\n")

    print(f"wrote {len(picks)} examples to {args.out} (split={args.split}, seed={args.seed})")


if __name__ == "__main__":
    main()