---
id: 0002
title: Reframe positioning to private, local, and distilled
date: 2026-05-29
status: accepted
supersedes: []
superseded_by: []
relates_to: []
tags: [scope]
---

## Context
Earlier positioning framed the project as the cheapest option that cannot beat
frontier models. That framing was defeatist and also inaccurate, since the
evaluation itself depends on a paid frontier API (the LLM-as-judge). It undersold
what the work actually delivers.

## Decision
Reframe around being private, local, and distilled: the model runs locally so a
user's code and diffs never leave their machine, there is zero per-call cost at
scale, and the headline technique is distilling a frontier model's commit-writing
ability into a roughly 1 to 2B model anyone can run.

## Consequences
Gives the project an honest story that does not depend on beating frontier models
on raw quality. Sets up distillation as the v2 throughline. Positions against
prior-art tools (aicommits, opencommit, Copilot) on privacy, since those send
diffs to a third-party API. Later scope decisions (0003, 0004) hang off this
framing.
