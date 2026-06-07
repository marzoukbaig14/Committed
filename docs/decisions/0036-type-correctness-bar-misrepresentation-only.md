---
id: 0036
title: Tighten type-correctness bar — only misrepresentation fails
date: 2026-06-07
status: accepted
supersedes: []
superseded_by: []
relates_to: [0028, 0035]
tags: [eval, judge]
---

## Context
ADR 0028 established `type_correctness` as a binary axis scored on plausibility
(is the chosen CC type defensible for this diff? — not exact-match). ADR 0035
superseded the completeness and faithfulness anchors of ADR 0031 but did not
state an explicit anchor for `type_correctness`, leaving the bar as "defensible"
without a pass/fail boundary.

On the 12-example sanity set, "defensible" proved under-specified: the judge
occasionally penalised `refactor` vs `chore` or `fix` vs `perf` choices where
either type was reasonable, producing type-correctness failures that did not
reflect a real error in the commit message.

## Decision
The `type_correctness` axis passes unless the chosen type is a **misrepresentation**
of the diff. A type misrepresents the diff in exactly two cases:

1. **Wrong category:** the type names an activity the diff does not perform
   (e.g. `feat` for a diff that only removes code, or `fix` for a purely
   organisational refactor with no corrected behaviour).
2. **Suppressed consequence:** the correct type carries a downstream expectation
   (e.g. `feat` signals a semver minor bump, `fix` signals a patch) and the
   chosen type suppresses that signal in a way that would mislead a reader
   acting on the label.

A type that a reviewer would merely *prefer* — but that is defensible given the
diff — passes. The axis measures labelling accuracy, not labelling optimality.

## Consequences
Fewer false-positive type failures; tighter alignment between the plausibility
criterion (ADR 0028) and the anchor wording the judge applies. The binary
pass/fail structure of 0035 is unchanged; only the pass/fail boundary for
`type_correctness` is now precisely stated. `judge_prompt.py` anchor wording
for this axis must reflect the two-case misrepresentation test.
