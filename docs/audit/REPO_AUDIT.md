# Committed — Repository Audit

**Generated:** 2026-06-26
**Branch:** main
**Commit:** ced1c8a5cb9eae93e38d8b0ba3fdc18c08dc390a
**Auditor:** Read-only sweep; no files changed except this one.

---

## 1. Contradictions

The most important section. One row per confirmed discrepancy between docs, or between a doc and the code.

| # | Claim | Source A says | Source B / Code says | Which is correct |
|---|-------|--------------|---------------------|-----------------|
| C1 | **Training stack: Unsloth** | ROADMAP.md (lines 157, 258): "Fire first QLoRA training run via Unsloth + TRL SFTTrainer"; STATUS.md "Next" (line 63): "Scaffold train.py (Unsloth + TRL SFTTrainer)"; SETUP_AGENT.md (lines 77, 81): unsloth listed as training dep; ADR 0006 (lines 13, 21): "unsloth, bitsandbytes" in training group | train.py docstring (line 4): "vanilla transformers + peft + trl (no Unsloth)"; pyproject.toml train group: accelerate, bitsandbytes, peft, trl, torch — no unsloth; README.md/MASTER.md: "vanilla transformers, no Unsloth" | **Code is correct.** Unsloth was planned; the final training implementation uses vanilla transformers + PEFT + TRL. ROADMAP, STATUS "Next", SETUP_AGENT.md, and ADR 0006 are stale on this point. |
| C2 | **v2 definition** | ROADMAP.md v2 section (lines 240–248): reasoning-trace distillation *only* ("augment the dataset with synthetic `<think>` traces…") | README.md/MASTER.md v2 section: leads with "Smaller-model comparison: can Qwen3-0.6B hit the same numbers?" followed by multi-line commits, specificity regression, reasoning-trace distillation, reasoning-display toggle | **README.md/MASTER.md is authoritative and more complete.** ROADMAP.md v2 describes only one of five v2 items and omits the Qwen3-0.6B comparison that is the stated driver of this re-run. |
| C3 | **STATUS.md "In Progress"/"Next" vs. actual repo state** | STATUS.md "In Progress": "Training config (configs/…yaml) — about to start." STATUS.md "Next": scaffold train.py (Unsloth + SFTTrainer), run training, re-run eval harness for before/after | Actual state: configs/qwen3-1.7b-lora-r16.yaml exists; train.py exists; training ran to completion; fine-tune eval ran (analysis/results/finetune_report.md); serving deployed; FastAPI Space live; CLI installable | **Code/repo is correct.** STATUS.md "In Progress" and "Next" sections were never updated after training + eval + serving + ship. STATUS.md "Done" also omits: training run, fine-tune eval, merger/quantization pipeline, serving deployment, CLI install, FastAPI Space. |
| C4 | **Dockerfile pre-warms wrong GGUF** | serving/Dockerfile (line 33): bakes `ggml-org/Qwen3-1.7B-GGUF / Qwen3-1.7B-Q4_K_M.gguf` (baseline) into image at build time | engine.py (lines 29–30): `DEFAULT_MODEL_REPO = "marzoukbaig14/committed-gguf"` and `DEFAULT_MODEL_FILE = "committed-finetuned-Q4_K_M.gguf"` per ADR 0048 | **ADR 0048 / engine.py is authoritative.** The Dockerfile pre-warm caches the baseline GGUF but the engine will attempt to download the fine-tuned GGUF at container startup. The baked cache is for the wrong artifact; the Space will perform a network pull on every cold start. |
| C5 | **serving/README.md default model** | "Defaults to the pinned baseline `ggml-org/Qwen3-1.7B-GGUF / Qwen3-1.7B-Q4_K_M.gguf` (ADR 0038)" | engine.py DEFAULT_MODEL_REPO/FILE point to the fine-tuned GGUF per ADR 0048 | **engine.py / ADR 0048 is correct.** serving/README.md still documents the pre-ADR-0048 state. |
| C6 | **ADR 0006 training-group deps include unsloth** | ADR 0006 (lines 13, 21): "unsloth, bitsandbytes" listed as the training group | pyproject.toml train group: accelerate, bitsandbytes, peft, trl, torch — no unsloth | **pyproject.toml is correct.** ADR 0006 was written before the decision to drop Unsloth; the dep group was implemented without it. |
| C7 | **Project structure: app file name** | README.md/MASTER.md structure tree: `app/ └── gradio_app.py` | Actual disk: `app/app.py` (plus `app/README_SPACE.md`, `app/requirements.txt`) | **Actual file is `app/app.py`.** README/MASTER structure diagram is wrong. |
| C8 | **Project structure: utils/ dir** | README.md/MASTER.md structure tree shows `src/committed/ └── utils/` | No `utils/` directory exists under `src/committed/` | **Directory does not exist.** README/MASTER structure diagram is wrong. |
| C9 | **STATUS.md Done: ADR count** | STATUS.md "Done": "Decision log: ADRs 0001–0043 logged" | docs/decisions/: 0001–0048 on disk; DECISION_LOG.md table goes to 0048 | **0048 is the current maximum.** STATUS.md was not updated when 0044–0048 were logged. |
| C10 | **ROADMAP.md phase map table: post-Data phases** | ROADMAP.md phase map (bottom): Train v1 "⬜ After baseline"; Final eval "⬜ After training"; Serve "⬜ After final eval"; Ship "⬜ End of v1"; v2 "⬜ After v1 ships" | v1 is shipped: training done, fine-tune eval done, serving live on HF Spaces, CLI installable | **v1 is complete.** Phase map table is entirely stale from the end of the Data phase onward. |
| C11 | **ROADMAP.md velocity table completeness** | ROADMAP.md velocity table ends at Session 7 (June 4) — data phase complete | Git log shows 14+ additional commits spanning eval design, baseline run, judge validation, training, serving, CLI, ADRs 0044–0048 | **Velocity table is stale.** At minimum 8 additional sessions worth of work is unrecorded. |

