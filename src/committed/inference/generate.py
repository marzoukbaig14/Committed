"""
generate.py — run the base model over the test set and write candidate messages.

Loads the GGUF model and the GBNF grammar, builds each prompt with
prompt.build_messages, renders it through the Qwen tokenizer with thinking
disabled, generates one constrained Conventional Commits line per diff, and
appends it to a JSONL candidates file. Resumable background job.

CONTRACT: each candidate's `id` is the row's ORIGINAL test-split index, the join
key run_eval.py uses. Never re-index a sampled subset to 0..N.

Run from the repo root.
"""

import argparse
import json
import random
import time
from pathlib import Path

from datasets import load_dataset
from llama_cpp import Llama, LlamaGrammar
from transformers import AutoTokenizer          # NEW: render the chat template ourselves

from committed.inference.prompt import build_messages

MODEL_PATH = "models/Qwen3-1.7B-Q4_K_M.gguf"
TOKENIZER_NAME = "Qwen/Qwen3-1.7B"               # NEW: tokenizer source for apply_chat_template
GRAMMAR_PATH = Path(__file__).parent / "grammar.gbnf"
DATASET = "marzoukbaig14/committed-train"
SPLIT = "test"
N_CTX = 4096
MAX_TOKENS = 128       # generous: capture true message length; ramblers still bounded
TEMPERATURE = 0.2
SEED = 7
STOP = ["</think>", "<think>"]   # backstop only now; enable_thinking=False is the real suppressor


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

    llm = Llama(model_path=MODEL_PATH, n_ctx=N_CTX, seed=args.seed, verbose=False)
    grammar = LlamaGrammar.from_string(GRAMMAR_PATH.read_text())
    # NEW: load the tokenizer so we own the chat template (and thinking) ourselves
    # instead of relying on llama.cpp's template handling, which mishandles Qwen3 thinking.
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)

    start = time.time()
    with out_path.open("a") as f:
        for n, i in enumerate(todo, 1):
            # NEW: render the prompt string with thinking turned off at the template level.
            # build_messages stays exactly as authored; we only change how it's rendered.
            prompt_str = tokenizer.apply_chat_template(
                build_messages(test[i]["diff"]),
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            # NEW: create_completion takes a raw prompt string (not chat messages),
            # so the grammar applies to a clean, think-free generation.
            out = llm.create_completion(
                prompt_str,
                grammar=grammar,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                seed=args.seed,
                stop=STOP,
            )
            message = out["choices"][0]["text"].strip()   # CHANGED: ["text"], not ["message"]["content"]
            if message.endswith("."):
                message = message[:-1]   # one trailing period, matching ADR 0017
            f.write(json.dumps({"id": i, "message": message}) + "\n")
            f.flush()

            if n % 20 == 0 or n == len(todo):
                rate = n / (time.time() - start)
                print(f"  {n}/{len(todo)}  ({rate:.2f} rows/s)")

    print(f"done: wrote candidates to {out_path}")


if __name__ == "__main__":
    main()