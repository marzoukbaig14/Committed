---
id: 0004
title: Pull the production serving layer into v1
date: 2026-05-29
status: accepted
supersedes: []
superseded_by: []
relates_to: [0002]
tags: [scope, serving]
---

## Context
A deployed Gradio demo alone is too thin to demonstrate production-ML
engineering, which is the headline skill this project is meant to show.

## Decision
Bring a real serving layer into v1: a FastAPI inference endpoint, a Dockerfile,
llama.cpp + GGUF CPU serving, GBNF constrained decoding, and latency/throughput
plus quantization benchmarks. A descope ladder protects shipping under time
pressure: drop the base-model comparison, then the quantization table, then
FastAPI, before ever cutting the core.

## Consequences
Makes production engineering the differentiator rather than an afterthought. Adds
scope and risk, mitigated by the explicit descope order. The core (working
fine-tune, human-validated judge, constrained decoding, deployed demo, README) is
never cut.
