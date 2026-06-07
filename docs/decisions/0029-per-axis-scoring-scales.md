---
id: 0029
title: Per-axis scoring scales mixed by judgment shape
date: 2026-06-06
status: superseded
supersedes: []
superseded_by: [0035]
relates_to: [0028]
tags: [eval, judge]
---

## Context
The four axes defined in ADR 0028 have different judgment shapes. Some
questions have a natural binary answer (the type either is or is not
defensible; a claim either is or is not supported). Completeness is
inherently graded — a message can cover the main change but omit a
material secondary one, which is neither full coverage nor a total miss.
Using a uniform scale across all axes would impose a false granularity on
binary judgments or collapse a graded one.

## Decision
Scale follows the shape of the judgment, not a uniform convention:

- **Binary (`pass` / `fail`):** `type_correctness`, `faithfulness`,
  `specificity`. Each is two-valued by nature.
- **Three-level (`fail` / `partial` / `pass`):** `completeness` only.
  Coverage is genuinely graded; `partial` captures the intermediate case
  where the primary change is represented but a material secondary change
  is missing.

For any downstream aggregation or ranking:
- Normalize each axis to `[0, 1]`: binary → `{0, 1}`; three-level →
  `{0, 0.5, 1}`.
- Do not mix raw label strings across axes.

Judge-vs-human validation uses the statistic appropriate to the scale:
- Binary axes (`type_correctness`, `faithfulness`, `specificity`):
  agreement rate and Cohen's κ.
- `completeness`: Spearman correlation or weighted Cohen's κ (ordinal).
`run_eval.py` emits the right statistic per axis rather than a single
pooled agreement number.

## Consequences
Scoring granularity matches the discriminability of each judgment. Downstream
aggregation always normalizes to `[0, 1]` first. Validation reports a per-axis
statistic, making it possible to diagnose which axis has poor judge-vs-human
alignment independently.
