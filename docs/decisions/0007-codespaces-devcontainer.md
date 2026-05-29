---
id: 0007
title: Use Codespaces plus a committed devcontainer as the canonical dev environment
date: 2026-05-29
status: accepted
supersedes: []
superseded_by: []
relates_to: [0006]
tags: [infra]
---

## Context
The human has no fixed personal machine and works from shared school computers,
so the environment must rebuild identically anywhere. Reproducibility is
non-negotiable.

## Decision
Adopt GitHub Codespaces with a committed .devcontainer/devcontainer.json as the
canonical dev environment. The devcontainer pins Python 3.11 and installs uv on
creation; the CPU dependency group installs via uv sync.

## Consequences
The shared-machine problem disappears: anyone opening the repo in a Codespace
gets the identical setup, and local machine state can never be a hidden
dependency. Training still happens off-Codespace on GPU machines.
