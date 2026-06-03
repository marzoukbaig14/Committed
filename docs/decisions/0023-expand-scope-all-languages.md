---
id: 0023
title: Expand the dataset scope from Python-only to all CommitChronicle languages
date: 2026-06-03
status: accepted
supersedes: [0018]
superseded_by: []
relates_to: [0022]
tags: [data, scope]
---

## Context
With the corrected extension-based filter (0022), a Python-only build projects to
roughly 2 to 5k usable pairs — well below the 15 to 25k target set in 0018. That
target was itself inflated by the per-repo language contamination that 0022 fixes.
"Single language (Python) to start" was a data-plan simplification, not a thesis
requirement; the private, local, distilled positioning is language-agnostic. An
all-languages expansion was pre-identified as the lever for exactly this contingency.

## Decision
Include all CommitChronicle languages rather than Python only. Identify each commit's
file language by extension via a language-to-extension map (per 0022). Stratify the
train/validation/eval split by language in addition to commit type (or cap per
language) so no single ecosystem dominates, and re-profile the diff token cap across
languages. This supersedes the "single language to start" data-plan element and the
0018 size target; the final size is re-derived from an all-languages estimate and the
build pass.

## Consequences
Roughly a 10 to 20x increase in candidate data, comfortably clearing the target and
likely allowing the dataset to be sampled down to about 20 to 30k. The result is a
multi-language tool, arguably a stronger product story. The base model stays
Qwen3-1.7B: model size is bounded by the local and CPU serving thesis, not by data
volume, and the task remains within the model's capacity (a unified diff is
structurally language-agnostic and Qwen3 already has multilingual code priors). The
final dataset size is confirmed by the re-estimate.