---

## 2. True ADR State

**Files on disk:** `docs/decisions/0001` through `docs/decisions/0048` plus `TEMPLATE.md`.
**True maximum ADR id:** 0048
**Next free ADR id:** 0049
**DECISION_LOG.md sync:** The generated table in DECISION_LOG.md runs from 0001 to 0048 — **in sync with the directory.** Every file that exists on disk has a matching entry in the table, and the table contains no entries for files that don't exist.

### Superseded ADRs

The following ADRs have `superseded` status in the DECISION_LOG.md table:

| ID | Title | Superseded by |
|----|-------|---------------|
| 0008 | Use claude-haiku-4-5 as the LLM-as-judge | 0011 |
| 0013 | Adopt STATUS.md, three-lane doc tracking, and GitHub-synced Project knowledge | 0014 |
| 0018 | Revise the dataset-size target from 30-50k to ~20-30k | (scope superseded by ADR 0023 + ADR 0026 build decisions) |
| 0025 | Set per-language cap (6k), floor (500), and stratification key for dataset build | 0026 |
| 0029 | Per-axis scoring scales mixed by judgment shape | 0035 |
| 0031 | Per-axis anchor definitions for all four judge axes | 0035 |
| 0033 | Switch the LLM-as-judge to a paid Claude model (Sonnet 4.6) | 0034 |

**Superseded ADRs referenced as current in key docs:** None of the seven superseded ADRs above are cited as currently active in MASTER.md, ROADMAP.md, STATUS.md, or README.md. ADRs 0025 and 0031 are referenced historically in STATUS.md with correct context ("ADRs 0025/0026" indicating the supersession chain). No false-positive references found.

**Note on ADR 0007 (Codespaces + devcontainer):** Listed as `accepted`. ADR 0041 says it "amends" (not supersedes) 0007. STATUS.md documents this correctly. Not a contradiction; the devcontainer is retained in-repo per the amended intent.

---

## 3. v1 Eval Numbers (v2 Comparison Targets)

Source: `analysis/results/baseline_report.md` and `analysis/results/finetune_report.md`.
Both runs: 442-example equal-allocation strata sample, judged by Gemini 2.5 Flash.
Deployment-reweighted = true test-split type distribution applied to per-type numbers (ADR 0037).
Sample-level numbers appear in the "Deterministic" and "LLM judge" subsections of each report.

### Deployment-reweighted headline (the v2 comparison targets)

| Metric | Baseline (zero-shot Qwen3-1.7B) | Fine-tune (v1) | Δ |
|--------|--------------------------------|----------------|---|
| Prefix-type accuracy (deployment-reweighted) | 0.131 | **0.637** | +0.506 |
| — always-`fix` floor | 0.489 | 0.489 | — |
| Conjunctive pass-rate (all 4 axes, deployment-reweighted) | 0.181 | **0.471** | +0.290 |
| Graded mean 0–3 (deployment-reweighted) | 1.207 | **2.188** | +0.981 |

