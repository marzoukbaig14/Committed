# Committed — Status

_Living status. Update in the same commit as the work._
_Plan lives in ROADMAP.md; design in MASTER.md + docs/decisions/._

**Phase:** Eval complete — baseline measured, judge validated against 50 genuine human ratings.
Infra migrated off Codespaces to local + CI. Training config is the next core task; first QLoRA
run pending.
**Calendar:** ~June 12, 2026 (eval + infra work landed in the June 11 session)

## Done
- Setup: devcontainer + uv lockfile; CPU deps; 3 secrets injected; 15 smoke tests pass.
- Data inspection: CommitChronicle loaded/inspected; token distribution measured; exploration
  scripts in analysis/.
- Dataset published to Hub: `marzoukbaig14/committed-train` — train 52,173 / val 2,898 / test 2,898,
  16 languages; auto-generated dataset card (composition, provenance, limitations).
- Filter + build pipeline: CC regex + normalization (ADR 0017), subject-line ceiling (0020), bot
  detection by message pattern (0021), language by file extension (0022), single-file only, drop
  merge/revert, token cap 2048 (Qwen3-1.7B tokens). 49/49 tests pass. Build: raw pool 189,330 →
  57,969 balanced (cap 6,000 / floor 500, 16 languages) → 90/5/5 splits stratified by commit type.
- Decision log: ADRs **0001–0043** logged (see DECISION_LOG.md). Eval-design set 0027–0036;
  0037 = deployment-reweighted headline metrics; 0038 = baseline GGUF pin (ggml-org/Qwen3-1.7B-GGUF
  Q4_K_M, matches serving quant so before/after isolates fine-tuning); 0039 = concrete CC GBNF
  grammar (ten-type codebook, optional scope, no !, single-line; format not semantics); 0040 =
  single canonical zero-shot prompt across baseline/training/inference (near-raw `Diff:\n{diff}`,
  `enable_thinking=False`); 0041 = dev surface Codespaces→local-native, reproducibility relocated
  to CI (amends 0007); 0042 = ruff scoped to package+tests, CI lint/test gate; 0043 =
  portfolio-integrated demo — `/committed` route in Next.js portfolio calls FastAPI on HF Docker
  Space; Gradio Space retained as standalone; neither publicized until fine-tune ready.
- **Eval harness implemented + run.** `docs/eval/judge_rubric.md` synced to ADR 0035;
  `judge_prompt.py`, `metrics.py` (BLEU, ROUGE-L, prefix-type accuracy), `judge_gemini.py`
  (Gemini 2.5 Flash + free-tier throttle + 429 backoff), `run_eval.py` (deterministic + composite
  gate-then-grade + deployment reweighting + judge-vs-human validation). `human_rate.py`
  (build/check/ingest for the blind human-rating worksheet).
- **Baseline measured (zero-shot Qwen3-1.7B).** 442-row equal-allocation strata sample, judged
  (`analysis/results/baseline_strata442.jsonl` + `baseline_judge_log.jsonl`, ~$0.83). Report
  committed (`analysis/results/baseline_report.json/.md`).
  - Headline (deployment-reweighted to true ~49% fix split): prefix-type accuracy **0.131** vs
    always-`fix` floor **0.489** — ~3.7× worse than trivial. Conjunctive pass-rate 0.181; graded
    mean 1.207.
  - **Feat-collapse confirmed:** ~95% of diffs predicted `feat`.
  - Judge per-axis (sample): type 0.33, faithfulness 0.43, completeness 0.52, specificity 0.81.
  - Deterministic (diagnostic only): BLEU 2.17, ROUGE-L F 0.156 (short-text caveats).
- **Judge validated against 50 genuine human ratings** (`analysis/human_ratings_50.jsonl`,
  hand-rated blind by Zook; an earlier Fable-5-generated set was discarded as invalid — LLM-vs-LLM
  is not human validation):
  - type raw 0.72 / κ 0.377 · faithfulness raw 0.68 / κ 0.384 · completeness raw 0.76 / κ 0.543 ·
    specificity raw 0.84 / κ 0.254.
  - Read: fair–moderate proxy; strongest on completeness; judge is stricter than the human on the
    faithfulness gate; specificity κ is prevalence-deflated (report raw agreement); n=50 → wide CIs.
- **Infra migrated off Codespaces** (NU Enterprise org Codespaces budget block). Now local Windows
  + VS Code + uv `.venv` (no GPU / no C++ compiler locally; `llama-cpp-python` skipped via
  `uv sync --no-install-package llama-cpp-python` — it's a serving dep, builds fine on Linux/CI).
  Devcontainer retained in repo. CI added (`.github/workflows/ci.yml`): `uv sync --locked` + ruff
  (scoped to package; `analysis/` excluded) + offline unit tests — green. `build.py` lambda→def.

## In progress
- Training config (`configs/…yaml`) — about to start. Core work (Zook authors values): LoRA rank +
  alpha, learning rate, sequence length (from the token distribution), batch size + grad-accum,
  epochs.

## Next
- Scaffold `src/committed/train/train.py` (Unsloth + TRL `SFTTrainer`) + a SLURM submit script.
- On Explorer HPC: `uv sync --group train`, confirm GPU visible + minimal import check, fire the
  first QLoRA run, push adapter checkpoints to the Hub (`marzoukbaig14/committed-qwen3-1.7b-lora`),
  W&B run attached.
- Re-run the eval harness on the fine-tuned candidates → before/after comparison (the thesis).
- Decide: move serving deps (`llama-cpp-python`, likely gradio/fastapi) into an optional `serve`
  group so dev/eval/training never compile llama.cpp (proposal only → then ADR + `pyproject` edit).

## Key data findings (feed the filter + training)
- Final training set: 52,173 rows. Commit types heavily skewed to `fix` (48.9%); a trivial
  always-predict-`fix` baseline scores ~49% prefix-accuracy — read all results against that floor.
- Token cap 2048 (Qwen3-1.7B tokens). Python single-file diffs: med 165, p90 601, p95 906,
  p99 2834. Over-cap diffs dropped, not truncated. Messages tiny (p99 38 chars). Use this for the
  training sequence length, but confirm against the all-language committed dataset.
- Language mix (after cap/floor): 6 hit the 6,000 cap (JavaScript, TypeScript, Java, Python, Go,
  Rust); then Shell 4,215 · C++ 3,753 · PHP 2,708 · C 2,407 · C# 2,146 · Swift 2,129 · Kotlin 1,812
  · Dart 1,370 · Ruby 750 · Elixir 679.
- ADR 0012: `repo` + `license` columns kept per row; CommitChronicle paper cited (arXiv 2308.07655);
  sensitive-data caveat carried forward.

## Quirks
- Dev is now **local on Windows** (uv `.venv`); training is on HPC; the laptop is CPU-only.
  `llama-cpp-python` needs a C++ compiler Windows lacks → skipped locally; builds fine on Linux/CI.
- Codespaces may return in ~3 days via the GitHub Student Pack (personal-account hours); the block
  was the NU Enterprise org budget. CI is green and independent of where dev happens.
- W&B web UI blocked on school wifi (DNS/filter); API calls (training) are fine; view via hotspot.
- Streaming + interpreter shutdown can throw a cosmetic exit crash; guard exploration scripts with
  `os._exit(0)`.
- "PyTorch not found" from transformers is expected in a CPU/tokenizer-only env.
- Org disables connectors (no Project GitHub sync) and blocks the W&B UI; continuity is by pasting
  STATUS, not syncing (ADR 0014).
