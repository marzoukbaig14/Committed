---
id: 0037
title: Deployment-reweighted headline metrics
date: 2026-06-11
status: accepted
supersedes: []
superseded_by: []
relates_to: [0025, 0026, 0032]
tags: [eval, metrics]
---

## Context
The judge set is a 442-row equal-allocation strata sample (ADR 0026 stratification). Equal
allocation flattens the commit-type distribution so that every type contributes roughly equally
to sample-level numbers. The real test split is ~49% `fix`; the equal-allocation sample is
~11% `fix`. This causes a collision: the sample-level always-`fix` floor reads ~11% and a
feat-collapsed model also reads ~11% prefix accuracy, falsely implying the model matches the
trivial baseline. The deployment story is the opposite — the real always-`fix` floor is ~49%.

## Decision
Report the headline metrics (prefix-type accuracy, conjunctive pass-rate, graded mean,
always-fix floor) reweighted to the true test-split type distribution, by recombining per-type
metrics measured on the equal-allocation sample. Weights are derived from the full reference
split at eval time (type counts → frequencies). The deployment-reweighted numbers are the
primary headline. Sample-level numbers are retained in the report as diagnostics.

Implementation: `compute_deployment()` in `src/committed/eval/run_eval.py` performs the
recombination. No extra judge calls; deterministic post-processing only.

## Consequences
The headline reflects deployment behavior (~13% reweighted prefix accuracy vs ~49%
always-fix floor — model is ~3.7× worse than always-fix). Before/after (baseline vs
fine-tuned) comparisons remain valid because both sides apply the same reweighting. The
sample-level diagnostics in the report remain useful for per-type reliability checks.