### Per-axis pass rates (sample-level, equal-allocation strata)

| Axis | Baseline | Fine-tune | Δ |
|------|----------|-----------|---|
| type_correctness | 0.33 | 0.81 | +0.48 |
| faithfulness | 0.43 | 0.86 | +0.43 |
| completeness | 0.52 | 0.73 | +0.21 |
| specificity | **0.81** | 0.71 | **−0.10** (regression) |

### Sample-level composite (LLM judge, not reweighted)

| Metric | Baseline | Fine-tune | Δ |
|--------|----------|-----------|---|
| Conjunctive pass-rate (sample) | 0.156 | 0.430 | +0.274 |
| Graded mean 0–3 (sample) | 1.138 | 2.163 | +1.025 |

### Deterministic (sample-level, diagnostic)

| Metric | Baseline | Fine-tune | Δ |
|--------|----------|-----------|---|
| BLEU (sacrebleu; short-text caveat) | 2.17 | 11.79 | +9.62 |
| ROUGE-L F | 0.156 | 0.305 | +0.149 |
| Prefix-type accuracy (sample) | 0.113 | 0.452 | +0.339 |

### Judge-vs-human validation (n=50; baseline run only)

| Axis | Raw agreement | Cohen's κ |
|------|--------------|----------|
| type_correctness | 0.72 | 0.377 |
| faithfulness | 0.68 | 0.384 |
| completeness | 0.76 | 0.543 |
| specificity | 0.84 | 0.254 |

---

## 4. Model-Reference Inventory (v2 swap-list)

Every file + approximate line where `Qwen3-1.7B`, `Qwen/Qwen3-1.7B`, `1.7b`, or `1p7b` appears. These are the locations a v2 agent must update to swap in Qwen3-0.6B.

### Source / serving code (functional references — must be updated for v2 to run correctly)

| File | Line | Content |
|------|------|---------|
| `src/committed/inference/engine.py` | 31 | `DEFAULT_TOKENIZER = "Qwen/Qwen3-1.7B"` |
| `src/committed/inference/generate.py` | 33 | `DEFAULT_MODEL_PATH = "models/Qwen3-1.7B-Q4_K_M.gguf"` |
| `src/committed/data/filter.py` | 31 | `MODEL_NAME = "Qwen/Qwen3-1.7B"` (tokenizer for diff token-cap) |
| `src/committed/serving/Dockerfile` | 33 | `hf_hub_download('ggml-org/Qwen3-1.7B-GGUF', 'Qwen3-1.7B-Q4_K_M.gguf')` (baked baseline cache) |
| `src/committed/serving/Dockerfile` | 34 | `AutoTokenizer.from_pretrained('Qwen/Qwen3-1.7B')` |
| `configs/qwen3-1.7b-lora-r16.yaml` | 1 | filename (config file itself is named for the model) |
| `configs/qwen3-1.7b-lora-r16.yaml` | 5 | `name: Qwen/Qwen3-1.7B` |
| `configs/qwen3-1.7b-lora-r16.yaml` | 46 | `output_dir: outputs/qwen3-1.7b-lora-r16` |
| `configs/qwen3-1.7b-lora-r16.yaml` | 52 | `hub_model_id: marzoukbaig14/committed-qwen3-1.7b-lora` |
| `configs/qwen3-1.7b-lora-r16.yaml` | 54 | `run_name: qwen3-1.7b-lora-r16` |
| `scripts/merge_convert_quantize.py` | 26 | `BASE_MODEL = "Qwen/Qwen3-1.7B"` |
| `scripts/merge_adapter.py` | 28 | `BASE_MODEL = "Qwen/Qwen3-1.7B"` |
| `scripts/merge_adapter.py` | 29 | `ADAPTER = "marzoukbaig14/committed-qwen3-1.7b-lora"` |
| `scripts/train.slurm` | 32 | `--config configs/qwen3-1.7b-lora-r16.yaml` |
| `analysis/pool_stats.py` | 28 | `MODEL_NAME = "Qwen/Qwen3-1.7B"` |
| `analysis/pool_stats.py` | 94 | `"loading tokenizer (Qwen3-1.7B) for token counts..."` |
| `analysis/token_dist.py` | 24 | `MODEL = "Qwen/Qwen3-1.7B"` |

### Documentation (narrative references — update for accuracy)

