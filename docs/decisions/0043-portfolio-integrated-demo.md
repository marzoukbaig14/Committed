---
id: 0043
title: Add portfolio-integrated web demo served by the FastAPI endpoint
date: 2026-06-13
status: accepted
supersedes: []
superseded_by: []
relates_to: [0004, 0005]
tags: [serving, scope]
---

## Context
`MASTER.md` specifies the v1 demo as a Gradio app on Hugging Face Spaces. The human
has an existing Next.js portfolio deployed on Vercel and wants the Committed demo to
live there as a first-class showcase, matching the portfolio's terminal aesthetic,
rather than as a standalone site. Vercel hosts frontends and short serverless functions;
it cannot hold a ~1.1 GB GGUF model in memory across requests, so the model must run
on a host that keeps it loaded.

## Decision
Two demo surfaces, both v1 deliverables:

1. **Gradio on HF Spaces** (phase one, standalone): the planned Gradio app remains a
   v1 deliverable. Kept **private** until the fine-tuned model is ready; not publicized
   before then.
2. **`/committed` route in the personal Next.js portfolio** (phase two, polished
   surface): calls the FastAPI inference endpoint — already a v1 production-layer item
   (ADR 0004) — hosted on a Hugging Face Docker Space. Neither surface publicized until
   the fine-tune is ready.

**Repo split:** the portfolio repo owns frontend presentation; the Committed repo owns
the serving backend and the HTTP contract (`POST /generate`, `GET /health`). This is
a cross-repo boundary by design.

## Consequences
- The FastAPI endpoint, a production-layer deliverable, is consumed by a real frontend,
  strengthening the production-engineering story.
- CORS configuration is required on the FastAPI side for the portfolio's origins
  (production domain, preview domains, any custom domain).
- The free HF Docker Space sleeps after roughly 48 hours idle; the frontend must handle
  a cold-start wake gracefully.
- A second deployment surface to maintain alongside the Gradio Space.
- Neither surface goes live until the fine-tuned model is ready.
