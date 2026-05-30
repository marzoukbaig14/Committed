# Committed — Master Design Document

**Status:** v1 locked. v2 planned. v3+ directional.

This document is the single source of truth for the design of Committed. Read it before doing any work. It can change, but only through the decision-log flow described in `handoffs/DECISIONLOG_AGENT.md`. Do not update it for minor implementation details; those belong in code comments and W&B run notes.

---

## Thesis

Committed is a small language model, fine-tuned to generate Conventional Commits messages from code diffs, that **runs locally so your code never leaves your machine.** It is built and deployed end to end on free infrastructure.

The positioning is **private, local, and distilled.** A model small enough to run on a laptop or in a free CPU container means zero per-call cost at scale, no network latency, offline capability, and most importantly no proprietary diff ever sent to a third-party API. The deeper technique on display is distillation: taking a frontier model's ability to write good commit messages and compressing it into a roughly one-to-two billion parameter model that anyone can run.

The contribution is engineering rigor across a complete applied-ML pipeline on a constrained budget: data curation logic, parameter-efficient fine-tuning, multi-metric evaluation validated against human ratings, and a real serving and deployment layer. This mirrors how most production ML actually ships.

## What this is, and is not

**This is:** applied ML on a narrow, structured task, optimized for privacy, locality, latency, and deployability, with production engineering as the headline skill on display.

**This is not:**
- A novel research contribution. Commit message generation has been studied since 2017.
- An attempt to beat frontier models on raw quality. A small local model will not beat Claude or GPT on quality, and that is fine; the value is that it runs locally for free.
- A general-purpose chatbot. Single task, structured output.