| File | Line(s) | Note |
|------|---------|------|
| `README.md` | 5, 53, 73, 95, 97, 103, 208, 247 | v1 model identity; v2 context; these correctly describe v1 and need a v2 section added, not wholesale replacement |
| `MASTER.md` | 5, 53, 73, 88, 190, 229 | Same content as README.md (files are near-identical) |
| `ROADMAP.md` | 16, 164, 179, 257 | Describes v1 training outputs; lora repo name |
| `docs/STATUS.md` | 19, 22, 35, 65, 74 | Baseline run description; lora Hub id |
| `docs/DECISION_LOG.md` | 9, 44 | ADR titles; historical reference |
| `docs/decision-tree.md` | 9, 44 | Generated file; auto-updated by build_decision_log.py |
| `docs/eval/FINDINGS_v1.md` | 3, 23 | v1 eval writeup; correctly scoped to v1 |
| `docs/eval/FINDINGS_v1_i1.md` | 18 | Same scope |
| `docs/decisions/0003-base-model-qwen3-1p7b.md` | 3, 22 | ADR recording the v1 decision; historical |
| `docs/decisions/0019-adopt-hpc-cluster-primary-training.md` | 37 | Historical |
| `docs/decisions/0023-expand-scope-all-languages.md` | 33 | Historical |
| `docs/decisions/0038-pin-baseline-gguf-q4km.md` | 3, 24, 27 | ADR for baseline artifact; v1-specific |
| `docs/decisions/0044-adapter-merge-gguf-q4km-pipeline.md` | 28 | ADR for v1 merge pipeline |
| `src/committed/serving/README.md` | 20 | Documents pre-ADR-0048 defaults (also contradiction C5) |
| `handoffs/DECISIONLOG_AGENT.md` | 218, 222, 241 | Example ADR; historical |
| `handoffs/SERVING_AGENT.md` | 32 | Baseline GGUF description; historical |
| `src/committed/train/train.py` | 5, 18 | Docstring; historical reference to v1 config |

---

## 5. Code Inventory

### `src/committed/cli.py`
Console-script entry point. The `committed` command: reads a unified diff from stdin or a file, rejects non-diff input before loading the model (fast path), downloads the GGUF if not cached, and writes exactly one CC line to stdout (all progress to stderr so the command composes in pipes). Imports `CommitGenerator` from `engine.py` — no inference logic here.

### `src/committed/data/filter.py`
Dataset filter: converts raw CommitChronicle records into clean training rows. Applies CC regex + normalization (ADR 0017), subject-line ceiling/floor (ADR 0020), bot detection (ADR 0021), language by extension (ADR 0022), single-file constraint, merge/revert drop, diff token cap (2048, Qwen3-1.7B tokenizer). Produces `build_row()`.

### `src/committed/data/build.py`
Balances the filtered row pool and creates 90/5/5 train/val/test splits stratified by commit type (ADR 0026). Applies per-language cap 6,000 and floor 500 (ADR 0025). Produces JSONL splits.

### `src/committed/data/push.py`
Loads JSONL splits, auto-generates a dataset card with composition tables and provenance, pushes to the Hub (`marzoukbaig14/committed-train`).

### `src/committed/train/train.py`
QLoRA fine-tune. **Imports: `torch`, `yaml`, `datasets`, `transformers` (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig), `peft` (LoraConfig, get_peft_model, prepare_model_for_kbit_training), `trl` (SFTConfig, SFTTrainer). No Unsloth import.** Loads Qwen3-1.7B in 4-bit NF4, attaches a LoRA adapter, trains with SFTTrainer in prompt/completion format with completion-only loss, logs to W&B offline, pushes adapter to Hub. Includes monkeypatches for transformers 5.9 + torch 2.5.1 checkpoint loading quirks.

### `src/committed/inference/engine.py`
Shared inference core. Loads the GGUF via `llama_cpp.Llama`, the tokenizer via `transformers.AutoTokenizer`, and the GBNF grammar. Implements `CommitGenerator.generate()`: diff-guard → prompt render → constrained decode → trailing-period strip. Defines `NotADiffError`, `looks_like_diff()`, and `resolve_model_path()`. All entry points (CLI, FastAPI, Gradio, eval) call this class — one path, no drift. **Default model (ADR 0048):** `marzoukbaig14/committed-gguf / committed-finetuned-Q4_K_M.gguf`. `n_threads` / `n_threads_batch` are None by default (eval path) and set to 2 by the serving layer.

