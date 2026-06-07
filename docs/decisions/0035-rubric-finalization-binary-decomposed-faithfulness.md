---
id: 0035
title: Finalize judge rubric — all axes binary, faithfulness decomposed into atomic per-claim checks
date: 2026-06-07
status: accepted
supersedes: [0029, 0031]
superseded_by: []
relates_to: [0028, 0030, 0032, 0034]
tags: [eval, judge]
---

## Supersession
- Supersedes **0029** (per-axis scoring scales): all four axes are now binary `pass|fail`;
  the "mixed by judgment shape" 3-level completeness scale is retired.
- Supersedes **0031** (per-axis anchor definitions) for the `completeness` and `faithfulness`
  axes only; `type_correctness` and `specificity` anchors carry over unchanged.
- Builds on 0028 (four-axis set), 0030 (reasoning protocol), 0032 (gate-then-grade composite),
  0034 (backend-swappable, Gemini default) — all unchanged.

## Context
The four-axis rubric (ADRs 0028–0034) used mixed scales — three binary, one 3-level
(`completeness`: fail/partial/complete) — and judged each axis holistically. A 12-example
sanity-set validation run surfaced two problems:

**Completeness (3-level) was both noisy and over-strict.** It flapped on the
`partial`↔`complete` boundary run-to-run, penalised messages for omitting supporting
detail (imports, internal mechanics of a change already named) that is not a materially
distinct change, and double-counted vagueness already charged to `specificity`.

**Faithfulness wobbled on genuinely ambiguous cases.** Judged holistically, it flipped
`fail`↔`pass` run-to-run on a borderline mischaracterisation (a "fix day calculation"
message for a year-interpretation diff) even at a fixed prompt. This is the documented
non-determinism of LLM-as-judge on borderline cases, concentrated on the implicit
conjunction-of-claims structure that a holistic judgment leaves unexamined.

`faithfulness` is the hard gate in the composite (ADR 0032) and the most important
axis — a message that misstates what the diff does is the worst failure mode. Dropping it
was considered and rejected: it would remove the most important signal without making
the eval deterministic.

## Decision

1. **All four axes are binary `pass | fail`.** Completeness collapses from 3-level to
   binary. The graded composite formula simplifies to
   `1 + completeness{0,1} + specificity{0,1}` (integer 1–3). Judge-vs-human agreement
   uses plain Cohen's κ on all four axes; no ordinal weighted-κ special case.

2. **Completeness — binary, coverage-only, with two clarifications:**
   - Supporting detail (imports, internal mechanics of a named change, refactor plumbing)
     is not a materially distinct change; its omission does not fail completeness.
   - Vagueness is charged to `specificity`, not `completeness`; a message that names the
     single change but names it vaguely still passes completeness.

3. **Faithfulness — operationalized as decomposed, atomic, per-claim precision:**
   The judge (a) characterises the diff in its own words first (per ADR 0030), (b) breaks
   the candidate message into its atomic claims, (c) tags each as a *what-changed* claim
   (must be supported by the diff) or a *rationale* claim (passes unless the diff
   contradicts it), (d) verifies each claim individually, and (e) passes iff every claim
   clears (conjunction). Decomposition is over the message's claims (precision), not over
   the diff's changes (that is `completeness`).

4. **Deliberate deviation from the textbook definition, recorded as intentional:**
   Standard faithfulness treats extrinsic-unverifiable content as unfaithful by default;
   this rubric penalises only intrinsic hallucination (a claim the diff contradicts) and
   lets an unprovable-but-not-contradicted rationale pass, because a commit message's
   "why" legitimately is not derivable from the diff.

5. **Decomposition applied to `faithfulness` only.** `type_correctness` is a single atomic
   decision; `completeness` is already a coverage check and is stable; `specificity` is
   holistic by nature. None meets the "conjunction-of-sub-items AND currently wobbling"
   bar; decomposition adds cost and its own variance where it is not needed.

6. **Self-consistency via majority-vote over 3 samples** is intended for `faithfulness`
   (and optionally all axes) on the final eval run (~3× judge cost, well under the $10
   ceiling). A **run-to-run stability number** (e.g. Krippendorff's α, or % agreement on a
   re-judged subset) is reported alongside the judge-vs-human agreement number.

## Consequences
- Output label stays binary on all axes; no schema change to `judge_gemini.py` / `judge.py`
  beyond the prompt update. Per-claim reasoning is visible in the logged rationale.
- Composite formula changes: `1 + completeness{0,1} + specificity{0,1}` (was
  `1 + completeness{0,0.5,1} + specificity{0,1}`); range stays [1–3].
- More auditable: a faithfulness failure names the specific failing claim.
- `docs/eval/judge_rubric.md` must be synced to `judge_prompt.py` — still owed as
  implementation work.
- Judge model in use: `gemini-2.5-flash` (validated on the 12-example sanity set;
  ~$1.10 per 500-sample run).

## Alternatives considered
- **Drop faithfulness** — rejected; most important axis; dropping it doesn't improve
  determinism.
- **Keep completeness 3-level** — rejected; `partial` bucket was the main source of
  flap and over-strictness; binary is the field's recommendation for reliability.
- **Decompose all axes** — rejected; only faithfulness met the threshold; blanket
  decomposition adds cost and decomposition-method variance unnecessarily.

## References
- Maynez, Narayan, Bohnet, McDonald (2020), *On Faithfulness and Factuality in
  Abstractive Summarization* (ACL) — intrinsic vs. extrinsic hallucination.
- Min et al. (2023), *FActScore* — atomic-claim decomposition + per-claim verification.
- LLM-as-a-judge reliability literature — binary/extreme outputs, aggregation over samples,
  and reporting human-alignment + stability together.
- CMG eval (Zeng et al. 2026; Li et al.) — reference-free multi-dimensional LLM-judge
  eval is current practice for commit-message generation.
