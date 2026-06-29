# Handoff: Job B — Phase 3 (0.6B merge → GGUF → eval → report)

You are running Phase 3 of v2-i1: turn the trained Qwen3-0.6B LoRA adapter into a servable GGUF and
evaluate it against the frozen v1 harness, producing the 0.6B-vs-1.7B comparison. Read `CLAUDE.md`,
**ADR 0049** (the v2-i1 scope contract), and the Phase 3 section of
`handoffs/JOB_B_v2i1_AGENT.md` before starting. This runs in the **Claude Code cloud sandbox**
(CPU-only, ~16GB RAM, ~30GB disk) — not the cluster, not the user's local machine.

**Governing principle (unchanged from Job B):** the eval harness, the 442-row strata sample, the
GBNF grammar, the canonical prompt, and the Gemini judge are all FROZEN — identical to how the 1.7B
model was evaluated. The only thing different from v1's eval is the model under test. If you change
any harness/judge/sample/prompt setting, the 0.6B-vs-1.7B comparison is contaminated.

## Environment notes for the sandbox
- **CPU-only, no GPU.** The merge loads a 0.6B model on CPU (fits in 16GB). GGUF eval runs on CPU
  via llama.cpp — slower than GPU but fine for 442 examples, and it mirrors the real serving path.
- **`llama-cpp-python` must build from source here** (the sandbox has GCC/Clang/cmake). **Keep the
  pin at `==0.3.30`** — do NOT change it. The user decided to hold the pin so the eval environment
  introduces no new variable. Install the eval/serving deps as the project defines them; if a build
  step is needed, build it — do not "fix" it by loosening the pin.
- **Network:** the sandbox reaches the Hub (for the adapter + base) and Gemini (for the judge). If
  huggingface.co or the Gemini endpoint is unreachable, stop and report — do not work around it.
- **Secrets:** the Gemini judge needs its API key, and Hub access needs `HF_TOKEN`, as the env
  defines them. Never print or commit a key.

## GATE — verify the adapter before spending anything (do this first)
Phase 3 is worthless if it merges a truncated or half-trained adapter. Before any merge/eval:
- Confirm the training run **finished cleanly** — check the run reached its full step count
  (~6522 steps, 2 epochs) and saved/pushed a final adapter, not a walltime-killed partial. The
  user can confirm from the cluster log tail; if you can see the run's W&B/Hub metadata, verify the
  final step and a non-truncated final loss.
- Confirm `marzoukbaig14/committed-qwen3-0.6b-lora` on the Hub has a complete final
  `adapter_model.safetensors` (and adapter_config.json). If the adapter looks partial or the run
  was cut off, **STOP and report** — do not merge a bad adapter.

## Branch
Continue on `v2-i1/qwen3-0p6b` (branch from `origin/main` if the sandbox is a fresh clone, then
check out the branch — it already has the 0.6B config and the Phase-1 scaffold). Small commits.
**Open a PR at the end; do not merge — the user merges.**

## Step 1 — merge → GGUF → quantize (the existing v1 pipeline, repointed to 0.6B)
Use the existing scripts (`scripts/merge_adapter.py`, `scripts/merge_convert_quantize.py`) — the
same merge→GGUF→Q4_K_M pipeline v1 used (ADR 0044). They were updated in Phase 1's CHANGE list to
reference the 0.6B base; confirm the `BASE` is `Qwen/Qwen3-0.6B` and the adapter/output repos are the
0.6B ones before running.
- Merge the 0.6B adapter into `Qwen/Qwen3-0.6B` → a standalone merged model.
- Convert to GGUF, quantize to **Q4_K_M** (the serving quant of record).
- Push the 0.6B GGUF to its Hub repo (e.g. `marzoukbaig14/committed-gguf-0.6b` or the 0.6B GGUF
  repo the scripts target — match whatever Phase 1 set; do not invent a new naming scheme without
  flagging it).
- Sanity-check: load the GGUF and generate one message from a trivial diff to confirm it produces
  valid Conventional Commits output (the GBNF grammar should guarantee well-formedness). If the
  output is malformed or generation errors, STOP and report before spending judge budget.

