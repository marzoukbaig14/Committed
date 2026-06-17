---
id: 0044
title: Adapter-merge → GGUF → Q4_K_M serving-artifact pipeline
date: 2026-06-16
status: accepted
supersedes: []
superseded_by: []
relates_to: [0038]
tags: [serving, infra]
---

## Context
After fine-tuning, the LoRA adapter lives on the Hub as a delta on top of the base model.
The serving layer (ADR 0005) needs a self-contained GGUF at Q4_K_M — the same quantization
pinned for the baseline (ADR 0038) — so that the before/after eval isolates fine-tuning
rather than quantization differences. A reproducible, documented path from adapter to
servable artifact was needed.

## Decision
Three-step pipeline implemented in `scripts/merge_adapter.py`:

1. **Merge** — load base + LoRA adapter, call `merge_and_unload()`, save merged weights in
   fp16 to a local staging directory.
2. **Convert** — run `convert_hf_to_gguf.py` (llama.cpp tooling) on the merged fp16 model
   to produce an f16 GGUF intermediate.
3. **Quantize** — run `llama-quantize` on the f16 GGUF to produce the final Q4_K_M GGUF.

Source adapter: `marzoukbaig14/committed-qwen3-1.7b-lora` (Hub). The resulting Q4_K_M GGUF
is the serving artifact, matching the baseline quant (ADR 0038).

## Consequences
- Any future fine-tune iteration runs the same three-step script to produce a comparable
  serving artifact; the quantization choice is fixed by ADR 0038 and must not change without
  a new ADR.
- The f16 intermediate is large (~3 GB) and ephemeral; it is not committed to the repo or
  pushed to the Hub — only the Q4_K_M GGUF is the artifact.
- The pipeline requires a Linux environment with llama.cpp binaries available (CI or HPC);
  it cannot run on the local Windows dev machine.
