# Committed

A fine-tuned 1.7B language model that writes Conventional Commits messages from code diffs. Runs locally via llama.cpp. Your code never leaves your machine.

**Status:** In active development. v1 in progress.

---

## What this is

Committed is a QLoRA fine-tune of Qwen3-1.7B trained on a filtered subset of CommitChronicle, a dataset of roughly 10.7 million real GitHub commits. The filtered training set targets 30-50k high-quality Python commits that follow the Conventional Commits specification exactly.

At inference time, the fine-tuned adapter is merged into the base model, converted to GGUF, and served via llama.cpp with grammar-constrained decoding. A GBNF grammar encodes the Conventional Commits format so every generation is valid by construction, no post-processing needed.

The project demonstrates a complete, production-grade applied-ML pipeline on free infrastructure: data curation, parameter-efficient fine-tuning, rigorous multi-metric evaluation validated against human ratings, and a real serving and deployment layer.

## What this is not

- A novel research contribution. Commit message generation has been studied since 2017.
- An attempt to beat frontier models on quality. A small local model will not out-write Claude or GPT-4. That is not the point.
- A general-purpose chatbot. Single task, structured output.

## Why local

Most commit-message tools (aicommits, opencommit, GitHub Copilot suggestions) send your diff to a third-party API. That means proprietary code, unreleased features, and internal architecture details leave your machine on every commit. Committed runs entirely locally, costs nothing per call, works offline, and scales to any volume without API bills.

---

## Tech stack

**Base model:** Qwen/Qwen3-1.7B (Apache 2.0, strong code priors, native thinking modes used in v2)

**Fine-tuning:**
- Unsloth (roughly 2x faster QLoRA, drop-in with SFTTrainer)
- TRL SFTTrainer
- PEFT LoRA
- bitsandbytes 4-bit quantization (training only, not serving)
- transformers, accelerate

**Data:**
- CommitChronicle via Hugging Face datasets library
- pandas for filtering

**Serving:**
- llama.cpp via llama-cpp-python (CPU inference, replaces bitsandbytes which is CUDA-only)
- GGUF quantization (Q4_K_M primary, Q8 and fp16 for benchmarking)
- GBNF grammar-constrained decoding
- FastAPI inference endpoint
- Docker

**Demo:** Gradio 5.x on Hugging Face Spaces (CPU Basic, free tier)

**Evaluation:**
- sacrebleu (BLEU)
- rouge-score (ROUGE-L)
- scikit-learn (prefix-classification accuracy, confusion matrix)
- Claude Sonnet 4.6 as LLM-as-judge (free-tier Gemini 2.5 Flash retained as reproducible fallback)
- 50 hand-rated examples for judge validation

**Tracking and registry:**
- Weights and Biases (run metrics, hyperparameters, sample generations)
- Hugging Face Hub as model registry (dataset, adapter, GGUF, eval reports, model and dataset cards)

**Dev environment:**
- GitHub Codespaces with a committed devcontainer
- uv for package management (uv sync to install, uv run to execute)
- ruff for linting, pytest for tests
- GitHub Actions: ruff + pytest + eval regression gate
- Training: Colab T4 primary, Kaggle backup, Northeastern cluster for larger runs

**Dependency split:** The GPU training stack (unsloth, bitsandbytes) lives in a separate uv dependency group and is never installed in the CPU Codespace. This is intentional and important.

---

## Project structure

```
committed/
├── README.md
├── CLAUDE.md                       # frozen agent behavioral contract
├── MASTER.md                       # single source of truth for the design
├── ROADMAP.md                      # 7-day plan and phase map
├── pyproject.toml                  # uv-managed deps, cpu/dev and train groups
├── uv.lock
├── .devcontainer/
│   └── devcontainer.json
├── .github/
│   └── workflows/
│       ├── ci.yml                  # ruff + pytest + eval regression gate
│       └── update-readme.yml       # auto-updates README progress section
├── docs/
│   ├── decisions/                  # ADR records, one file per decision
│   ├── progress.yml                # phase and artifact status tracker
│   ├── DECISION_LOG.md             # generated, do not edit by hand
│   └── decision-tree.md            # generated, do not edit by hand
├── scripts/
│   ├── build_decision_log.py       # regenerates the decision log and tree
│   └── update_readme_progress.py   # updates README progress section
├── src/committed/
│   ├── data/
│   │   ├── load.py
│   │   ├── filter.py
│   │   └── push.py
│   ├── train/
│   │   ├── config.py
│   │   └── train.py
│   ├── eval/
│   │   ├── metrics.py
│   │   ├── judge.py
│   │   ├── human_rate.py
│   │   └── run_eval.py
│   ├── inference/
│   │   ├── generate.py
│   │   ├── prompt.py
│   │   └── grammar.gbnf
│   ├── serving/
│   │   ├── api.py
│   │   └── Dockerfile
│   └── utils/
│       └── hub.py
├── app/
│   └── gradio_app.py
├── configs/
├── notebooks/
└── tests/
```

