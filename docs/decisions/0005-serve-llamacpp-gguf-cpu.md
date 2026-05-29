---
id: 0005
title: Serve via llama.cpp and GGUF on CPU, not bitsandbytes
date: 2026-05-29
status: accepted
supersedes: []
superseded_by: []
relates_to: [0004]
tags: [serving]
---

## Context
The serving target is CPU-only on a free tier. bitsandbytes 4-bit quantization is
CUDA-only and will not run on CPU, so it cannot be the serving path.

## Decision
Serve with llama.cpp via llama-cpp-python, using GGUF-quantized weights (Q4_K_M
primary; Q8 and fp16 for the quality-versus-latency comparison). Retain
bitsandbytes for QLoRA training only. llama.cpp also natively supports GBNF
grammars, which 0009 relies on.

## Consequences
Free CPU-Basic serving becomes viable. The training and serving quantization
paths are now deliberately different (bitsandbytes for training, GGUF for
serving), which is worth keeping clear. Enables cheap grammar-constrained
decoding.
