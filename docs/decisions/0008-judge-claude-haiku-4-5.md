---
id: 0008
title: Use claude-haiku-4-5 as the LLM-as-judge
date: 2026-05-29
status: accepted
supersedes: []
superseded_by: []
relates_to: []
tags: [eval]
---

## Context
The earlier plan named Claude Haiku 3.5 as the judge, a generation behind. For a
reproducible evaluation the judge model must be pinned.

## Decision
Use claude-haiku-4-5 as the LLM-as-judge, pinned to the snapshot
claude-haiku-4-5-20251001. It scores a rubric (type-correctness, specificity,
scope-correctness, conciseness) and is validated against 50 human-rated examples,
with the correlation reported.

## Consequences
The eval reflects a current model and is reproducible across runs. Introduces a
small paid-API dependency and cost for evaluation. Human validation keeps the
automated judge honest.
