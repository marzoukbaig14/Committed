---
id: 0038
title: Pin baseline GGUF artifact to Qwen3-1.7B Q4_K_M
date: 2026-06-11
status: accepted
supersedes: []
superseded_by: []
relates_to: [0003, 0005, 0009]
tags: [serving, eval, infra]
---

## Context
The baseline generation and serving path needs a concrete GGUF artifact and a
fixed quantization. Two forces pin the choice:

- Qwen's own GGUF repo ships only `Q8_0`. `Q4_K_M` — the primary serving target
  in MASTER's Serving Plan — comes from the `ggml-org` conversion instead.
- A fair before/after comparison requires the baseline to run at the *same*
  quantization the fine-tune will be served at. If the baseline ran fp16/Q8 and
  the fine-tune ran Q4_K_M, the measured delta would conflate fine-tuning with
  quantization loss.

## Decision
The baseline runs `ggml-org/Qwen3-1.7B-GGUF`, file `Qwen3-1.7B-Q4_K_M.gguf`
(~1.2 GB, Apache-2.0). The file is pulled into a gitignored `models/` directory
and re-fetched from the Hub as needed; it is never committed. Inference loads it
with `n_ctx=4096` and renders prompts through the `Qwen/Qwen3-1.7B` tokenizer's
chat template (see `src/committed/inference/generate.py`). `Q8_0` and `fp16` are
reserved for the later quality-vs-latency comparison table, not the baseline.

## Consequences
The before/after delta isolates fine-tuning rather than quantization, because both
sides run Q4_K_M. The Hub is the source of truth for the artifact; the local
`models/` file is a cache, consistent with the project's ephemeral-compute model.
The project now carries a pin on a specific third-party (`ggml-org`) conversion;
if that repo changes or disappears, the baseline must be re-pinned or re-converted.
