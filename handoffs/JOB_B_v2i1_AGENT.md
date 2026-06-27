# Handoff: Job B — v2-i1, the Qwen3-0.6B Controlled Run

You are executing v2 iteration 1 of Committed: re-running the v1 fine-tune + eval pipeline with
**exactly one variable changed — the base model, Qwen3-1.7B → Qwen3-0.6B.** Read `CLAUDE.md` first;
it is your behavioral contract. Read **ADR 0049** (`docs/decisions/0049-v2-i1-qwen3-0p6b-controlled-comparison.md`)
before doing anything — it is your scope contract and it governs every choice below. Also read
`docs/audit/REPO_AUDIT.md` for the verified repo state and the model-reference inventory.

**The governing principle (ADR 0049, extends ADR 0045):** hold everything constant but the base
model. The recipe, the dataset, the grammar, the prompt, the eval harness, the 442-row strata
sample, and the Gemini judge are all frozen. The entire scientific value of this run is that the
before/after delta is attributable to *capacity alone*. If you change anything else, the result is
contaminated and worthless. When in doubt about whether something is in scope, it is not — ask.

## Why a fresh agent might get this wrong (read this)

You are reasoning about a repo you did not build and cannot see the history of. Two specific traps:
- `src/committed/serving/Dockerfile` **is intentionally absent** (deleted on purpose; the live demo
  is served by the standalone `marzoukbaig14/committed-api` Space, not the in-repo serving dir). Do
  not "restore" it or treat its absence as a bug.
- The training stack is **vanilla `transformers` + `peft` + `trl`, no Unsloth.** Any doc that says
  Unsloth is stale (and should already be fixed). Do not `uv add unsloth`.

## GATE 0 — verify the data-freeze before spending anything (do this first)

ADR 0049's data-freeze rests on the claim that Qwen3-0.6B and Qwen3-1.7B share an identical
tokenizer, so `committed-train` is reusable unchanged and is **not** rebuilt. **Verify this; do not
assume it.** In VS Code (`code check_tokenizer.py`), paste:
```python
from transformers import AutoTokenizer
a = AutoTokenizer.from_pretrained("Qwen/Qwen3-1.7B")
b = AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
s = "diff --git a/x.py b/x.py\n@@ -1 +1 @@\n-print(0)\n+print(1)\n"
print("vocab_equal:", a.get_vocab() == b.get_vocab())
print("ids_equal:  ", a(s)["input_ids"] == b(s)["input_ids"])
```
Run `uv run python check_tokenizer.py` (tokenizer-only; "PyTorch not found" is expected; needs Hub
network). Then delete the scratch file.

- **Both `True`** → data-freeze valid. Proceed. `committed-train` is reused unchanged; you do **not**
  touch `src/committed/data/` or rebuild the dataset.
- **Either `False`** → **STOP. Do not proceed, do not start any training.** The data-freeze is
  invalid; the dataset would need re-filtering with the 0.6B tokenizer, which changes the v2-i1
  design and means ADR 0049 needs amending. Report this to the human and halt.

## Branch

Branch from the merged, reconciled `main`. Run as separate commands (the human's local shell is
Windows PowerShell, which rejects `&&`):
```
git checkout main
git pull
git checkout -b v2-i1/qwen3-0p6b
```
Small commits. **Open a PR at the end; do not merge — the human merges.** Do not touch `main`
directly.

## The model-reference swap-list: CHANGE / FREEZE / DEFER

The audit inventory found ~10 locations referencing the 1.7B model. They are **not** all "change."
Treat them in three buckets:

### CHANGE — the actual experiment (these get the 0.6B id)
- **`configs/qwen3-1.7b-lora-r16.yaml`** → copy to a **new** file `configs/qwen3-0.6b-lora-r16.yaml`.
  Change only: the base model id (`Qwen/Qwen3-1.7B` → `Qwen/Qwen3-0.6B`), `hub_model_id`
  (→ a 0.6B adapter repo, e.g. `marzoukbaig14/committed-qwen3-0.6b-lora`), and `run_name`
  (→ something like `qwen3-0.6b-lora-r16`). **Leave every other value identical** — LoRA rank 16,
  alpha 32, lr 2e-4, sequence length, epochs, batch size, grad-accum. Do NOT edit the 1.7B config;
  leave it as the v1 record.
- **`scripts/train.slurm`** → point it at the new `qwen3-0.6b-lora-r16.yaml` (the `--config` / arg
  on ~line 32). If sensible, parameterize the config path rather than hardcoding, so the same script
  serves both runs.
- **`scripts/merge_adapter.py`** and **`scripts/merge_convert_quantize.py`** → the `BASE` model id
  (~lines 28–29 / 26) becomes `Qwen/Qwen3-0.6B`, and the adapter/output repos point at the 0.6B
  artifacts. These run *after* the cluster training, in the post-run leg.

### FREEZE — must NOT change (changing these contaminates the comparison)
- **`src/committed/data/filter.py`** (`MODEL` tokenizer ref, ~line 31), **`analysis/pool_stats.py`**,
  **`analysis/token_dist.py`** — these use the tokenizer for the diff token-cap. Because Gate 0
  confirmed the tokenizers are identical, the token counts are unchanged and **the dataset is reused
  byte-for-byte.** Do not rebuild data. Do not "update" these to 0.6B — it would produce an
  identical dataset and waste a full collection pass. Leave them.
- The **GBNF grammar** (`src/committed/inference/grammar.gbnf`), the **canonical prompt**
  (`prompt.py`, ADR 0040), the **eval harness** (`src/committed/eval/*`), the **442-row strata
  sample**, and the **Gemini judge** (ADR 0011) — all frozen. The 0.6B model is evaluated by the
  exact same harness, sample, prompt, grammar, and judge as the 1.7B model. Switching the judge or
  re-sampling the eval set breaks comparability with the v1 numbers.