We acknowledge prior art openly in the README (tools like `aicommits`, `opencommit`, and Copilot's commit suggestions). Our position relative to them is explicit: those send your diff to a third-party API; this runs locally.

---

## Goals

### v1 — locked, must ship

v1 is split into a hard **core**, a strongly recommended **production layer**, and optional **stretch** work. Under time pressure, cut from the bottom up. Never cut the core.

**v1 core (irreducible; this is "done"):**
- A filtered Conventional Commits dataset on Hugging Face Hub.
- A QLoRA fine-tune of Qwen3-1.7B, adapter published to the Hub, every run tracked in W&B.
- A multi-metric eval: BLEU, ROUGE-L, prefix-classification accuracy, and an LLM-as-judge (Gemini 2.5 Flash, free tier) validated against 50 human ratings with the correlation reported.
- Grammar-constrained decoding that guarantees valid Conventional Commits output.
- A deployed Gradio demo on Hugging Face Spaces (CPU Basic, free).
- A README telling the private/local/distilled story honestly: what was built, what was learned, good and bad and weird sample outputs, and a failure-mode analysis from the human-rated set.

**v1 production layer (strongly recommended; this is the differentiator):**
- llama.cpp + GGUF serving with a FastAPI inference endpoint and a Dockerfile.
- Latency and throughput benchmarks, plus a quantization quality-versus-latency comparison (Q4 / Q8 / fp16).
- Evaluation in CI: ruff and pytest plus an eval-regression gate that runs on new adapters.
- Hugging Face Hub treated as a model registry, with proper model and dataset cards.

**v1 stretch (only if time allows):**
- A base-model comparison on the same fine-tune and eval harness: Qwen3-1.7B vs Qwen3-0.6B vs Qwen2.5-Coder-1.5B (optionally Llama-3.2-1B). This answers, with measured numbers, whether code specialization beats a newer general base on this task.
- A LoRA rank ablation (8 / 16 / 32).

**Descope order under time pressure:** drop the base-model comparison first, then the quantization table, then FastAPI (let Gradio call the model directly). **Never cut:** the working fine-tune, the human-validated judge, constrained decoding, the deployed demo, and the README.

**Success criterion:** v1 is done when the demo is live, the adapter and dataset are on the Hub, the eval is reported honestly, and the README tells the story, regardless of whether the fine-tune beats baseline by a small or large margin.

**Kill switch:** if the fine-tune fails to beat baseline meaningfully, ship anyway with honest reporting. A well-documented negative result is a strong portfolio signal. Note that with a current base model and constrained decoding, a weak result is much less likely than it was under the original TinyLlama plan.

### v2 — planned, open to change

- Generate synthetic reasoning traces with a free-tier LLM (provider chosen when v2 begins) for the same filtered dataset (`diff -> reasoning -> message`). This is the distillation step made explicit.
- Train a v2 model on the augmented schema.
- Headline analytical contribution: a with-versus-without-reasoning ablation. Bonus axis available because Qwen3 has native thinking modes: compare our distilled reasoning against the base model's own `/think` output.
- Add a reasoning-display toggle to the demo.
- Triggers: a small API budget (around $25) and/or Northeastern compute-cluster access.

### v3+ — directional

- Repo-specific style adaptation via RAG (retrieve similar past commits from the user's repo). This also fills a genuine gap: showing a working RAG pipeline.
- Multi-format output (Conventional Commits / Gitmoji / free-form, user-selected).
- A VS Code extension (a real distribution surface).
- Larger base models (3 to 7B) when compute permits.

---

## Locked Tech Stack

### Core
- Python 3.11+
- PyTorch 2.x
- `uv` for packaging (use `uv sync` and `uv run`; never manage a virtualenv by hand)
- `ruff` for linting, `pytest` for tests

### Modeling and training
- `transformers`, `peft` (LoRA), `accelerate`, `trl` (SFTTrainer)
- `unsloth` (roughly 2x faster QLoRA, drop-in with SFTTrainer)
- `bitsandbytes` (4-bit quantization) **for QLoRA training only, not for serving**
- Tokenization via `AutoTokenizer.from_pretrained(MODEL_NAME)`, never `tiktoken`

**Base model: `Qwen/Qwen3-1.7B`.** Chosen as the current best-in-class small base for fine-tuning, with strong code priors, a clean Apache 2.0 license, and native thinking modes that set up the v2 reasoning ablation. **In-family fallback: `Qwen/Qwen3-0.6B`** if CPU serving latency is unacceptable; swapping within the family does not change the serving code path. (Earlier planning used TinyLlama-1.1B; we moved off it because it is a 2023-era model, weak by current standards, and deliberately handicapped for a code task. See the decision log.)

### Data
- `datasets` (loads CommitChronicle from the Hub), `pandas`
- Not PyGithub, BigQuery, or tiktoken

### Serving and inference
- `llama-cpp-python` for CPU inference (this replaces bitsandbytes-on-CPU, which does not work; bitsandbytes 4-bit is CUDA-only)
- GGUF quantization (Q4_K_M as primary; Q8 and fp16 for the quality-versus-latency comparison)
- GBNF grammar-constrained decoding (native to llama.cpp) to guarantee valid Conventional Commits output
- `fastapi` for an inference endpoint (separates the serving API from the UI)
- Docker for the inference service

### Demo
- Gradio 5.x on Hugging Face Spaces, CPU Basic (free). With this stack a 1.7B model at Q4 should generate a short message in a few seconds on CPU, so paid ZeroGPU is likely unnecessary.

### Evaluation
- `evaluate`, `sacrebleu`, `rouge-score`
- `scikit-learn` (prefix-classification accuracy, confusion matrix)
- LLM-as-judge via the `google-genai` SDK, model `gemini-2.5-flash` on the free tier (pin a specific Flash model id for reproducible eval; the harness throttles and retries to respect free-tier rate limits)
- Hand-rolled eval harness. The README notes ecosystem awareness of `lm-eval-harness`, `lighteval`, and `inspect` without adopting them.

### Tracking and registry
- Weights & Biases (free tier) for run metrics, hyperparameters, and sample generations
- Hugging Face Hub as the model registry, with model and dataset cards

### Dev environment and CI
- GitHub Codespaces with a committed devcontainer (the canonical, reproducible dev environment)
- Colab T4 as the primary training box, Kaggle as backup, Northeastern cluster for larger runs
- GitHub Actions: ruff + pytest + an eval-regression gate

### Dependency split (important)
The training stack (`unsloth`, `bitsandbytes`) needs a GPU and must not be installed in the CPU Codespace. Use `uv` dependency groups: a default/dev group (CPU; installs in Codespaces) and a `train` group (GPU; installs only on Colab or the cluster). Trying to install the GPU training stack in a CPU container is a common source of dependency hell.

### Reasoning-trace generation (v2 only, deferred)
- A free-tier LLM provider, chosen when v2 begins (Gemini free tier is the default candidate)

---

## Architecture

```
                    ┌─────────────────────┐
                    │   GitHub repo       │  source of truth: code + docs
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼─────────────────────┐
          ▼                    ▼                     ▼
 ┌──────────────────┐  ┌────────────────┐   ┌──────────────────┐
 │ Codespaces       │  │ Colab / Kaggle │   │ NE cluster       │
 │ write code, data │  │ GPU training:  │   │ larger runs,     │
 │ eval, serving,   │  │ QLoRA via      │   │ when access      │
 │ demo (CPU)       │  │ Unsloth        │   │                  │
 └──────────────────┘  └───────┬────────┘   └────────┬─────────┘
                               │                     │
                               └──────────┬──────────┘
                                          ▼
                            ┌──────────────────────────┐
                            │  Hugging Face Hub         │  source of truth
                            │  dataset, LoRA adapter,   │  for artifacts
                            │  GGUF, eval reports,      │
                            │  model + dataset cards    │
                            └────────────┬─────────────┘
                                         │
                          ┌──────────────┴───────────────┐
                          ▼                              ▼
              ┌────────────────────────┐    ┌─────────────────────────┐
              │ Serving (local / CPU)  │    │ HF Spaces (Gradio demo)  │
              │ llama.cpp + GGUF       │    │ CPU Basic, calls the     │
              │ GBNF-constrained decode│    │ served model             │
              │ FastAPI endpoint       │    │                          │
              │ Dockerfile             │    │                          │
              └────────────────────────┘    └─────────────────────────┘

W&B logs every training run: hyperparameters, metrics, sample generations.
```

Hugging Face Hub is the source of truth for all artifacts. Training environments are ephemeral; datasets, adapters, GGUF files, and eval reports all live on the Hub so the next pipeline step, possibly run by a different agent in a different session, can pull from it.

---

## Data Plan

**Source:** CommitChronicle (Hugging Face, roughly 10.7M commits, pre-filtered).

**Filter pipeline:**
- Conventional Commits regex: `^(feat|fix|refactor|docs|test|chore|perf|style|build|ci)(\(.+\))?: .+`
- Message length: 5 to 200 characters
- **Diff size: capped to fit a small-model context.** The exact threshold is set empirically by inspecting the token distribution of real samples, not picked in advance. (The original plan stated a line range that did not correspond to any token budget; we cap by tokens instead. The model's sequence length is a training hyperparameter, not a locked decision.)
- Single-file changes only, to start: an easier task with less noise
- Drop merge commits, revert commits, and bot commits (Dependabot, GitHub Actions bot, and so on)
- Single language to start (Python), which is well represented in CommitChronicle

**Output:** a `username/committed-train` Hub dataset, target 30 to 50k pairs. Retains the `repo` and `license` columns for per-row provenance (see ADR 0012 and Licensing).

**Schema (modular for v1 and v2):**
```python
{
    "diff": str,                   # the code diff
    "message": str,                # the conventional commit message
    "reasoning_trace": str | None, # v2 populates this; None in v1
}
```

**Split:** 90/5/5 train/val/eval, stratified by commit type if practical.

---

## Training Plan

- **Method:** QLoRA (4-bit base plus a LoRA adapter) via Unsloth and TRL's SFTTrainer
- **Hardware:** Colab free T4 primary, Kaggle backup, NE cluster for larger runs
- **Checkpoints:** push to the Hub every N steps; never rely on Colab disk alone
- **Tracking:** every run logged to W&B with hyperparameters, eval metrics, and sample generations

**Hyperparameter starting points (tune from here):**
- LoRA rank: 16 (ablate 8 and 32 if time allows)
- LoRA alpha: 32
- Learning rate: 2e-4 (standard for QLoRA)
- Batch size: tune to fit T4 VRAM
- Epochs: 1 to 3 (watch the eval curve for overfit)
- Sequence length: an implementation detail, tuned to the filtered diff distribution

---

## Serving Plan

This layer is the production-engineering signal and is part of v1.

- **Merge and convert:** merge the LoRA adapter into the base, convert to GGUF, quantize. Q4_K_M is the primary serving artifact; also produce Q8 and keep an fp16 reference for the comparison.
- **Inference:** `llama-cpp-python` runs the GGUF model on CPU. This is what makes free CPU-Basic serving viable; bitsandbytes 4-bit will not run on CPU.
- **Constrained decoding:** a GBNF grammar encodes the Conventional Commits format, so every generation is valid by construction. This is cheap once we are on llama.cpp and is a strong reliability signal for a small model.
- **API:** a FastAPI endpoint exposes generation, separate from the UI, so the serving path is a real service and not just a notebook.
- **Container:** a Dockerfile packages the inference service for reproducible deployment.
- **Benchmarks:** measure latency and throughput, and report a quality-versus-latency table across Q4 / Q8 / fp16 in the README.

---

## Evaluation Plan

Multi-metric, with the human-validated LLM-as-judge as the headline.

1. **BLEU (sacrebleu):** automatic, noted as unreliable for short text but reported for completeness.
2. **ROUGE-L:** automatic, complementary.
3. **Prefix-classification accuracy:** categorical and deterministic; did the model pick the right `feat` / `fix` / `refactor` / etc.?
4. **LLM-as-judge (`gemini-2.5-flash`, free tier)** on 500 to 1000 examples: rubric scoring on type-correctness, specificity, scope-correctness, and conciseness.
5. **50 human-rated examples:** used to validate the judge; report the correlation between judge scores and human ratings.

**The README must report:** all five metrics, sample outputs (good, bad, weird) with commentary, and a failure-mode analysis from the human-rated set.

---

## Output Format

### v1
```
type(scope): short imperative description
```
Constrained to the Conventional Commits grammar at decode time, so output is always well-formed.

### v2
```
<reasoning>
2 to 4 lines: which file changed, the nature of the change, the type and scope justification
</reasoning>
<commit>type(scope): short imperative description</commit>
```
The demo gains a reasoning-display toggle in v2.

---

## Project Structure

```
committed/
├── README.md
├── CLAUDE.md                  # frozen agent contract
├── pyproject.toml             # uv-managed deps, with a [dev] and a [train] group
├── uv.lock
├── .gitignore
├── .env.example               # template; real .env is gitignored
├── .devcontainer/
│   └── devcontainer.json      # the reproducible dev environment
├── .github/workflows/ci.yml   # ruff + pytest + eval-regression gate
├── docs/
│   ├── decisions/             # ADR records, one file per decision
│   ├── DECISION_LOG.md        # generated
│   └── decision-tree.md       # generated
├── scripts/
│   └── build_decision_log.py  # regenerates the log and tree from records
├── data/                      # gitignored scratchpad
├── src/committed/
│   ├── __init__.py
│   ├── data/                  # load.py, filter.py, push.py
│   ├── train/                 # config.py, train.py
│   ├── eval/                  # metrics.py, judge.py, human_rate.py, run_eval.py
│   ├── inference/             # generate.py, prompt.py, grammar.gbnf
│   ├── serving/               # api.py (FastAPI), Dockerfile
│   └── utils/                 # hub.py
├── configs/                   # YAML training configs per run
├── notebooks/                 # exploration only, not production
├── app/
│   └── gradio_app.py          # HF Spaces entry point
└── tests/
```

---

## Timeline

**Ship v1 core regardless. Burnout beats polish.**

Honest estimate: v1 core in roughly two to three weeks; core plus the production layer in roughly three to four weeks. The detailed near-term plan is in `ROADMAP.md`. Days will slip; that is expected, and the descope ladder is there for exactly that reason.

---

## Working Norms

- **Plumbing is delegable; the core is the human's.** Agents may write scaffolding, config, CI, upload helpers, and the like. The human writes the data filter logic, the training config, the eval metrics, and the judge prompt.
- **Hub is the source of truth for artifacts.** Pull from the Hub, push to the Hub. Push checkpoints often; Colab disconnects.
- **One agent, one responsibility.** Each spawned agent owns a single file or task.
- **Modular schema.** Records always include `reasoning_trace` (None in v1). Training and inference read and condition on it when present.
- **Honest reporting.** The README documents what worked and what did not. Negative results are fine.
- **Decisions are logged.** Design and dev decisions route through the decision-log flow.

---

## Licensing

- Code: MIT
- LoRA adapter: Apache 2.0 (inherited from Qwen3-1.7B)
- Filtered dataset: redistributed under the source's terms (ADR 0012). CommitChronicle aggregates permissively licensed repos (MIT, Apache-2.0, BSD-3-Clause); we retain the `repo` and `license` columns for per-row provenance, attribute CommitChronicle and its paper (arXiv 2308.07655) in the dataset card, and carry the sensitive-data caveat forward. Automated scrubbing is deferred and noted as a known limitation.

---

## Open Questions

- Exact final dataset size (target 30 to 50k; depends on filter strictness, decided after inspecting real samples)
- Whether to run the LoRA rank ablation inside v1 or defer to v2 (time-dependent)
- The v2 reasoning-trace budget (pending Northeastern compute access or an Anthropic API budget)
- All of v3 (RAG, multi-format, IDE integration, larger models), revisited after v1 ships

---

*This document is the contract for what we build. Update it only through the decision-log flow when a locked decision changes.*