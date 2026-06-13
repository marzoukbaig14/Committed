---
id: 0040
title: Zero-shot canonical prompt and near-raw diff format across all phases
date: 2026-06-11
status: accepted
supersedes: []
superseded_by: []
relates_to: [0003, 0039]
tags: [eval, training, serving]
---

## Context
The baseline, the training data, and fine-tuned inference all need a prompt. Three
constraints tie them together: a fine-tune is conditioned on the exact prompt it
was trained under, so in-context exemplars at inference are redundant and can fight
the learned mapping; the baseline must use the identical prompt shape so the
before/after delta is attributable to fine-tuning rather than a prompt difference;
and the diff serialization seen at training must match the one seen at inference.

## Decision
One canonical, **zero-shot** prompt is used verbatim at baseline inference, wrapped
around every training example, and at fine-tuned inference. Source of truth:
`src/committed/inference/prompt.py`.

- **System instruction** carries only what the grammar cannot: the type choice
  (one-line definition per type) and four content rules that map 1:1 to the judge
  axes — imperative mood, state only what the diff shows (no invented rationale),
  name the most significant change, be specific. Format is delegated entirely to
  the grammar (ADR 0039).
- **Diff format** is near-raw: `Diff:\n{diff}`. This exact serialization must also
  be used when formatting training examples.
- **Zero in-context examples.**
- **Thinking suppression:** Qwen3 emits a reasoning trace that otherwise leaks into
  the constrained line. It is suppressed by rendering the chat template with
  `enable_thinking=False` through the Qwen tokenizer (`generate.py`); a `/no_think`
  tag on the final user turn and `<think>`/`</think>` stop tokens are backstops.

## Consequences
The before/after comparison isolates fine-tuning. The same prompt module is the
single point of truth for training-time and inference-time formatting, so the two
cannot drift. Observed baseline failure modes this prompt + grammar setup surfaced,
which motivate the fine-tune: **feat-collapse** (~95.5% of baseline predictions are
`feat`), **junk/hallucinated scopes**, and **thinking-mode leakage** (now mitigated
at the template level). Any future change to the prompt wording or diff format is a
new ADR, because it invalidates comparability with prior runs and requires retraining.
