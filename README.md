# Committed

A fine-tuned 1.7B language model that writes Conventional Commits messages from code diffs. Runs locally via llama.cpp. Your code never leaves your machine.

**[Live Demo](https://my-portfolio-ten-rosy-36.vercel.app/committed)** · **[Gradio Space](https://huggingface.co/spaces/marzoukbaig14/committed-demo)** · **[Model (GGUF)](https://huggingface.co/marzoukbaig14/committed-gguf)** · **[LoRA Adapter](https://huggingface.co/marzoukbaig14/committed-qwen3-1.7b-lora)** · **[Dataset](https://huggingface.co/datasets/marzoukbaig14/committed-train)**

---

## Quickstart

Generate a commit message from a real diff, locally, CPU-only. Requires Python 3.11+. No GPU, no API key, nothing leaves your machine.

### CLI (recommended)

Install the package and the prebuilt CPU build of `llama-cpp-python` (the extra index serves a ready-made wheel, so there's no C++ compile step):

```
pip install "committed @ git+https://github.com/marzoukbaig14/Committed.git" --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

Then pipe a diff straight in:

```
git diff | committed
```

Example:

```
$ git diff | committed
fix: increase default timeout to 60s
```

You can also pass a diff file instead of using stdin:

```
committed path/to/change.diff
```

Notes:
- **First run downloads the model** (~1 GB, the fine-tuned GGUF) from the Hugging Face Hub and caches it; later runs reuse the cache and start in seconds. The download is a public artifact — no token needed.
- The model loads fresh each run (~18 s cold the first time, a few seconds once cached). Progress goes to stderr; only the commit message is written to stdout, so `git diff | committed` composes cleanly in scripts and pipes.
- Bring your own GGUF with `--model-path path/to/model.gguf`; cap length with `--max-tokens N`. See `committed --help`.

### Docker

A CPU-only Docker image (`docker run --rm -i … < some.diff`) is planned as a zero-setup alternative and will be documented here once published.

---

## What this is

Committed is a QLoRA fine-tune of Qwen3-1.7B trained on a filtered subset of CommitChronicle, a dataset of roughly 10.7 million real GitHub commits. The filtered training set is ~58k single-file commits across 16 languages that follow the Conventional Commits specification, balanced by commit type.

At inference time, the fine-tuned adapter is merged into the base model, converted to GGUF, and served via llama.cpp with grammar-constrained decoding. A GBNF grammar encodes the Conventional Commits format so every generation is valid by construction, no post-processing needed.

The project demonstrates a complete applied-ML pipeline on free infrastructure: data curation, parameter-efficient fine-tuning, rigorous multi-metric evaluation validated against human ratings, and a real serving and deployment layer.

## What this is not

- A novel research contribution. Commit message generation has been studied since 2017.
- An attempt to beat frontier models on quality. A small local model will not out-write Claude or GPT-4. That is not the point.
- A general-purpose chatbot. Single task, structured output.

## Why local

Most commit-message tools (aicommits, opencommit, GitHub Copilot suggestions) send your diff to a third-party API. That means proprietary code, unreleased features, and internal architecture details leave your machine on every commit. Committed runs entirely locally, costs nothing per call, works offline, and scales to any volume without API bills.

---

## Results

The fine-tune was evaluated against the un-tuned Qwen3-1.7B base on a 442-example test sample, scored by an LLM judge on four orthogonal axes (the judge itself validated against 50 hand-rated examples). Headline numbers are reweighted to the true commit-type distribution of the test split.

| Metric | Base | Fine-tuned |
|--------|------|-----------|
| Type accuracy (deployment-reweighted) | 0.131 | **0.637** |
| Conjunctive pass-rate (all four axes) | 0.181 | **0.471** |
| Graded mean (0–3) | 1.207 | **2.188** |
| Faithfulness | 0.43 | **0.86** |

The base model's dominant failure was "feat-collapse" — it labeled ~95% of all diffs `feat` regardless of content, scoring below a trivial always-guess-`fix` baseline (0.489) on type. Fine-tuning broke the collapse. One axis (specificity) regressed, 0.81 → 0.71; the full breakdown, the regression analysis, and sample outputs are on the **[project page](PORTFOLIO_COMMITTED_URL)**.

---

## Tech stack

**Base model:** Qwen/Qwen3-1.7B (Apache 2.0, strong code priors, native thinking modes used in v2)

**Fine-tuning:**
- QLoRA via PEFT LoRA + TRL SFTTrainer (vanilla `transformers`, no Unsloth)
- bitsandbytes 4-bit quantization (training only, not serving)
- transformers, accelerate

**Data:**
- CommitChronicle via Hugging Face datasets library
- pandas for filtering

**Serving:**
- llama.cpp via llama-cpp-python (CPU inference, replaces bitsandbytes which is CUDA-only)
- GGUF quantization (Q4_K_M serving artifact)
- GBNF grammar-constrained decoding
- FastAPI inference endpoint
- Docker

**Demo:** Gradio on Hugging Face Spaces (CPU Basic, free tier) + a portfolio-integrated web demo calling the FastAPI Space

**Evaluation:**
- sacrebleu (BLEU), rouge-score (ROUGE-L)
- scikit-learn (prefix-classification accuracy, confusion matrix)
- Gemini 2.5 Flash (free tier) as LLM-as-judge; Claude Sonnet 4.6 available as optional upgrade backend
- 50 hand-rated examples for judge validation

**Tracking and registry:**
- Weights and Biases (run metrics, hyperparameters, sample generations)
- Hugging Face Hub as model registry (dataset, adapter, GGUF, eval reports, model and dataset cards)

**Dev environment:**
- Local-native dev (uv-managed `.venv`); devcontainer retained in-repo
- uv for package management (uv sync to install, uv run to execute)
- ruff for linting, pytest for tests
- GitHub Actions: ruff + pytest CI gate
- Training: Northeastern Explorer HPC (A100); free-tier T4/Kaggle reproducible as fallback

**Dependency split:** The GPU training stack lives in a separate uv dependency group and is never installed in the CPU dev/serving environment. Serving deps are a minimal required set; eval/train/dev are optional groups (ADR 0047).

---

## Evaluation methodology

Five metrics, chosen to cover different failure modes:

| Metric | What it measures | Reliability |
|--------|-----------------|-------------|
| BLEU (sacrebleu) | N-gram overlap with reference | Low for short text; reported for completeness |
| ROUGE-L | Longest-common-subsequence overlap | Complementary to BLEU; also limited alone |
| Prefix-classification accuracy | Did the model emit the correct type (feat, fix, refactor, etc.)? | High; deterministic and meaningful |
| LLM-as-judge (Gemini 2.5 Flash free tier) | Four orthogonal axes: type-correctness, faithfulness, completeness, specificity | Headline metric |
| Human ratings (50 examples) | Same axes, rated by a human | Used to validate the judge; judge-vs-human agreement is reported |

The judge-vs-human agreement is the key number — it gives the judge score an honest confidence bound rather than reporting it as ground truth. The judge applies an analytic per-axis rubric: faithfulness is a hard gate (an unfaithful message fails regardless of other axes), and the headline is the conjunctive pass-rate — the fraction of outputs that clear all four axes. Headline numbers are reweighted to the true deployment commit-type distribution (ADR 0037).

---

## Project structure

```
committed/
├── README.md
├── CLAUDE.md                       # frozen agent behavioral contract
├── MASTER.md                       # single source of truth for the design
├── ROADMAP.md                      # phase map and progress log
├── pyproject.toml                  # uv-managed deps, serve-minimal + optional groups
├── uv.lock
├── .devcontainer/
│   └── devcontainer.json
├── .github/
│   └── workflows/
│       └── ci.yml                  # ruff + pytest gate
├── docs/
│   ├── decisions/                  # ADR records, one file per decision
│   ├── eval/judge_rubric.md        # the judge rubric (synced to ADR 0035)
│   ├── DECISION_LOG.md             # generated, do not edit by hand
│   └── decision-tree.md            # generated, do not edit by hand
├── scripts/
│   └── build_decision_log.py       # regenerates the decision log and tree
├── src/committed/
│   ├── cli.py                      # the `committed` console script
│   ├── data/                       # load, filter, build, push
│   ├── train/                      # config, train
│   ├── eval/                       # metrics, judge_gemini, human_rate, run_eval
│   ├── inference/                  # engine, prompt, grammar.gbnf
│   ├── serving/                    # api.py (FastAPI), Dockerfile
│   └── utils/
├── app/
│   └── gradio_app.py
├── configs/
├── analysis/                       # exploration scripts + saved eval results
└── tests/
```

---

## Roadmap

### v1 — shipped

Core:
- [x] Filtered dataset published to Hugging Face Hub
- [x] QLoRA fine-tune of Qwen3-1.7B, adapter on Hub, W&B tracked
- [x] Multi-metric eval: BLEU, ROUGE-L, prefix-classification accuracy, LLM-as-judge validated against 50 human ratings
- [x] Grammar-constrained GGUF inference (llama.cpp + GBNF)
- [x] Gradio demo deployed to HF Spaces
- [x] README with honest results and sample outputs

Production layer:
- [x] FastAPI serving endpoint + Dockerfile
- [x] Eval-in-CI regression gate
- [x] Hugging Face Hub model and dataset cards
- [x] Local CLI install path (`git diff | committed`) with GGUF auto-download
- [ ] Quantization quality-vs-latency benchmarks (Q4 / Q8 / fp16)

### v2 — next

- [ ] Smaller-model comparison: can Qwen3-0.6B hit the same numbers?
- [ ] Fine-tune for full multi-line commits (subject + body, not just the subject line)
- [ ] Address the specificity regression (relax subject-only normalization in the next data iteration)
- [ ] Synthetic reasoning-trace distillation; with-vs-without-reasoning ablation
- [ ] Reasoning-display toggle in the demo

### v3+ — directional

- [ ] Repo-specific style adaptation via RAG (retrieve similar past commits from the user's own repo)
- [ ] Multi-format output: Conventional Commits, Gitmoji, free-form
- [ ] VS Code extension (reads staged diff, fills the commit message box directly)
- [ ] Larger base models (3-7B) when compute permits

---

## Decision log

Every significant design and development decision is logged as an Architecture Decision Record in `docs/decisions/` (48 records and counting). The full log with a relationship diagram is in `docs/DECISION_LOG.md` and `docs/decision-tree.md`, both auto-generated by `scripts/build_decision_log.py`. Start with `docs/decisions/0001-adopt-adr-logging.md` and read forward.

---

## License

- Code: MIT
- Model adapter: Apache 2.0 (inherited from Qwen3-1.7B)
- Dataset: redistributed under the source's terms; CommitChronicle is cited in the dataset card (arXiv 2308.07655), with per-row `repo` and `license` provenance retained

---

Built by Muhammad Marzouk Baig — MS Artificial Intelligence, Northeastern University
