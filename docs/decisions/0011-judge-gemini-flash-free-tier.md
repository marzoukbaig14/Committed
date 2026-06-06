---
id: 0011
title: Switch the LLM-as-judge from Claude Haiku to Gemini 2.5 Flash (free tier)
date: 2026-05-29
status: accepted
supersedes: [0008]
superseded_by: []
relates_to: [0002]
tags: [eval]
---

## Context
Decision 0008 pinned claude-haiku-4-5 as the LLM-as-judge, which needs a paid
Anthropic API key with credits. The project is built by a student with no budget
to spare, and its own thesis is that it runs end to end on free infrastructure;
the paid judge was the last remaining cost. Google's Gemini API has a free tier
(Gemini 2.5 Flash, no credit card) whose limits (~1,500 requests/day) comfortably
cover a one-time eval of ~1,000 short examples. The judge's credibility comes from
validation against 50 human ratings, which is independent of the model used.

## Decision
Use Gemini 2.5 Flash on the free tier as the LLM-as-judge, via Google's
google-genai SDK and a GEMINI_API_KEY. Pin a specific Flash model identifier for
reproducibility. The eval harness must respect the free-tier rate limits
(throttling plus 429 backoff). This removes anthropic from the v1 judge path.

## Consequences
The entire v1 pipeline, evaluation included, is now free with no credit card,
matching the project thesis exactly (this also updates the note in 0002, which had
said the eval used a paid API). Methodology is unchanged: an LLM-as-judge validated
against human ratings is provider-agnostic. The eval harness gains rate-limit
handling. Free-tier prompts may be used by Google for training, which is acceptable
because the judge only sees public eval data, never private diffs, and the served
product stays local. v2 reasoning-trace generation, also specced on Haiku, will be
revisited to a free provider when v2 begins.