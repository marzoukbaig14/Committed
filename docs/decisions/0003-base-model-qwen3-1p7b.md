---
id: 0003
title: Use Qwen3-1.7B as the primary base model
date: 2026-05-29
status: accepted
supersedes: []
superseded_by: []
relates_to: [0002]
tags: [model, training]
---

## Context
Earlier planning selected TinyLlama-1.1B, chosen for a "make the tiny old model
work" narrative. TinyLlama is a 2023-era model, weak by current standards, and
not code-specialized, which would likely have produced mediocre output. The
binding deployment constraint is CPU-only serving on a free tier, which caps
practical model size at roughly 1 to 2B parameters. Current benchmarks place the
Qwen3 family at the top for small-model fine-tuning, and Qwen has strong code
priors.

## Decision
Use Qwen/Qwen3-1.7B as the primary base, with Qwen/Qwen3-0.6B as an in-family
fallback if CPU serving latency is unacceptable. Apache 2.0 license. Its native
thinking modes also set up the v2 reasoning ablation.

## Consequences
Better expected output quality than TinyLlama and a current, defensible choice.
The earlier TinyLlama selection is abandoned. Serving code is unaffected by the
1.7B-to-0.6B fallback. The "make a weak model work" narrative is replaced by the
stronger "small model distilled to match much larger ones on a narrow task."
