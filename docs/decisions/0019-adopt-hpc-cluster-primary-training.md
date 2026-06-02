---
id: 0019
title: Adopt the HPC cluster as primary training compute, keeping the v1 core free-tier reproducible
date: 2026-06-02
status: accepted
supersedes: []
superseded_by: []
relates_to: [0003]
tags: [infra, scope]
---

## Context
MASTER's training plan listed Colab T4 (free, 16 GB) as the primary training box, with
the Northeastern HPC cluster reserved "for larger runs." The cluster is in fact
available, with many GPUs and ~1 TB of storage. This removes the compute and memory
ceilings that shaped several v1 choices — notably the diff token cap and the training
sequence length, both sized to fit a T4. A tension to manage: the project's thesis is
that the pipeline is built on *free* infrastructure, and an institutional cluster is
not free for an outside reader to reproduce.

## Decision
Adopt the HPC cluster as the primary training environment for the main fine-tune and
for the compute-heavy work (the stretch base-model comparison and LoRA rank ablation,
and later v2). Demote Colab T4 / Kaggle to a fallback. Crucially, keep the v1 *core*
fine-tune demonstrably runnable on a free T4: a QLoRA of a 1.7B model on a ~15-25k
dataset fits free infrastructure, so the "built on free infrastructure" claim is
preserved. The cluster is used for speed and for the heavier experiments, not as a
requirement for the core result.

## Consequences
- The diff token cap and training sequence length are no longer compute-bound; they are
  set by data quality and CPU serving latency instead (cap raised accordingly).
- The v1 stretch goals (base-model comparison, LoRA rank ablation) are materially
  de-risked.
- v2 reasoning-trace generation can run an open model on the cluster, partially
  satisfying the v2 compute trigger without an API budget.
- Unchanged on purpose: the base model stays Qwen3-1.7B (the thesis is a small, local
  model; cluster access is not a reason to scale the base up — that remains a separate
  v3 question); serving stays CPU/free; and the Hugging Face Hub remains the source of
  truth for all artifacts (the cluster's 1 TB local storage is convenience, not a
  substitute for Hub-as-registry portability).
- The README must state honestly that the core pipeline is free-tier reproducible and
  the cluster was used to accelerate training and to run the ablations.

Affects MASTER: Tech Stack (training-hardware line), Training Plan (Hardware), and a
note in the Thesis / README story that the core remains free-infrastructure reproducible.
