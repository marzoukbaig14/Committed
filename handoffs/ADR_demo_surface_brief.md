# Decision brief for the log agent: portfolio-integrated demo surface

This is the source content for one ADR. Hand it to the decision-log agent, which will assign the next ID (after `ls docs/decisions/` to confirm the live max), echo the id and decision statement for your `CONFIRM <id>`, write the record, regenerate the log and tree, and update `MASTER.md`. The decision is yours; review and adjust before confirming.

## Title
Add a portfolio-integrated web demo served by the FastAPI endpoint, alongside the Gradio Space

## Status
Accepted. Additive — supersedes nothing.

## Context
- `MASTER.md` specifies the v1 demo as a Gradio app on Hugging Face Spaces.
- The human has an existing Next.js portfolio deployed on Vercel and wants the Committed demo to live there as a first-class showcase, matching the portfolio's terminal aesthetic, rather than as a standalone site.
- Vercel hosts frontends and short serverless functions; it cannot hold a ~1.1 GB model in memory across requests, so the model must run on a host that keeps it loaded. Hugging Face Spaces (free CPU tier) does, and the project is already HF-centric.

## Decision
1. Keep the planned Gradio-on-HF-Spaces demo as the standalone demo (phase one). It remains a v1 deliverable. Set to private until the fine-tune is ready.
2. Add a dedicated `/committed` route in the personal Next.js portfolio (separate repo) as the polished surface (phase two). It calls the FastAPI inference endpoint — already in the v1 production layer — hosted on a Hugging Face Docker Space.
3. Repo split: the portfolio repo owns the frontend presentation; the Committed repo owns the serving backend and the HTTP contract (`POST /generate`, `GET /health`).
4. Neither surface is publicized — no production link or merge, Gradio Space private — until the fine-tuned model is ready.

## Alternatives considered
- Gradio-only on Spaces (the original plan): simplest, but reads as an ML demo rather than a product and does not exercise the FastAPI layer through a real frontend.
- A standalone custom site on Vercel: cleaner separation but an orphan surface; integrating into the portfolio makes Committed a first-class project there.
- Hosting the model on Vercel: not viable — serverless functions cannot keep the model loaded, and free-tier function timeouts are far too short for CPU inference.

## Consequences
- A cross-repo boundary: presentation in the portfolio repo, serving in the Committed repo, meeting at the HTTP contract.
- CORS configuration on the FastAPI side for the portfolio origins (production domain, any custom domain, Vercel preview domains).
- A second deployment surface to maintain.
- The FastAPI endpoint, a production-layer deliverable, is now consumed by a real frontend, which strengthens the production-engineering story.
- The free HF Space sleeps after roughly 48 hours idle, so the frontend must handle a cold-start wake.

## Affected documents
- `MASTER.md`: extend the Demo section to record the second surface and the repo split; add a note in the Serving Plan that the FastAPI endpoint is consumed by the portfolio page.