---

## Current status

Design and architecture are fully locked. The decision-log system is being stood up now (Day 1). Environment setup follows immediately after.

**Completed:**
- Project thesis, scope, and positioning finalized
- Full tech stack decided and documented
- v1, v2, v3 scopes defined with a descope ladder
- 11 architecture decision records written and logged
- All governance documents written (MASTER.md, CLAUDE.md, ROADMAP.md, handoffs)

**In progress:**
- Repository scaffolding
- Decision-log system (ADR records, generator script, GitHub Actions)

**Up next:**
- Dev environment (devcontainer, uv, dependency groups, secrets, smoke tests)
- Data curation

---

## Roadmap

### v1 (current, target 3-4 weeks)

Core (never cut):
- [ ] Filtered dataset published to Hugging Face Hub
- [ ] QLoRA fine-tune of Qwen3-1.7B, adapter on Hub, W&B tracked
- [ ] Multi-metric eval: BLEU, ROUGE-L, prefix-classification accuracy, LLM-as-judge validated against 50 human ratings
- [ ] Grammar-constrained GGUF inference (llama.cpp + GBNF)
- [ ] Gradio demo deployed to HF Spaces
- [ ] README with honest results, sample outputs, failure-mode analysis

Production layer (strongly recommended):
- [ ] FastAPI serving endpoint + Dockerfile
- [ ] Quantization quality-vs-latency benchmarks (Q4 / Q8 / fp16)
- [ ] Eval-in-CI regression gate
- [ ] Hugging Face Hub model and dataset cards

Stretch (cut first under time pressure):
- [ ] Base-model comparison: Qwen3-1.7B vs Qwen3-0.6B vs Qwen2.5-Coder-1.5B on the same harness
- [ ] LoRA rank ablation (8 / 16 / 32)

### v2 (planned, pending compute/API budget)

The reasoning-distillation experiment. Uses a free-tier LLM (provider chosen when v2 begins) to generate chain-of-thought reasoning traces for each diff, trains a v2 model on those traces, and runs a with-vs-without-reasoning ablation as the headline analytical contribution. Qwen3's native thinking modes add a bonus comparison axis.

- [ ] Synthetic reasoning-trace generation via a free-tier LLM
- [ ] Fine-tune v2 on augmented diff-reasoning-message schema
- [ ] With-vs-without-reasoning ablation
- [ ] Qwen3 native thinking comparison
- [ ] Reasoning-display toggle in demo

### v3+ (directional)

- [ ] Repo-specific style adaptation via RAG (retrieve similar past commits from user's own repo)
- [ ] Multi-format output: Conventional Commits, Gitmoji, free-form
- [ ] VS Code extension (reads staged diff, fills commit message box directly)
- [ ] Larger base models (3-7B) when compute permits

---

## Evaluation methodology

Five metrics, chosen to cover different failure modes:

| Metric | What it measures | Reliability |
|--------|-----------------|-------------|
| BLEU (sacrebleu) | N-gram overlap with reference | Low for short text; reported for completeness |
| ROUGE-L | Longest-common-subsequence overlap | Complementary to BLEU; also limited alone |
| Prefix-classification accuracy | Did the model emit the correct type (feat, fix, refactor, etc.)? | High; deterministic and meaningful |
| LLM-as-judge (Claude Sonnet 4.6, 500-1000 examples; free Gemini fallback) | Four orthogonal axes: type-correctness, faithfulness, completeness, specificity | Headline metric |
| Human ratings (50 examples) | Same axes, rated by a human | Used to validate the judge; judge-vs-human correlation is reported |

The judge-vs-human correlation is the key number. It gives the judge score an honest confidence bound rather than reporting it as ground truth. The judge applies an analytic per-axis rubric: faithfulness is a hard gate (an unfaithful message fails regardless of other axes), and the headline is the conjunctive pass-rate — the fraction of outputs that clear all four axes. A paid Claude judge is used for validation; the eval is reproducible on the free-tier Gemini fallback, and everything shipped (model, dataset, serving, demo) stays free.

---

## Results

Not yet available. Will be updated when eval runs complete.

---

## Decision log

Every significant design and development decision is logged as an Architecture Decision Record in `docs/decisions/`. The full log with a relationship diagram is in `docs/DECISION_LOG.md` and `docs/decision-tree.md`. Both are auto-generated by `scripts/build_decision_log.py`.

Start with `docs/decisions/0001-adopt-adr-logging.md` for the first record and read forward.

---

## License

- Code: MIT
- Model adapter: Apache 2.0 (inherited from Qwen3-1.7B)
- Dataset: CommitChronicle license (verify terms before commercial use)

---

Built by Muhammad Marzouk Baig — MS Artificial Intelligence, Northeastern University