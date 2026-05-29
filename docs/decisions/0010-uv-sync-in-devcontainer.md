---
id: 0010
title: Run uv sync in the devcontainer postCreateCommand
date: 2026-05-29
status: accepted
supersedes: []
superseded_by: []
relates_to: [0007]
tags: [infra]
---

## Context
The devcontainer's postCreateCommand initially installed uv but did not run
uv sync, because no pyproject.toml existed on the first build. Now that
pyproject.toml and uv.lock are committed, a fresh Codespace has uv available but
no dependencies installed until they are synced manually.

## Decision
Extend postCreateCommand to run uv sync after installing uv, so every Codespace
build (and any fresh clone opened in a Codespace) installs the locked
dependencies automatically.

## Consequences
Codespace rebuilds are now fully automated and reproducible from the lockfile,
completing the goal set in 0007. Container creation takes slightly longer because
dependencies install during postCreate. The devcontainer now assumes pyproject.toml
and uv.lock are present, which they are.
