# Committed — Master Design Document

**Status:** v1 locked. v2 planned. v3+ directional.

This document is the single source of truth for the design of Committed. Read it before doing any work. It can change, but only through the decision-log flow described in `handoffs/DECISIONLOG_AGENT.md`. Do not update it for minor implementation details; those belong in code comments and W&B run notes.

---

## Thesis

Committed is a small language model, fine-tuned to generate Conventional Commits messages from code diffs, that **runs locally so your code never leaves your machine.** It is built and deployed end to end on free infrastructure. The v1 core is reproducible on free infrastructure (a free Colab T4 fits the 1.7B QLoRA on this dataset); an institutional HPC cluster is used only to accelerate training and run the stretch ablations (ADR 0019).

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
- LLM-as-judge via the `google-genai` SDK, model `gemini-2.5-flash` (free tier; ADR 0011). The judge harness is backend-swappable (ADR 0034): a Claude Sonnet 4.6 backend (`anthropic` SDK, prompt caching, forced tool-use, cost guardrails) is available as an optional upgrade once API credits are secured; `anthropic` is an optional dependency, not installed by default
- Hand-rolled eval harness. The README notes ecosystem awareness of `lm-eval-harness`, `lighteval`, and `inspect` without adopting them.

### Tracking and registry
- Weights & Biases (free tier) for run metrics, hyperparameters, and sample generations
- Hugging Face Hub as the model registry, with model and dataset cards

### Dev environment and CI
- GitHub Codespaces with a committed devcontainer (the canonical, reproducible dev environment)
- Training primary: an institutional HPC cluster (many GPUs, ~1 TB storage). Colab T4 / Kaggle kept as the free-tier-reproducible fallback — the v1 core fine-tune must remain runnable on a free T4 to preserve the free-infrastructure thesis (ADR 0019)
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

**Filter pipeline (regex relaxed per ADR 0017):**
- Conventional Commits regex on the subject line (first line), case-insensitive, with an optional `(scope)`, an optional breaking-change `!`, and a required `: ` separator:
  `^(feat|fix|refactor|docs|test|chore|perf|style|build|ci|doc)(\([^)]+\))?!?: .+` (IGNORECASE). The `doc` alias is normalized to `docs`. Deliberately excluded: `revert` (revert commits are dropped), non-standard types (`deps`/`wip`/`release`), bracketed-type styles (`[Chore]`, deferred), and subjects with no colon or a path prefix (left to a possible future classifier-based harvest of good-but-unformatted messages).
