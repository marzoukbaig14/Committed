# Findings — v2-i1: Qwen3-0.6B controlled comparison

**What this is.** v2 iteration 1 (ADR 0049) re-runs the v1 fine-tune + eval pipeline with
**exactly one variable changed — the base model, Qwen3-1.7B → Qwen3-0.6B.** Recipe, dataset,
grammar, prompt, 442-row strata sample, eval harness, and composite are all frozen, so any
before/after difference is attributable to base-model capacity.

**Judge.** The judge was switched from Gemini 2.5 Flash to **DeepSeek `deepseek-chat`** (ADR 0050)
after the Gemini prepaid balance was depleted mid-run. To keep the comparison internally
consistent, **all four arms were re-judged on DeepSeek** — 0.6B baseline + fine-tune and the v1
1.7B baseline + fine-tune (their candidate generations were reused unchanged; v1 training/generation
was not re-run). The v1 *Gemini-judged* numbers in `analysis/results/*_report.json` are therefore a
**superseded reference**; every number below is DeepSeek-judged. Total judge cost: ~$1.2 (est.),
0 examples skipped, 442/442 each arm.

All metrics are deployment-reweighted to the true test-split type distribution (ADR 0037) unless
noted; the four axes are reported as pass-rates. The always-`fix` floor is **0.489**.

## Judge reliability (DeepSeek vs. human, n=50, on the 1.7B baseline candidates)

The same 50 human ratings that validated the v1 Gemini judge were applied to the DeepSeek judge on
the identical candidates. The DeepSeek judge agrees with the human **at least as well as Gemini did
on every axis**:

| axis | DeepSeek agree / κ | (v1 Gemini κ) |
|---|---|---|
| type_correctness | 0.82 / **0.61** | 0.38 |
| faithfulness | 0.78 / **0.56** | 0.38 |
| completeness | 0.80 / **0.60** | 0.54 |
| specificity | 0.88 / **0.34** | 0.25 |

Three axes show moderate-to-substantial agreement (κ ≈ 0.56–0.61). **Specificity is the
weakest-agreement axis** (κ 0.34) — as it also was for Gemini — so specificity-driven differences
below carry the most judge uncertainty.

## Table 1 — 0.6B: baseline → fine-tune (the rescue)

| metric | 0.6B baseline | 0.6B fine-tune | lift |
|---|---|---|---|
| prefix-type accuracy | 0.154 | **0.601** | +0.447 |
| type_correctness pass | 0.296 | **0.726** | +0.430 |
| faithfulness pass | 0.285 | 0.810 | +0.525 |
| completeness pass | 0.353 | 0.729 | +0.376 |
| specificity pass | 0.414 | 0.545 | +0.131 |
| conjunctive (all-4) pass | 0.101 | 0.359 | +0.258 |
| graded mean (0–3) | 0.777 | 2.094 | +1.317 |
| BLEU / ROUGE-L | 0.86 / 0.121 | 8.42 / 0.278 | — |

**Type distribution (raw generations):** the 0.6B baseline emits `feat:` for **86.7%** of commits
(4 distinct types ever used) — classic feat-collapse, and its prefix accuracy (0.154) sits *below*
the always-`fix` floor (0.489), i.e. worse than a trivial constant guess. The fine-tune drops `feat`
to **9.7%** across 9 types, with `fix` at 50% (matching the real-world distribution), lifting prefix
accuracy to 0.601 — well above the floor.

## Table 2 — 0.6B vs 1.7B (all DeepSeek-judged)

| metric | 0.6B base | 1.7B base | 0.6B ft | 1.7B ft | ft gap (1.7B − 0.6B) |
|---|---|---|---|---|---|
| prefix-type accuracy | 0.154 | 0.131 | 0.601 | 0.637 | +0.036 |
| type_correctness | 0.296 | 0.296 | 0.726 | 0.778 | +0.052 |
| faithfulness | 0.285 | 0.491 | 0.810 | 0.848 | +0.038 |
| completeness | 0.353 | 0.543 | 0.729 | 0.776 | +0.047 |
| specificity | 0.414 | 0.814 | 0.545 | 0.667 | **+0.122** |
| conjunctive (all-4) | 0.101 | 0.175 | 0.359 | 0.471 | **+0.112** |
| graded mean (0–3) | 0.777 | 1.447 | 2.094 | 2.139 | +0.045 |
| BLEU / ROUGE-L | 0.86 / .12 | 2.17 / .16 | 8.42 / .28 | 11.79 / .31 | — |

## The headline questions, answered

**1. Did the same fine-tune rescue feat-collapse at 0.6B?** **Yes, decisively.** Both bases
feat-collapse and score an identical type_correctness of 0.296; the 0.6B base is actually *marginally
less* collapsed than the 1.7B base by raw feat-share (86.7% vs 95.5%), so lower capacity did not make
the collapse worse. The fine-tune lifts 0.6B type_correctness to 0.726 and prefix accuracy from below
the floor (0.154) to 0.601. The rescue is real and large.

**2. How close did 0.6B land to 1.7B?** **Very close on most axes, with the gap concentrated in
specificity.** The 0.6B fine-tune is within ~4–5 points of the 1.7B fine-tune on prefix accuracy
(0.601 vs 0.637), type (0.726 vs 0.778), faithfulness (0.810 vs 0.848), completeness (0.729 vs
0.776), and the graded mean is nearly identical (2.094 vs 2.139). The capacity cost shows up almost
entirely in **specificity** (0.545 vs 0.667, −0.122): the 0.6B fine-tune picks the right type and
states accurate, complete facts, but its messages are **vaguer** — they name the concrete
mechanism less often. Because the conjunctive metric requires all four axes to pass, that specificity
shortfall is what drives most of the conjunctive gap (0.359 vs 0.471). The lower BLEU/ROUGE-L (8.4 vs
11.8) is consistent: 0.6B writes less reference-like, less specific text.

**Verdict (ADR 0049).** For Conventional-Commit *typing and faithfulness*, the recipe transfers to
0.6B almost fully — a strong "you may not need 1.7B for this" result at ~⅓ the parameters. The honest
caveat is **message concreteness**: 0.6B trades a meaningful amount of specificity for its smaller
size, and that is the axis with the lowest judge–human agreement, so it should be read with that
uncertainty. Whether to ship 0.6B as the serving default is a separate, downstream decision (its own
ADR), not settled here.

**Caveats.** (a) Judge switched to DeepSeek (ADR 0050) — comparable to or better than Gemini on
human agreement, but absolute numbers are not comparable to v1's published Gemini figures; only the
all-DeepSeek deltas here are valid. (b) Specificity has the weakest human agreement (κ 0.34). (c) The
strata sample is equal-allocation; headline numbers are deployment-reweighted (ADR 0037).