### DEFER — only if 0.6B is chosen for deployment (NOT part of this run)
- **`src/committed/inference/engine.py`** (`DEFAULT_MODEL_REPO`/`FILE`, ~line 31) and
  **`src/committed/inference/generate.py`** (~line 33) point at the *fine-tuned 1.7B* serving
  artifact. **Do not change these in this run.** Whether to ship the 0.6B GGUF as the serving
  default is a *downstream decision* gated on the eval result, and it would be its own ADR + change.
  This run produces numbers, not a deployment swap.

## Execution sequence

### Phase 1 — config + scaffold (local, no GPU)
- Gate 0 passed.
- Create `configs/qwen3-0.6b-lora-r16.yaml` (CHANGE list above).
- Point `scripts/train.slurm` at it.
- Sanity-check the config parses and the only diffs vs the 1.7B config are the three intended fields
  (diff the two YAMLs and confirm). Commit.
- **Do NOT run training locally** (no GPU / the laptop is CPU-only). 

### Phase 2 — HAND TO HUMAN at the cluster boundary
This is the one manual step. Produce, in your hand-back message, the exact commands the human runs
on Northeastern Explorer, drawn from the v1 training process (see ROADMAP / STATUS / the train docs
for the real invocation):
- the `uv sync --group train` line (vanilla stack; A100 partition),
- the `sbatch scripts/train.slurm` line (request `--gres=gpu:a100:1`, bf16, `--time=08:00:00`),
- and a clear instruction: **before committing to the full run, watch the first ~100 steps** — check
  s/it and GPU memory. The 0.6B frees VRAM vs the 1.7B, so the held batch size may underfill the
  A100; this is a "confirm the recipe still fits," NOT a license to change the recipe. If it OOMs or
  the GPU is badly underused, report back rather than silently re-tuning.
The adapter auto-pushes to the Hub (the 0.6B adapter repo) every 100 steps + at end — the Hub is the
only persistent store across the ephemeral cluster job. **Stop here and wait for the human to run the
job and confirm the adapter is on the Hub.** Do not fabricate training output.

### Phase 3 — post-run: merge, quantize, eval (after the human confirms the adapter is on the Hub)
- **Before the eval step, surface one open dependency decision to the human:** `uv.lock` currently
  pins `llama-cpp-python==0.3.30` (exact), bumped from `>=0.3.23` during a recent lockfile refresh.
  The GGUF eval runs through `llama-cpp-python`, so confirm with the human whether to keep the exact
  pin or loosen it back to `>=` before running the eval. Do not change the pin on your own — flag it
  and wait for the human's call.
- Run `merge_adapter.py` / `merge_convert_quantize.py` (CHANGE list) to merge the 0.6B adapter into
  Qwen3-0.6B and produce the Q4_K_M GGUF, pushed to a 0.6B GGUF repo.
- Run the **frozen eval harness** on the 0.6B fine-tune over the same 442-row strata sample with the
  Gemini judge — the identical invocation v1 used. Also run the 0.6B *baseline* (un-fine-tuned
  Qwen3-0.6B) over the same set, so you have both the 0.6B before and after. (Budget: ~2 judge runs
  on the 442 set, ~$0.83 each.)
- Produce the before/after report comparing **0.6B baseline → 0.6B fine-tune**, and a second table
  comparing **0.6B fine-tune vs the recorded 1.7B fine-tune** across the full per-axis vector (type,
  faithfulness, completeness, specificity, conjunctive pass-rate, graded mean, BLEU, ROUGE-L). The
  1.7B numbers are in `analysis/results/` — read them, do not re-run 1.7B.
- **The headline question to answer explicitly in the report:** did the same fine-tune rescue
  feat-collapse at 0.6B (compare the 0.6B baseline's type distribution and the lift), and how close
  to the 1.7B fine-tune did 0.6B land. Write it honestly — if 0.6B is materially worse, that is a
  valid result per ADR 0049 (capacity / recipe-transfer limit), not a failure to hide.
- Save raw eval evidence in-repo per ADR 0046. Commit.

## Definition of done
- Gate 0 verified and reported.
- `configs/qwen3-0.6b-lora-r16.yaml` created (only the 3 intended fields differ from 1.7B); slurm
  pointed at it. Committed.
- Cluster commands handed to the human; training run by the human; 0.6B adapter confirmed on the Hub.
- 0.6B GGUF produced; 0.6B baseline + fine-tune evaluated on the frozen 442 set with the Gemini
  judge; before/after + vs-1.7B report written with the feat-collapse-rescue answer; raw evidence
  committed.
- PR opened against `main`; **not merged.**

## Explicit non-goals / hard stops
- Do not change the recipe (rank/alpha/lr/seq-len/epochs/batch beyond confirming fit). Do not rebuild
  the dataset. Do not edit the 1.7B config. Do not switch or re-tune the judge. Do not re-sample the
  eval set. Do not change `engine.py`/`generate.py` serving defaults. Do not restore the serving
  Dockerfile. Do not touch `CLAUDE.md`. Do not merge to `main`. Do not run training locally or
  fabricate cluster output.
- If 0.6B results suggest a recipe change would help, that is **v2-i2** — propose it as a new ADR,
  do not act on it in this run.

## If something breaks
Read the actual error. On the cluster, the known v1 landmine is the trl/transformers fp16 GradScaler
crash on non-A100 GPUs — this is why A100 + bf16 is required; if the human reports a non-A100 node,
flag it rather than working around it. If the eval harness or judge throttling errors, surface the
real traceback and the cost incurred so far; do not silently retry into the budget.
