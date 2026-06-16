# Committed — Post-Fine-Tune Eval Findings (v1, iteration 1)

> ## ⚠️ Reading these numbers: gold is not the standard
> The training and eval data are **real, not synthetic** — CommitChronicle commit
> messages written by developers in the wild. They contain real labeling mistakes:
> a heavy `feat` bias, prefixes that contradict their own description text, and
> housekeeping commits mislabeled as features. **We do not want a model that
> memorizes and reproduces these mistakes.** The goal is a model that generalizes
> to *correct, defensible, reasonable* commit messages — so exact-match against gold
> is explicitly NOT the metric. Type correctness is scored on **plausibility against
> the diff** (ADR 0036), not agreement with gold. Every number below is read in that
> light: a disagreement with gold is sometimes the model being *right* and sometimes
> the model being *wrong*, and the two are kept separate, never merged. A future
> iteration should supplement with synthetic examples and/or filter the training set
> down to only those pairs whose gold type is defensible against the diff — i.e.
> train on correct behavior, not on noise.

_Before/after: zero-shot Qwen3-1.7B baseline vs. the 2-epoch QLoRA fine-tune, on the
same 442-row equal-allocation strata sample, through the same Gemini 2.5 Flash judge
and the same frozen rubric (ADR 0035/0036). Only the model weights differ between the
two columns. Headline numbers are deployment-reweighted to the true test-split type
distribution (ADR 0037)._

## 1. Before / after

| Metric | Baseline (zero-shot) | Fine-tune | Δ |
|---|---|---|---|
| Prefix-type accuracy (deployment-reweighted) | 0.131 | 0.637 | +0.506 |
| — always-`fix` floor (same for both) | 0.489 | 0.489 | — |
| Conjunctive pass-rate (all 4 axes) | 0.181 | 0.471 | +0.290 |
| Graded mean (0–3) | 1.207 | 2.188 | +0.981 |
| type_correctness | 0.33 | 0.81 | +0.48 |
| faithfulness | 0.43 | 0.86 | +0.43 |
| completeness | 0.52 | 0.73 | +0.21 |
| specificity | 0.81 | 0.71 | −0.10 |
| BLEU (diagnostic, short-text caveat) | 2.17 | 11.79 | +9.62 |
| ROUGE-L F (diagnostic) | 0.156 | 0.305 | +0.149 |

Source: `analysis/results/baseline_report.md`, `analysis/results/finetune_report.md`.

## 2. Headline read

The fine-tune crossed the line that matters most. The baseline's deployment-reweighted
type accuracy (0.131) was roughly 3.7x *worse* than the trivial always-`fix` floor
(0.489) — a model that, left to itself, collapsed to `feat` on ~95% of diffs and was
worse than guessing. The fine-tune (0.637) is now clearly *above* that floor: it went
from worse-than-trivial to genuinely useful at type selection. Faithfulness — the hard
gate, where a single failure disqualifies a message — nearly doubled (0.43 → 0.86).
Every judged axis improved except specificity.

The single most important way to describe what happened: the failure mode *moved*. The
base model defaulted to `feat` (uninformative — a generic pretraining prior). The
fine-tune defaults to `fix` (a data-driven lean inherited from the training mix). That
is progress, not just a different flaw — a `fix`-lean driven by training composition is
a *correctable* error, because the training composition is a knob we control. We trade an
arbitrary prior for one we can engineer away.

## 3. Type disagreements with gold — two distinct phenomena

A large fraction of the model's type choices on the 442-row sample differ from the gold
prefix. These split into two opposite stories, and reading them honestly requires keeping
them apart — conflating them would either excuse a real model weakness as "gold's fault"
or dismiss a real data-quality problem as "model error."

### 3a. Gold is wrong, the model is more defensible
This is the evidence for the principle at the top of this document. CommitChronicle's gold
labels carry a strong `feat` bias and sometimes a prefix that contradicts the commit's own
description. In these cases the model's type is the better call, and exact-match scoring
would have *penalized the model for being right*. Representative cases:
- **id 131** — a version bump labeled `feat` in gold; the model says `chore`. A version bump
  is housekeeping. The model is correct.
- **id 2638** — gold reads `docs: fix routing`, but the diff updates a test; the model says
  `fix`. Gold's own description says "fix."
- **id 437 / id 2722** — the gold prefix contradicts its own description text.

This is exactly why type is scored on plausibility, not exact-match (ADR 0036), and why a
future iteration should curate the training set toward defensible pairs.

