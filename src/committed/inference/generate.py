"""
generate.py — baseline/fine-tune batch driver: run a model over the test split
and write candidate messages to a JSONL the eval harness consumes.

The per-diff inference primitive (load + prompt + grammar + decode) now lives in
`engine.CommitGenerator`; this file owns only the batch concerns: which rows to
run, resuming, and the id join-key. Serving and the Gradio demo call the same
CommitGenerator, so eval and serving cannot drift — that parity is what protects
the train/inference match.

CONTRACT: each candidate's `id` is the row's ORIGINAL test-split index, the join
key run_eval.py uses. Never re-index a sampled subset to 0..N.

Run from the repo root.
"""

import argparse
import json
import os
import random
import time
from pathlib import Path

from datasets import load_dataset

from committed.inference.engine import CommitGenerator

DATASET = "marzoukbaig14/committed-train"
SPLIT = "test"
SEED = 7
# Batch runs use the local models/ cache by default (ADR 0038); serving resolves
# the model from the Hub instead. Override either with COMMITTED_MODEL_PATH.
DEFAULT_MODEL_PATH = "models/Qwen3-1.7B-Q4_K_M.gguf"


def already_done(out_path: Path) -> set[int]:
    done = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["id"])
    return done


def select_ids(n_rows: int, ids_file: str | None, limit: int, seed: int) -> list[int]:
    if ids_file:
        return [int(x) for x in json.loads(Path(ids_file).read_text())]
    rng = random.Random(seed)
    return sorted(rng.sample(range(n_rows), min(limit, n_rows)))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="analysis/results/baseline_candidates.jsonl")
    p.add_argument("--ids-file", default=None)
    p.add_argument("--limit", type=int, default=500)
    p.add_argument("--seed", type=int, default=SEED)
    args = p.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    test = load_dataset(DATASET, split=SPLIT)
    ids = select_ids(len(test), args.ids_file, args.limit, args.seed)
    done = already_done(out_path)
    todo = [i for i in ids if i not in done]
    print(f"{len(test)} test rows | {len(ids)} selected | {len(done)} done | {len(todo)} to do")

    model_path = os.environ.get("COMMITTED_MODEL_PATH", DEFAULT_MODEL_PATH)
    gen = CommitGenerator(model_path=model_path, seed=args.seed)

    start = time.time()
    with out_path.open("a") as f:
        for n, i in enumerate(todo, 1):
            message = gen.generate(test[i]["diff"])
            f.write(json.dumps({"id": i, "message": message}) + "\n")
            f.flush()

            if n % 20 == 0 or n == len(todo):
                rate = n / (time.time() - start)
                print(f"  {n}/{len(todo)}  ({rate:.2f} rows/s)")

    print(f"done: wrote candidates to {out_path}")


if __name__ == "__main__":
    main()
