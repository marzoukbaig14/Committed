---
id: 0030
title: Judge reasoning protocol — diff-first, reason-then-label, structured output
date: 2026-06-06
status: accepted
supersedes: []
superseded_by: []
relates_to: [0028, 0029]
tags: [eval, judge]
---

## Context
Without a specified reasoning protocol the judge prompt can produce labels that
are difficult to validate: the model may pattern-match to superficial features,
emit a label before grounding it in the diff, or produce rationale and score in
a format that is hard to parse or audit. A reproducible, structured protocol
reduces these failure modes and makes the judge-vs-human correlation
debuggable.

## Decision
The following protocol applies to every axis judgment:

1. **Diff-first:** the judge characterizes the diff in its own words before
   reading the candidate message. This prevents anchoring on the message when
   forming a view of what the change actually does.
2. **Reason-then-label:** reasoning is emitted before the label, not after.
   The score must follow from the stated reasoning, not precede it.
3. **Structured output:** rationale and label are returned as separate named
   fields (e.g., `reasoning` and `label`), not embedded in prose. This makes
   results parseable without regex heuristics.
4. **Per-example logging:** every judgment (diff, candidate, reasoning, label)
   is logged so the full judge output is auditable and the human-validation
   correlation is computed over a readable record, not a bare aggregate.
5. **No persona instruction:** the prompt does not instruct the model to "act
   as" a senior engineer or any other persona. Persona framing adds noise
   without measurable benefit on structured scoring tasks.
6. **Principle-only anchors:** anchor descriptions state general principles
   without illustrative examples. Concrete examples in the prompt risk the
   judge pattern-matching to surface features of the illustration rather than
   applying the underlying criterion.

## Consequences
Judge output is parseable, auditable, and aligned with the axis structure from
ADR 0028. The per-example reasoning log makes it possible to identify
systematic errors (e.g., the judge consistently misclassifying a specific
commit type) rather than only observing an aggregate correlation number.
`judge_prompt.py` and `run_eval.py` already reflect this protocol.
