---
id: 0024
title: Make the project an installable package (src-layout with a hatchling build backend)
date: 2026-06-03
status: accepted
supersedes: []
superseded_by: []
relates_to: [0010]
tags: [infra, packaging]
---

## Context
MASTER's project structure specifies a `src/committed/` package and a uv-managed
`pyproject.toml`, but the package was never actually created and `pyproject.toml` was
initialized as an application with no `[build-system]`. As a result `committed` was
not importable: tests and scripts doing `from committed.data ... import` failed with
`ModuleNotFoundError`, and a `filter.py` had landed in the gitignored root `data/`
scratchpad rather than in the package. This architectural step slipped through the
initial setup.

## Decision
Make the project an installable package. Create `src/committed/` with `__init__.py`
files and the `data/` subpackage, add a `[build-system]` (hatchling) and
`[tool.hatch.build.targets.wheel] packages = ["src/committed"]` to `pyproject.toml`,
and install it editable via `uv sync`. Source modules live under `src/committed/`;
the root `data/` directory remains a gitignored scratchpad only.

## Consequences
`committed` imports cleanly from tests, scripts, and analysis in the Codespace and in
CI, with no PYTHONPATH workarounds. Completes the package architecture MASTER already
assumed. Records a setup constraint the project now carries: a build backend is
required for the editable install.
