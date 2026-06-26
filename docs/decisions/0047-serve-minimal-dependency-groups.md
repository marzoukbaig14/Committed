---
id: 0047
title: Split dependencies into a serve-minimal required set with eval/train/dev groups
date: 2026-06-17
status: accepted
supersedes: [0006]
superseded_by: []
relates_to: [0005, 0024, 0043]
tags: [infra, serving, deps]
---

## Context
`[project.dependencies]` listed the entire stack as required: the serving runtime
(llama-cpp-python, transformers, fastapi, uvicorn, gradio) alongside eval-only deps
(google-genai, sacrebleu, rouge-score, scikit-learn, evaluate, pandas, datasets,
wandb, pyyaml) and the training stack (already isolated in a `train` group).

The HF Gradio Space (ADR 0043 surface) installs the package to run only the inference
path. With everything required, two problems followed. First, installing the package
on the Space (`committed @ git+...`) pulled the full tree and, combined with compiling
llama-cpp-python from source, exceeded the Space build time limit ("Job timeout").
The interim fix was a hand-maintained `requirements.txt` plus a vendored copy of
`committed/` uploaded directly to the Space — which means the Space and the GitHub
repo can silently diverge, the worst failure mode for a project whose thesis is
reproducibility (ADR 0024).

The serving path imports were checked directly: nothing under `src/committed/inference/`
or `src/committed/serving/` imports pandas, datasets, wandb, or yaml. `train.py` does
import yaml (`yaml.safe_load` of the run config). The decision-log generator
(`scripts/build_decision_log.py`) also parses YAML.

## Decision
Restructure dependencies by the import graph: a dependency is **required** only if the
serving/demo path (`engine.py`, `serving/api.py`, `app.py`) imports it. Everything else
moves to an optional group, with the rule that when membership is uncertain a dep stays
required (a heavier build is a nuisance; a missing serving dep is a broken Space).

- **`[project.dependencies]` (required):** fastapi, gradio, llama-cpp-python,
  transformers, uvicorn.
- **`eval` group:** datasets, evaluate, google-genai, pandas, pyyaml, rouge-score,
  sacrebleu, scikit-learn, wandb.
- **`train` group:** accelerate, bitsandbytes, peft, trl, torch — plus pyyaml (config
  loading) and wandb (run tracking), duplicated here because training needs them
  independently of eval.
- **`dev` group:** matplotlib, pytest, ruff — plus pyyaml, because the decision-log
  generator needs it and base `uv sync` no longer installs it.

The Space's `requirements.txt` collapses to the prebuilt-CPU-wheel index line plus
`committed @ git+https://github.com/marzoukbaig14/Committed.git`, and the vendored
`committed/` folder is deleted from the Space so the GitHub-installed package is the
one imported. GitHub becomes the single source of truth again.

## Consequences
- The Space build pulls only the serving set, so it builds fast, and there is one
  source of truth: edits land in the repo and the Space rebuilds from it. No more
  hand-maintained vendored copy.
- Eval and training now require an explicit group: `uv sync --group eval` /
  `uv sync --group train`. A bare `uv sync` yields a serving/dev-only environment.
- pyyaml and wandb intentionally appear in more than one group; uv dedupes on install.
- A serving-path import added later that pulls an eval/train-only dep will break the
  Space build until that dep is promoted to required — the tradeoff for a small
  required set. The import-graph rule and a green Space build are the guardrails.
- The Space still serves the fine-tune via the GGUF env vars (ADR 0038 path); decode
  parity is unaffected since this changes packaging only, not inference code.