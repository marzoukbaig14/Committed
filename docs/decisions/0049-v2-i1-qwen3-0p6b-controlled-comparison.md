---
id: 0049
title: "v2 iteration 1 scope: Qwen3-0.6B controlled comparison"
date: 2026-06-26
status: accepted
supersedes: []
superseded_by: []
relates_to: [0045, 0011, 0003]
tags: [model, scope, eval]
---

## Context
v1 shipped: the QLoRA fine-tune of Qwen3-1.7B beat the zero-shot baseline on every axis
except specificity (deployment-reweighted type accuracy 0.131 → 0.637, conjunctive
pass-rate 0.181 → 0.471, faithfulness 0.43 → 0.86). The project thesis is a small, local,
CPU-served model; the next question is how far "small" can go. ADR 0003 already named
Qwen/Qwen3-0.6B as the in-family smaller option, and the README/MASTER v2 list leads with
it: can the same recipe rescue feat-collapse at 0.6B, and how close to the 1.7B numbers
does it land?

A comparison is only interpretable if the two runs differ in exactly one variable. ADR 0045
froze the fine-tune eval protocol to "hold everything constant but the weights" for the v1
before/after. v2-i1 needs the same discipline, widened by one notch: hold everything constant
but the base model.

## Decision
v2 iteration 1 re-runs the v1 fine-tune and eval pipeline changing exactly one variable: the
base model, **Qwen3-1.7B → Qwen3-0.6B**. Held constant:

- **Training recipe** — LoRA rank 16, alpha 32, lr 2e-4, sequence length, epochs, and batch
  size as the held v1 defaults (`configs/qwen3-1.7b-lora-r16.yaml`).
- **Training dataset** — `marzoukbaig14/committed-train`, reused unchanged. Qwen3-0.6B and
  Qwen3-1.7B share a tokenizer, so the token-cap filtering is identical and the data is **NOT**
  rebuilt.
- **Grammar** — the same GBNF grammar.
- **Prompt** — the same canonical zero-shot prompt (ADR 0040).
- **Eval harness** — the same harness and the same 442-row equal-allocation strata sample.
- **Judge** — the same Gemini 2.5 Flash backend (ADR 0011).

This extends ADR 0045 from "only the weights differ" to "only the base model differs," so the
0.6B-vs-1.7B delta is attributable to model capacity and nothing else.

**Pre-committed reading of the result:** if Qwen3-0.6B lands materially worse than 1.7B under
the identical recipe, that is a valid result — a capacity or recipe-transfer limit, not a
failure to report — and any recipe change (a different rank, lr, or data rebalance to chase
the gap) is deferred to v2-i2 rather than folded into this comparison.

## Consequences
- A clean apples-to-apples capacity comparison: the headline question (does the same fine-tune
  rescue feat-collapse at 0.6B, and how close to type 0.637 / conjunctive 0.471 does it reach)
  is answerable from one controlled run.
- Reusing the dataset and harness unchanged keeps v2-i1 cheap and keeps it comparable to the
  v1 baseline that ADR 0045 protects; resampling the strata or rebuilding the data would break
  that comparability and would need its own ADR.
- The v1 base-model artifacts (Qwen3-1.7B references in configs, scripts, engine defaults,
  serving) are the swap surface a v2-i1 implementer changes for the 0.6B run; that code work
  is out of scope for this scope-setting record.
- Holding the recipe fixed means a worse 0.6B result does not get "fixed" inside this iteration;
  it is recorded as the capacity finding and the recipe search moves to v2-i2.
