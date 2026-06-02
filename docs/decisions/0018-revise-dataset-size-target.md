---
id: 0018
title: Revise the dataset-size target from 30-50k to ~20-30k
date: 2026-06-02
status: accepted
supersedes: []
superseded_by: []
relates_to: [0017]
tags: [data, scope]
---

## Context
The data plan assumed a 30-50k-pair target. A full-scale scan (1,000,000 commits)
measured the relaxed Conventional Commits match rate on Python single-file commits
at ~3.1%. The earlier 1.2% estimate came from a biased, contiguous 80k sample
dominated by a few low-adoption repos. Python single-file commits are ~9.4% of all
commits.

## Decision
Revise the target from 30-50k to ~20-30k raw matches, projecting to ~15-25k usable
pairs after the structural filters (message length, dropped bot/merge/revert
commits, and the diff token cap). The exact figure is finalized after the full
build pass.

## Consequences
v1 can ship on mined CC data alone, with no synthetic harvesting required. ~15-25k
is adequate for a narrow QLoRA fine-tune, and the smaller figure is reported
honestly per project norms. MASTER's Goals, Data Plan, and Open Questions are
updated to reflect the revised target.
