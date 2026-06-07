---
id: 0028
title: Finalize judge axis set to four orthogonal axes
date: 2026-06-06
status: accepted
supersedes: [0027]
superseded_by: []
relates_to: []
tags: [eval, judge]
---

## Context
ADR 0027 adopted the analytic per-axis rubric architecture and named four
dimensions: `type_correctness`, `specificity`, `scope_correctness`,
`conciseness`. For subject-line-only commit messages, `scope_correctness`
and `conciseness` add low-signal, overlapping judgments that risk near-
arbitrary scores:

- `scope_correctness` requires inferring the author's intended scope from
  the diff alone — a weak signal for short messages with no body.
- `conciseness` on a 5–200 character subject is a near-binary hard limit,
  not a graded quality that meaningfully discriminates between outputs.

The rubric architecture from ADR 0027 (analytic per-axis, plausibility-based
type-correctness, LLM judge reserved for semantic dimensions) stands unchanged.
Only the axis list is revised.

## Decision
The judge scores exactly four orthogonal axes:

1. `type_correctness` — is the chosen CC type defensible for this diff?
2. `faithfulness` — is every claim in the message supported by the diff
   (no over-claims, no hallucinations)?
3. `completeness` — does the message represent the primary and all material
   changes shown in the diff (no under-claims)?
4. `specificity` — is the description concrete rather than generic?

`scope_correctness` and `conciseness` are dropped from the axis list.

## Consequences
Cleaner orthogonality: faithfulness covers accuracy, completeness covers
coverage, specificity covers concreteness, type covers label defensibility.
No axis overlaps. Scope quality and message length are not scored semantically;
they can be revisited if a genuine need appears in a later iteration.
