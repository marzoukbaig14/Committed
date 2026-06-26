---
id: 0006
title: Split dependencies into a CPU/dev group and a GPU/train group
date: 2026-05-29
status: superseded
supersedes: []
superseded_by: [0047]
relates_to: []
tags: [infra]
---

## Context
The training stack (unsloth, bitsandbytes) requires CUDA and must never install
in the CPU Codespace. A previous setup session lost time forcing GPU dependencies
into a CPU container.

## Decision
Use uv dependency groups to separate a default/CPU group that installs in
Codespaces (datasets, pandas, transformers, llama-cpp-python, gradio, fastapi,
uvicorn, the eval libraries, anthropic, wandb, pyyaml, and so on) from a train
group that installs only on GPU machines (unsloth, bitsandbytes, accelerate,
peft, trl).

## Consequences
Prevents the dependency hell from the prior session. The Codespace stays lean and
CPU-only. GPU machines install the train group separately. Adds a small ongoing
discipline: deciding which group each new dependency belongs in.
