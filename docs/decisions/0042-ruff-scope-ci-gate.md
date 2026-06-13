---
id: 0042
title: Scope ruff to the package and tests; add the CI lint + test gate
date: 2026-06-11
status: accepted
supersedes: []
superseded_by: []
relates_to: [0024, 0041]
tags: [infra, process]
---

## Context
With CI added (ADR 0041), the lint and test gate needs a defined scope. The `analysis/`
directory holds exploration scripts and notebooks that are not shipped and are not held
to the package's style bar; linting them would block CI on throwaway code. The smoke
test authenticates to live services and cannot run on a tokenless CI runner.

## Decision
- **Lint scope:** ruff lints the shipped package (`src/committed`) and `tests`;
  `analysis/` and `notebooks/` are excluded via
  `[tool.ruff] extend-exclude = ["analysis", "notebooks"]` in `pyproject.toml`.
- **CI gate** (`.github/workflows/ci.yml`, on push to `main` and on PRs): `uv sync --locked`
  → `ruff check .` → `pytest tests/test_filter.py tests/test_build.py`. The deterministic,
  offline filter/build tests are the reproducibility signal; `smoke_test.py` is excluded
  because it needs live HF / W&B / Gemini tokens the runner does not have.
- One package fix to pass the gate: `build.py` `lambda` → `def` (ruff E731).

## Consequences
Shipped code is held to the lint bar while exploration code iterates freely, unlinted.
CI is green and fully deterministic — no network dependency — so it is a clean
reproducibility proof rather than a flaky external check. The gate runs on every push to
`main` and on every PR.
