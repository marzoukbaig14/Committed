---
id: 0050
title: Switch the LLM judge to DeepSeek (OpenAI-compatible) after Gemini credits depleted
date: 2026-06-30
status: accepted
supersedes: []
superseded_by: []
relates_to: [0011, 0045, 0049]
tags: [eval, infra, scope]
---

## Context

The v2-i1 0.6B eval (ADR 0049) judges candidate commit messages with the Gemini 2.5
Flash LLM-judge (ADR 0011). Mid-run, the Gemini API began returning
`429 RESOURCE_EXHAUSTED: "Your prepayment credits are depleted."` — a billing-balance
failure, not a rate limit. The harness mislabeled it as a daily-quota cap, which cost a
wrong diagnosis. At that point the 0.6B fine-tune arm was fully judged (442/442) but the
0.6B baseline arm had only 35/442.

The Gemini API bills on a prepaid model with a ~$10 minimum top-up and no
pay-exactly-for-use option. The project has no budget for another $10 block. DeepSeek's
API is OpenAI-compatible, pay-as-you-go with no enforced minimum, and roughly 10-50x
cheaper per token (`deepseek-chat`: ~$0.07/$0.27 per MTok cached/uncached input, ~$1.10
per MTok output, vs Gemini Flash's $0.30/$2.50). Re-judging the entire eval on DeepSeek
costs well under $1.

This is a real-world budget constraint overriding the judge-continuity premise of
ADR 0045/0049. It was decided with the human, who accepts the comparability cost.

## Decision

Add a DeepSeek judge backend and make it the judge for the v2-i1 eval.

- New module `src/committed/eval/judge_deepseek.py` (model `deepseek-chat`), mirroring
  `judge_gemini.py`: identical `judge_records` contract, identical JSONL log format,
  identical four-axis `JudgeResult` schema. Only the API call changes.
- The rubric and protocol (`judge_prompt.py`: `JUDGE_SYSTEM` + `build_judge_user`) are
  imported **unchanged**. DeepSeek's `json_object` mode guarantees valid JSON but not a
  schema, so the backend appends a JSON-format envelope (plumbing, not rubric) and
  validates the response into `JudgeResult`, retrying malformed shapes.
- `run_eval.py` gains `--backend deepseek` (additive). The 442-row strata sample, the
  canonical prompt, the GBNF grammar, the deterministic metrics, and the gate-then-grade
  composite with deployment reweighting are all unchanged.
- For an internally consistent comparison under a single judge, **all four arms are
  re-judged on DeepSeek**: 0.6B baseline + 0.6B fine-tune, and the recorded v1 1.7B
  baseline + 1.7B fine-tune (whose candidate files are already in-repo). v1's training and
  generation are NOT re-run (ADR 0049 hold); only the judging is redone.
- The DeepSeek judge is validated against `human_ratings_50.jsonl` (agreement + Cohen's
  kappa per axis), the same check that justified the Gemini judge, so the new judge's
  trust is documented rather than assumed.

## Consequences

- **Easier:** the eval can finish within a tiny budget, pay-per-use, no minimum block.
- **Harder / the cost:** this breaks byte-for-byte comparability with v1's *published*
  Gemini-judged numbers. A different judge model can shift absolute pass-rates, so the
  Gemini numbers in `analysis/results/{baseline,finetune}_report.json` and
  `docs/eval/FINDINGS_v1.md` become a **superseded reference** for this comparison; the
  DeepSeek-judged 1.7B numbers replace them. Only same-judge deltas (0.6B vs 1.7B, both
  DeepSeek-judged) are valid going forward.
- This is explicitly **not** the apples-to-apples judge continuity ADR 0045/0049 intended
  — it is the pragmatic ground truth given the depleted budget, accepted knowingly.
- **Mitigation of the comparability hit:** rubric/protocol/sample/metrics are all frozen,
  so only the judge model varies; and the human-validation re-run quantifies how closely
  the DeepSeek judge tracks the human labels (and, by extension, the Gemini judge).
- **Infra:** requires `DEEPSEEK_API_KEY` in the environment and `api.deepseek.com` on the
  network allowlist; adds an `openai` SDK dependency for the eval path.
- **Revisit:** if Gemini budget is restored later, the eval could be re-confirmed on
  Gemini; the Gemini backend remains in place and unchanged.