### 3b. The model is wrong, gold is right — the `fix`-bias
The same `fix`-lean that helps on average also misfires: the model over-assigns `fix`,
flattening the rarer types it saw little of during training. This is a genuine model
weakness, not gold being noisy. The misses cluster precisely on the low-frequency types:
- **style → fix** (ids 2788–2829): whitespace, renames, comment removal are genuinely `style`.
- **ci → fix** (ids 2831–2892): changes to CI scripts are genuinely `ci`.
- **perf → fix** (ids 2101–2121) and **build → fix** (ids 2760–2787): similar flattening.

These are the perf/build/ci/style types the dataset under-represents — which points
directly at the fix in §6.

## 4. Behaviors we still don't like

- **Messages are too short / under-specific.** Specificity is the one axis that regressed
  (0.81 → 0.71). The model faithfully learned the terse CommitChronicle subject style
  (training targets are tiny — ~38 chars at p99) and, in learning brevity, sometimes drops
  the concrete detail that makes a message useful. This is a learned property of the training
  targets, not a decoding bug.
- **The `fix`-collapse on rare types** (see §3b). About 19% of type choices still misfire,
  and they lean toward defaulting to the majority class.
- **Where this comes from.** The fine-tune replaced the base model's `feat`-prior (~95% feat
  at baseline) with a `fix`-lean inherited directly from the training set's type imbalance
  (`fix` is ~49% of training rows). The residual type errors are the model defaulting to that
  majority class on types it rarely saw.
- **An important distinction about the dataset stratification.** The dataset build *was*
  stratified on type and language (ADR 0025/0026) — but that stratification was tuned to keep
  the splits *representative* of the source distribution, which *preserves* the `fix`≈49%
  imbalance into the training set rather than *flattening* it. Representative is not the same
  as balanced. The build's balancing was not aggressive enough to offset the `fix`-prior
  because it was never trying to — it was preserving the real-world distribution by design.
  Correcting the model's bias means changing that design goal (see §6).

## 5. Caveats on the numbers

The headline numbers are trustworthy as a directional, fair-to-moderate signal — the Gemini
judge was validated against 50 genuine human ratings, with raw agreement of 0.72 / 0.68 /
0.76 / 0.84 across type / faithfulness / completeness / specificity and Cohen's κ of 0.377 /
0.384 / 0.543 / 0.254. That is good enough to trust the *direction and rough magnitude* of
the before/after, which is what this report claims.

Two honest limits: n=50 is small, so the validation carries wide confidence intervals; and
**the specificity axis is the shakiest of the four** — its κ (0.254) is the lowest and is
prevalence-deflated, meaning the judge and the human agreed often in raw terms (0.84) but
disagreed enough on the minority cases that the chance-corrected agreement is weak. So the
specificity regression in §1 is real enough to flag but should be read with the most caution
of any number here — it is also plausibly a rubric-calibration issue rather than purely a
model one (see §6).

## 6. Next-iteration hypotheses (v1-i2 / v2 — each routes through an ADR)

Both stories in §3 point at the same root fix: better training data. In rough order of leverage:

- **Rebalance the training-set type distribution (highest leverage; addresses the `fix`-lean).**
  The training split is `fix`-heavy (~49%). At *build* time, stratify toward a **flatter** type
  target — oversample the rare types (perf/build/ci/style), and consider capping `fix` — rather
  than a representative target. This is a change to the dataset-build composition (a `build.py`
  change and an amendment to ADR 0025/0026), and explicitly **not** a change to the eval strata
  sampler. The two are different knobs: the eval sampler controls what we measure on and cannot
  offset a bias baked into training.
- **Improve label quality.** Filter the training set to pairs whose gold type is *defensible
  against the diff*, dropping the §3a-style mislabels so the model trains on correct behavior
  rather than noise. Optionally supplement with synthetic, correctly-typed examples.
- **Address brevity / specificity.** Relax the subject-only normalization to keep slightly
  longer subjects or a one-line body, so the targets carry more concrete detail. For a fine-tuned
  model the training distribution dominates the prompt, so this is a data lever, not a prompt one.
- **Re-check the specificity rubric.** Given the low κ on specificity, the bar itself may be
  miscalibrated; the fix there is the rubric anchor text, not the model. Worth checking before
  attributing the specificity regression entirely to the model.

## 7. Side-by-side examples

Rendered by `scripts/build_examples_table.py` into `docs/eval/examples_v1_i1.md`. Curated set
spans both stories from §3 — cases where the model beats noisy gold (3a) and cases where the
model's `fix`-bias misfires (3b) — plus a clear win and a degenerate-gold example. Per-example
commentary to be added.

> TODO (Zook): final pass on wording throughout; populate §7 with curated examples + verdicts.