- Subject-line length: at most 200 characters (upper outlier guard); no floor — the CC regex already requires a non-empty description (ADR 0020)
- **Diff size: capped by tokens to fit a small-model context.** Over-cap diffs are dropped, not truncated, since a truncated diff could omit the very change the message describes. The exact threshold is set empirically by inspecting the token distribution of real samples, not picked in advance. (The original plan stated a line range that did not correspond to any token budget; we cap by tokens instead. The model's sequence length is a training hyperparameter, not a locked decision.)
- Single-file changes only, to start: an easier task with less noise
- Drop merge commits, revert commits, and bot commits; bots are detected by the dependency-bump message template, since the author field is anonymized (ADR 0021)
- All CommitChronicle languages, with each file's language identified by extension via a language→extension map — not the per-repo language column, which mislabels polyglot repos (ADR 0022, ADR 0023)

**Target normalization (ADR 0017):** applied to the matched subject line to build the training target.
1. lowercase the type (`Fix:` -> `fix:`)
2. map `doc` -> `docs`
3. strip the breaking-change `!` (`feat!:` -> `feat:`)
4. subject line only — multi-line commits are kept, the body is dropped
5. strip surrounding whitespace
6. strip a single trailing period
7. scope casing left unchanged (scopes are identifiers; lowercasing would distort them)
8. description casing left unchanged (blind lowercasing mangles acronyms; accepted v1 limitation)

**Output (target revised per ADR 0025):** a `username/committed-train` Hub dataset spanning all CommitChronicle languages (ADR 0023). The full collection pass produced a 189,330-row pool; after the per-language cap (6,000) and floor (500) defined in ADR 0025 the balanced dataset is approximately 59k rows. The earlier Python-only 20–30k raw / 15–25k usable projection (ADR 0018) was inflated by per-repo language mislabeling (ADR 0022) and is superseded by the actual pool count. Exact post-cap sizes confirmed by `uv run python src/committed/data/build.py --dry-run` before publishing. Retains the `repo` and `license` columns for per-row provenance (see ADR 0012 and Licensing).

**Schema (modular for v1 and v2):**
```python
{
    "diff": str,                   # the code diff
    "message": str,                # the conventional commit message
    "reasoning_trace": str | None, # v2 populates this; None in v1
}
```

**Split:** 90/5/5 train/val/eval, stratified by commit type only (ADR 0026; the earlier type × language grid was removed because the per-language cap makes all language volumes comparable before the split step, so the two-dimensional grid universally produced thin cells and was dead code). Per-language cap: 6,000 rows (downsampled above); floor: 500 rows (dropped below). Cap and floor are reversible build-time parameters in `src/committed/data/build.py` (ADR 0025).

---

## Training Plan

- **Method:** QLoRA (4-bit base plus a LoRA adapter) via Unsloth and TRL's SFTTrainer
- **Prompt:** a single canonical zero-shot prompt (`src/committed/inference/prompt.py`, ADR 0040) wraps every training example and is reused verbatim at baseline and fine-tuned inference, so the before/after delta is attributable to fine-tuning and the train/inference diff format cannot drift. Diff serialized near-raw as `Diff:\n{diff}`; Qwen3 thinking suppressed via `enable_thinking=False`
- **Hardware:** institutional HPC cluster primary (many GPUs, ~1 TB storage); Colab T4 / Kaggle as the free-tier-reproducible fallback. The v1 core fine-tune stays runnable on a free T4 (ADR 0019)
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

- **Merge and convert:** merge the LoRA adapter into the base, convert to GGUF, quantize. Q4_K_M is the primary serving artifact; also produce Q8 and keep an fp16 reference for the comparison. The baseline is pinned to the same quant — `ggml-org/Qwen3-1.7B-GGUF`, `Qwen3-1.7B-Q4_K_M.gguf` (ADR 0038), pulled into a gitignored `models/` cache — so the before/after delta isolates fine-tuning, not quantization.
- **Inference:** `llama-cpp-python` runs the GGUF model on CPU. This is what makes free CPU-Basic serving viable; bitsandbytes 4-bit will not run on CPU.
- **Constrained decoding:** a GBNF grammar (`src/committed/inference/grammar.gbnf`, ADR 0039) encodes the Conventional Commits format — the ten-type filter codebook, optional `(scope)`, no `!`, single-line no-trailing-period description — so every generation is valid by construction. It enforces format, not semantics; semantic errors are caught by the judge. Cheap on llama.cpp and a strong reliability signal for a small model.
- **API:** a FastAPI endpoint exposes generation, separate from the UI, so the serving path is a real service and not just a notebook.
- **Container:** a Dockerfile packages the inference service for reproducible deployment.
- **Benchmarks:** measure latency and throughput, and report a quality-versus-latency table across Q4 / Q8 / fp16 in the README.

---

## Evaluation Plan

Multi-metric, with the human-validated LLM-as-judge as the headline.

1. **BLEU (sacrebleu):** automatic, noted as unreliable for short text but reported for completeness.
2. **ROUGE-L:** automatic, complementary.
3. **Prefix-classification accuracy:** categorical and deterministic; did the model pick the right `feat` / `fix` / `refactor` / etc.?
4. **LLM-as-judge (`gemini-2.5-flash`, free tier — ADR 0011; Claude Sonnet 4.6 optional upgrade — ADR 0034)** on 500 to 1000 examples: analytic per-axis rubric with four orthogonal axes, all binary `pass|fail` (ADRs 0027–0035):
   - `type_correctness` — passes unless the type is a misrepresentation of the diff (ADR 0036): (1) wrong category — the type names an activity the diff does not perform, or (2) suppressed consequence — the correct type carries a downstream expectation (e.g. semver signal) that the chosen type masks. A type a reviewer would merely prefer, but that is defensible, passes. Scored on plausibility, not exact-match.
   - `faithfulness` — are all atomic claims supported by the diff? Operationalized as decomposed per-claim precision: what-changed claims must be supported; rationale claims pass unless contradicted. Hard gate: a fail disqualifies the message regardless of other axes.
   - `completeness` — does the message cover the primary and all material changes? Supporting detail and refactor plumbing are not materially distinct; vagueness is charged to specificity, not completeness.
   - `specificity` — is the description concrete rather than generic?
   **Primary metric:** conjunctive pass-rate (all four axes pass). Per-axis vector always reported. Graded score `1 + completeness{0,1} + specificity{0,1}` (integer 1–3, faithful messages only) for checkpoint ranking. Self-consistency via majority-vote over 3 samples intended for faithfulness. Stability number (Krippendorff's α or re-judge agreement) reported alongside judge-vs-human agreement. Anchors in `docs/eval/judge_rubric.md` (ADR 0035).
   **Headline reweighting (ADR 0037):** the judge set is an equal-allocation strata sample (~442 rows); the real test split is ~49% `fix`. Sample-level headline numbers are reported as diagnostics only. The primary headline reweights per-type metrics to the true test-split type distribution so the reported numbers reflect deployment behavior.
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
├── analysis/                  # exploration scripts + saved results (analysis/results/)
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

- Exact final dataset size (~59k after cap/floor per ADR 0025; confirmed by `build.py --dry-run` before Hub push)
- Whether to run the LoRA rank ablation inside v1 or defer to v2 (time-dependent)
- The v2 reasoning-trace budget (pending Northeastern compute access or an Anthropic API budget)
- All of v3 (RAG, multi-format, IDE integration, larger models), revisited after v1 ships

---

*This document is the contract for what we build. Update it only through the decision-log flow when a locked decision changes.*