### `src/committed/inference/prompt.py`
Zero-shot prompt builder. Defines `SYSTEM_INSTRUCTION` (the frozen canonical rubric), `build_messages()` (system + diff + `/no_think` user turn), `build_prompt()` (applies the Qwen3 chat template with `enable_thinking=False`). One module shared across baseline, training, and fine-tuned inference so input shape cannot drift.

### `src/committed/inference/grammar.gbnf`
GBNF grammar for constrained decoding (ADR 0039). Encodes: `type(scope)?: description`. Type codebook: 10 types (feat, fix, refactor, docs, test, chore, perf, style, build, ci). Scope optional, parenthesized, `[a-zA-Z0-9_./-]+`. Description: one line, no leading/trailing whitespace, no trailing period.

### `src/committed/inference/generate.py`
Batch generation driver for eval: runs `CommitGenerator` over the test split, writes candidate JSONL with row ids for the eval harness to consume. Decoupled from the harness so any model can be dropped in.

### `src/committed/eval/metrics.py`
Deterministic eval metrics: BLEU (sacrebleu), ROUGE-L (rouge_score), prefix-type accuracy, always-fix floor, per-type breakdown.

### `src/committed/eval/judge_prompt.py`
Single source of the judge's four-axis rubric expressed as a prompt. Both Claude and Gemini backends import from here. Contains `JUDGE_SYSTEM` (fixed rubric) and `build_judge_prompt()`.

### `src/committed/eval/judge_gemini.py`
LLM-as-judge plumbing for Gemini 2.5 Flash. API throttle, 429 backoff, structured JSON parsing, per-record log. Default judge backend.

### `src/committed/eval/judge.py`
LLM-as-judge plumbing for Anthropic Claude. API calls, cost ceiling, structured JSON parsing, per-record log. Optional upgrade backend.

