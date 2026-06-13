---
id: 0041
title: Migrate dev surface to local-native; relocate the reproducibility guarantee to CI
date: 2026-06-11
status: accepted
supersedes: []
superseded_by: []
relates_to: [0007, 0010]
tags: [infra, process]
---

## Context
ADR 0007 made GitHub Codespaces plus a committed devcontainer the canonical dev
environment, on the reasoning that the human has no fixed machine (shared school
computers) and so reproducibility had to be guaranteed by the container. Mid-session
the NU Enterprise organisation's Codespaces budget was blocked, removing access to
that environment.

## Decision
This **amends ADR 0007** (it does not abandon its reproducibility intent — it relocates
where the guarantee is verified):

- Day-to-day development moves to **local-native**: Windows + VS Code + a `uv` `.venv`.
- The **devcontainer is retained** in the repo; it remains valid if Codespaces returns.
- The reproducibility guarantee that previously rested on a locally-run container is
  **relocated to CI**: a clean GitHub Actions runner runs `uv sync --locked`, which
  fails the build if `uv.lock` is stale or cannot be satisfied exactly. Reproducibility
  is now proven on every push, on a machine with none of the developer's local state.

Codespaces may return (the GitHub Student Pack provides personal-account hours); the
block was an org-budget matter, not a permanent loss.

## Consequences
Reproducibility no longer depends on any single machine or on Codespaces being
available — it is enforced by CI. The local Windows surface has no GPU and no C++
compiler, so `llama-cpp-python` (a serving dependency) is skipped locally via
`uv sync --no-install-package llama-cpp-python` and is built on Linux/CI instead;
this motivates the still-open proposal to move serving deps into an optional `serve`
group. Training continues to run on the HPC cluster (ADR 0019), unaffected.