## Step 2 — eval, with the judge (BUDGET-GUARDED)
Run the **frozen eval harness** — the identical invocation v1 used (`src/committed/eval/run_eval.py`
or however v1 was driven), over the same 442-row strata sample, with the Gemini 2.5 Flash judge.
- Evaluate **two** models so you have both 0.6B before and after:
  1. the **0.6B fine-tune** (the GGUF you just made), and
  2. the **0.6B baseline** (un-fine-tuned Qwen3-0.6B, same GGUF quant/pipeline, no adapter) —
     so the fine-tune's lift is measured against its own base, apples-to-apples with how v1
     measured the 1.7B lift.
- **Budget guard:** each judged run is ~$0.83 (~$1.66 total). Before launching the judge, state the
  expected cost. If the judge throttles or 429s, use the harness's existing backoff — do NOT
  silently retry in a loop that burns budget. If anything errors mid-run, STOP, report the real
  error and the cost incurred so far, and wait for the user. Do not exceed roughly the ~$1.66
  expected without checking in.
- Run the deterministic metrics (BLEU, ROUGE-L, prefix-type accuracy) too — those are free.

## Step 3 — the report (the point of all this)
Write the comparison, honestly. Two tables:
- **0.6B baseline → 0.6B fine-tune** across the full per-axis vector: type accuracy
  (deployment-reweighted), conjunctive pass-rate, graded mean, faithfulness, completeness,
  specificity, plus BLEU and ROUGE-L.
- **0.6B fine-tune vs the recorded 1.7B fine-tune** across the same vector. The 1.7B numbers are in
  `analysis/results/` / `docs/eval/FINDINGS_v1.md` — **read them, do not re-run 1.7B.**
- **Answer the headline question explicitly:** did the same fine-tune rescue feat-collapse at 0.6B?
  Compare the 0.6B baseline's type distribution (was it also ~95% `feat`, or worse, given lower
  capacity?) against the fine-tuned lift. And: how close to the 1.7B fine-tune did 0.6B land?
- **Write it straight.** If 0.6B is materially worse than 1.7B, that is a valid result per ADR 0049
  (a capacity / recipe-transfer finding), not something to bury. If 0.6B lands close, say that
  plainly too — it's the stronger "you don't need 1.7B for this" result and it bears on whether
  0.6B should become the shipped serving artifact (a *future* decision, its own ADR — do not act on
  it here).
- Save raw eval evidence in-repo per ADR 0046 (the judged JSONL + the report json/md), the same way
  v1's evidence is tracked.

## Definition of done
- Adapter gate passed (clean finish, complete adapter on Hub).
- 0.6B GGUF (Q4_K_M) produced and pushed; sanity generation valid.
- 0.6B baseline + 0.6B fine-tune evaluated on the frozen 442 set with the Gemini judge; cost stated
  and within ~$1.66 (or checked in if more).
- Report written with both tables + the feat-collapse-rescue answer + the 0.6B-vs-1.7B verdict; raw
  evidence committed.
- PR opened against `main`; **not merged.**

## Explicit non-goals / hard stops
- Do NOT change the eval harness, the 442 sample, the grammar, the prompt, or the judge — they're
  frozen for comparability. Do NOT loosen the `llama-cpp-python==0.3.30` pin. Do NOT re-run the 1.7B
  eval (read its recorded numbers). Do NOT change `engine.py`/`generate.py` serving defaults or swap
  the deployed model to 0.6B (that's a future, separate ADR). Do NOT merge to `main`. Do NOT exceed
  the judge budget without checking in. Do NOT fabricate eval numbers — every number traces to a
  judged/deterministic run with committed evidence.
- If the 0.6B results suggest a recipe change would help, that's **v2-i2** — note it, do not act.

## If something breaks
Read the actual error. If the GGUF generation is malformed, the merge or grammar wiring is wrong —
report before judging. If the judge errors or throttles, surface the real traceback and the spend so
far; don't loop. If `llama-cpp-python` fails to build, report the build error — do not loosen the
pin to dodge it. If the adapter gate fails (partial/truncated run), stop; the fix is a rerun, not a
salvage.
