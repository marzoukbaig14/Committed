---
id: 0031
title: Per-axis anchor definitions for all four judge axes
date: 2026-06-06
status: accepted
supersedes: []
superseded_by: []
relates_to: [0028, 0029, 0030]
tags: [eval, judge]
---

## Context
The four axes (ADR 0028) and their scales (ADR 0029) require concrete anchor
definitions — the pass/fail criteria and reasoning steps the judge applies per
axis. Without anchors, scores are under-specified and judge-vs-human alignment
cannot be meaningfully interpreted.

## Decision
The canonical anchor definitions for all four axes are the source of record in
`docs/eval/judge_rubric.md`. The orthogonality boundaries logged here are the
ones that matter for cross-axis consistency:

- **`type_correctness`:** is the CC type label defensible given the diff?
  (plausibility, not exact-match against the dataset gold label — see ADR 0027).
- **`faithfulness`:** does every claim in the message have support in the diff?
  Faithfulness catches over-claims and hallucinations. It does not evaluate
  coverage (missing changes are completeness, not faithfulness failures).
- **`completeness`:** does the message represent the primary change and all
  material secondary changes visible in the diff? Completeness catches under-
  claims and omissions. It does not evaluate whether stated claims are accurate
  (accuracy is faithfulness, not completeness).
- **`specificity`:** is the description concrete and diff-grounded rather than
  generic? A message that would apply unchanged to dozens of different diffs
  fails specificity regardless of its accuracy or completeness.

The faithfulness / completeness boundary is the one most likely to confuse:
faithfulness = accuracy / over-claims; completeness = coverage / under-claims.

## Consequences
Anchors are versioned alongside the rubric artifact. Any future revision to
anchor wording that changes scoring behavior is a new ADR (superseding this
one), not an in-place edit of `judge_rubric.md`. The orthogonality boundaries
above are the authoritative summary for agents reading this record without
opening the full rubric.
