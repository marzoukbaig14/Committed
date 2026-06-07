---
id: 0032
title: Composite scoring — faithfulness gate then lexicographic priority, no weights
date: 2026-06-06
status: accepted
supersedes: []
superseded_by: []
relates_to: [0028, 0029, 0031]
tags: [eval, judge]
---

## Context
The four axes (ADR 0028) need a principled composite for two use cases:
(1) a headline pass-rate metric for the README; (2) an optional graded score
for ranking checkpoints. A weighted average was considered and rejected:
weighting permits a high quality score to buy back a correctness failure
(e.g., a hallucinated but well-written message scoring higher than an accurate
but vague one). This violates the correctness-before-quality principle.

## Decision

**Primary metric — conjunctive pass-rate:**
A message passes iff it clears all four axes.
- `faithfulness`: unconditional hard gate. A `fail` fails the message
  regardless of all other axes. Always report faithfulness separately so gate
  failures are visible in the results table.
- `type_correctness`, `completeness`, `specificity`: in lexicographic priority
  order. "Clears completeness" requires `pass`; a `partial` does not clear it.
- A message passes only when `faithfulness=pass`, `type_correctness=pass`,
  `completeness=pass`, and `specificity=pass`.
- Report the per-axis vector alongside the headline pass-rate at all times.

**Optional graded score (checkpoint ranking / A-B comparison only):**
`0` on any faithfulness gate failure; else
`1 + completeness({0, 0.5, 1}) + specificity({0, 1})` → a `[1, 3]` score in
half-steps, restricted to faithful messages. `type_correctness` sits at the
top of the quality tier (not a gate), reflecting that type label ambiguity is
real; promote it to a gate only if Committed drives automated releases where a
wrong type has hard downstream consequences.

**No weighting anywhere.** If composite behavior needs tuning, change which
axes are gated, not relative weights.

## Consequences
Correctness is resolved before quality: no amount of specificity or completeness
can mask a faithfulness failure. The conjunctive pass-rate is the shippable-rate
headline — the fraction of outputs a user could actually commit to a repo. The
graded score is an internal ranking tool only, never the primary metric. Per-axis
vectors are always reported so the pass-rate headline can be interrogated.
