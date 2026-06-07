---
id: 0027
title: Adopt analytic per-axis LLM rubric with plausibility-based type-correctness
date: 2026-06-06
status: accepted
supersedes: []
superseded_by: []
relates_to: [0011]
tags: [eval, judge]
---

## Context
The eval requires a semantic quality metric beyond the three deterministic ones
(BLEU, ROUGE-L, prefix-classification accuracy). Two rubric designs were
considered for the Gemini 2.5 Flash judge (ADR 0011):

- **Option 1 — holistic:** A single overall quality score. Simple to prompt and
  aggregate but opaque: a mediocre type with a great description and a great type
  with a vague description score the same.
- **Option 2 — analytic:** Score four quality dimensions separately
  (type-correctness, specificity, scope-correctness, conciseness) and combine
  into a composite.

For type-correctness specifically, exact-match against the dataset's "gold" label
was considered and rejected. Real commits have genuine type ambiguity: a commit
that refactors error handling could defensibly be `fix`, `refactor`, or `chore`.
Penalising the model for choosing a different-but-valid type would produce a
misleading metric and largely duplicate the deterministic prefix-accuracy signal.

## Decision
Use the analytic, per-axis rubric (Option 2):

1. Score the four dimensions separately: type-correctness, specificity,
   scope-correctness, conciseness.
2. Score type-correctness on **plausibility** — is the chosen type defensible for
   this diff? — not exact-match against the gold label.
3. Reserve LLM-judge calls for the irreducibly semantic dimensions; all
   objective checks (BLEU, ROUGE-L, prefix-accuracy) stay in `metrics.py` in
   code, not the prompt.

The composite weighting of the four scores into a single headline number is a
separate decision to author once anchor descriptions are validated.

## Consequences
Each judge call returns interpretable per-dimension sub-scores, making it
possible to diagnose where a model fails (wrong type vs. vague description vs.
wrong scope vs. verbose). The architecture is already reflected in `metrics.py`
and `judge_prompt.py`. Remaining core work to author: anchor descriptions per
score level, category definitions, composite weights, and final judge-prompt
wording.