### `src/committed/eval/human_rate.py`
Human-rating worksheet builder and validator. Generates a blind-rating worksheet from candidates; ingests hand ratings; computes judge-vs-human agreement (Cohen's κ per axis).

### `src/committed/eval/run_eval.py`
Eval harness orchestrator. CLI flags: `--dataset`/`--refs` (references), `--candidates`, `--backend`, `--judge-log`, `--report`, `--human-ratings`, `--type-gate`, `--limit`, `--rpm`, `--ceiling`, `--split`. Ties together: reference loading, candidate alignment, deterministic metrics, LLM judge, gate-then-grade composite (ADR 0032), deployment reweighting (ADR 0037), optional human validation, JSON + Markdown report output.

### `src/committed/serving/api.py`
FastAPI serving layer. Two endpoints: `POST /generate` (diff → CC line; 400 on non-diff or empty) and `GET /health` (503 until model loaded, then `{"status": "ok", "model_loaded": true}`). CORS: exact origins from `COMMITTED_CORS_ORIGINS` env var plus `https://*.vercel.app` regex. `CommitGenerator` constructed at startup with `n_threads=2, n_threads_batch=2` (2-vCPU Space sizing).

### `src/committed/serving/Dockerfile`
Docker image for the FastAPI Space. Base: `python:3.11-slim` with build-essential for llama-cpp-python compilation. Installs via `uv sync --locked --no-dev`. **Pre-warm cache at build time bakes `ggml-org/Qwen3-1.7B-GGUF / Qwen3-1.7B-Q4_K_M.gguf` and `Qwen/Qwen3-1.7B` tokenizer.** Note: this is the baseline GGUF, not the fine-tuned default (contradiction C4). Exposes 7860; CMD is uvicorn.

---

## 6. Git + Structure

### Last 20 commits (git log -20 --oneline)

```
ced1c8a Add files via upload
31a588d Enhance README with evaluation and project details
551f60e Update README.md
b35866c Fix markdown links in README.md
ed10e53 Update README.md
493e449 Update CLAUDE.md
93bc756 Update MASTER.md
7fb0f89 feat: local CLI install path (git diff | committed) with GGUF auto-download
d1531e4 feat(cli): add `committed` console script for local git diff | committed
2e12265 feat(serving): report model_loaded in /health for a real warm/cold signal
c06824c fix(serving): set n_threads=2 on FastAPI Space to match Gradio (fix slow CPU inference)
be38b37 nothing
1bfb86c build: pin llama-cpp-python to 0.3.30
ec77c5c fix(serving): enforce diff guard in shared engine so all entry points reject non-diff input
25697cc feat(serving): default serving layer to fine-tuned GGUF (ADR 0048)
393fb61 docs(adr): 0048 pin fine-tuned GGUF as serving artifact of record
45d82ac docs(adr): bring 0044-0046 onto main from youthful-pasteur
c4c2f20 docs(adr): 0047 serve-minimal dependency groups
eaf2b52 build: add pyyaml to dev group (decision-log generator needs it)
```

### Directory tree (tracked files, excluding `__pycache__`, `.venv`, `.ruff_cache`, `.pytest_cache`)

```
.devcontainer/
    devcontainer.json
.github/
    workflows/
        ci.yml
analysis/
    build_strata.py
    collect_rows.py
    count_filtered.py
    explore_data.py
    human_ratings_50.jsonl
    inspect_messages.py
    line_analysis.py
    pool_stats.py
    profile_test_split.py
    spotcheck_filter.py
    token_dist.py
    results/
        baseline_judge_log.jsonl
        baseline_report.json
        baseline_report.md
        baseline_strata442.jsonl
        finetune_judge_log.jsonl
        finetune_report.json
        finetune_report.md
        finetune_strata442.jsonl
        human_ratings_50.jsonl
        language_distribution.png
        scan_full.txt
        spotcheck.txt
        token_dist.png
        token_dist.txt
app/
    app.py
    README_SPACE.md
    requirements.txt
configs/
    qwen3-1.7b-lora-r16.yaml
data/                           (gitignored; not inventoried)
docs/
    decision-tree.md
    DECISION_LOG.md
    STATUS.md
    decisions/
        0001-adopt-adr-logging.md
        … (0001–0048, 48 ADRs)
        TEMPLATE.md
    eval/
        examples_v1_i1.md
        FINDINGS_v1.md
        FINDINGS_v1_i1.md
        judge_rubric.md
    serving/
        HTTP_CONTRACT.md
handoffs/
    DECISIONLOG_AGENT.md
    SERVING_AGENT.md
    SETUP_AGENT.md
scripts/
    build_decision_log.py
    merge_adapter.py
    merge_convert_quantize.py
    train.slurm
src/committed/
    __init__.py
    cli.py
    data/
        __init__.py  (implied)
        build.py
        filter.py
        push.py
    eval/
        __init__.py
        human_rate.py
        judge.py
        judge_gemini.py
        judge_prompt.py
        metrics.py
        run_eval.py
    inference/
        __init__.py
        engine.py
        generate.py
        grammar.gbnf
        prompt.py
    serving/
        __init__.py
        api.py
        Dockerfile
        README.md
    train/
        __init__.py
        train.py
tests/
    smoke_test.py
    test_build.py
    test_filter.py
    test_serving.py
CLAUDE.md
LICENSE
MASTER.md
pyproject.toml
README.md
ROADMAP.md
START_HERE.md
uv.lock
.env.example
.gitignore
.python-version
```

**Notes:**
- `src/committed/utils/` does not exist (README.md/MASTER.md structure diagram says it does — contradiction C8).
- `app/app.py` is the Gradio demo (README.md/MASTER.md says `app/gradio_app.py` — contradiction C7).
- `data/` directory is present on disk but gitignored and not inventoried here.

---

## 7. Artifacts

`huggingface-cli` is not installed in the active shell environment on this machine. Hub artifacts were not verified against the live Hub. Names and expected contents recorded from docs and code.

| Hub artifact | Reference source | Expected content | Verified |
|---|---|---|---|
| `marzoukbaig14/committed-train` | README.md, push.py | train 52,173 / val 2,898 / test 2,898 rows, 16 languages | Not verified (no CLI) |
| `marzoukbaig14/committed-qwen3-1.7b-lora` | configs/qwen3-1.7b-lora-r16.yaml, merge_adapter.py | LoRA adapter, rank 16, from v1 training run | Not verified |
| `marzoukbaig14/committed-gguf` | engine.py DEFAULT_MODEL_REPO (ADR 0048) | `committed-finetuned-Q4_K_M.gguf` (~1.0 GB per cli.py hint) | Not verified |
| `ggml-org/Qwen3-1.7B-GGUF` (external) | ADR 0038, Dockerfile | `Qwen3-1.7B-Q4_K_M.gguf` — baseline artifact, baked into Docker image at build time | Not verified |
| `marzoukbaig14/committed-demo` (Space) | README.md | Gradio Space (CPU Basic); `app/app.py` | Not verified |
| FastAPI HF Docker Space | memory/committed-api-space-deploy.md | FastAPI Space; Factory rebuild required for backend changes (no GitHub auto-sync) | Not verified |

---

*End of audit. No files other than this one were created or modified.*
