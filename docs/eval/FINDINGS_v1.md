# Committed — v1 Fine-Tune Evaluation

What happened when I fine-tuned Qwen3-1.7B to write Conventional Commit messages from
diffs, measured honestly against the zero-shot baseline. This is the eval writeup for v1,
iteration 1. The short version: the fine-tune went from worse-than-guessing to genuinely
useful at the thing that matters most, one axis regressed, and the residual errors point at
a specific, fixable data problem rather than a modeling dead end.

---

## How to read these numbers: gold is not the target

The training and eval data are real, not synthetic — CommitChronicle commit messages
written by developers in the wild. They carry real labeling mistakes: a heavy `feat` bias,
prefixes that contradict their own description text, housekeeping commits dressed up as
features. I did not want a model that memorizes and reproduces those mistakes, so
exact-match against the gold label is explicitly **not** the metric. Type correctness is
scored on plausibility against the diff (ADR 0036), not agreement with gold. That choice
runs through everything below: when the model disagrees with gold, sometimes the model is
right and sometimes it's wrong, and those two cases are kept apart rather than averaged into
one misleading accuracy number.

The setup: zero-shot Qwen3-1.7B baseline vs. the 2-epoch QLoRA fine-tune, on the same
442-row equal-allocation strata sample, through the same Gemini 2.5 Flash judge and the same
frozen rubric (ADR 0035/0036). Only the model weights differ between the two columns.
Headline numbers are reweighted to the true test-split type distribution (ADR 0037), so they
reflect deployment behavior rather than the artificially balanced sample.

---

## Before / after

| Metric | Baseline (zero-shot) | Fine-tune | Δ |
|---|---|---|---|
| Prefix-type accuracy (deployment-reweighted) | 0.131 | 0.637 | +0.506 |
| — always-`fix` floor (same for both) | 0.489 | 0.489 | — |
| Conjunctive pass-rate (all 4 axes pass) | 0.181 | 0.471 | +0.290 |
| Graded mean (0–3) | 1.207 | 2.188 | +0.981 |
| type_correctness | 0.33 | 0.81 | +0.48 |
| faithfulness | 0.43 | 0.86 | +0.43 |
| completeness | 0.52 | 0.73 | +0.21 |
| specificity | 0.81 | 0.71 | −0.10 |
| BLEU (diagnostic; short-text caveat) | 2.17 | 11.79 | +9.62 |
| ROUGE-L F (diagnostic) | 0.156 | 0.305 | +0.149 |

Source: `analysis/results/baseline_report.md`, `analysis/results/finetune_report.md`.

---

## What actually happened

The fine-tune crossed the line that matters. The baseline's deployment-reweighted type
accuracy was 0.131 — roughly 3.7x *worse* than a model that blindly guesses `fix` every
time (the 0.489 floor). Left to itself, the base model collapsed to `feat` on about 95% of
diffs, which is worse than useless: a confident, uninformative default. The fine-tune sits
at 0.637, clearly above the trivial floor. It went from worse-than-guessing to actually
choosing types. Faithfulness — the hard gate, where a single unsupported claim disqualifies
the whole message — nearly doubled, 0.43 to 0.86. Every judged axis improved except
specificity.

The most useful way to describe the change is that the failure mode *moved*. The base model
defaulted to `feat`, an arbitrary artifact of its pretraining prior. The fine-tune defaults
to `fix`, a lean it inherited from the training mix (`fix` is about 49% of the training
rows). That's progress, not just a reshuffled flaw — an arbitrary prior got traded for a
data-driven one, and the training composition is a knob I control. I can engineer the second
problem away. I couldn't have touched the first.

---

## Type disagreements with gold: two opposite stories

A large share of the model's type choices on the 442-row sample differ from the gold prefix.
Those disagreements split into two stories that look identical in an aggregate accuracy score
and mean opposite things. Collapsing them would either excuse a real model weakness as
"gold's fault" or wave off a real data-quality problem as "model error," so I keep them
separate.

### When gold is wrong and the model is right

This is the whole reason type is scored on plausibility instead of exact-match.
CommitChronicle's labels carry a strong `feat` bias and sometimes a prefix that contradicts
the commit's own text. In these cases exact-match scoring would have *penalized the model for
being correct*. A few representative cases:

- **id 131** — a version bump labeled `feat` in gold; the model says `chore`. A version bump
  is housekeeping. The model is right.
- **id 2638** — gold reads `docs: fix routing`, but the diff edits a test; the model says
  `fix`. Gold's own description literally says "fix."
- **id 437 / id 2722** — the gold prefix contradicts its own description text.

A future iteration should curate the training set toward defensible pairs so the model trains
on correct behavior rather than this noise.

### When the model is wrong and gold is right: the `fix`-bias

The same `fix`-lean that helps on average also misfires. The model over-assigns `fix` and
flattens the rarer types it saw little of in training. This is a genuine weakness, not gold
being noisy, and the misses cluster exactly where you'd predict — on the low-frequency types:

- **style → fix** (ids 2788–2829): whitespace, renames, comment removal are genuinely `style`.
- **ci → fix** (ids 2831–2892): changes to CI scripts are genuinely `ci`.
- **perf → fix** (ids 2101–2121) and **build → fix** (ids 2760–2787): the same flattening.

These are precisely the perf/build/ci/style types the dataset under-represents, which points
straight at the highest-leverage fix in the next-steps section.

---

## What I still don't like

Messages run too short and under-specific. Specificity is the one axis that regressed, 0.81
to 0.71. The model faithfully learned the terse CommitChronicle subject style — the training
targets are tiny, about 38 characters at the 99th percentile — and in learning that brevity
it sometimes drops the concrete detail that makes a message worth reading. This is a learned
property of the training targets, not a decoding bug, and I confirmed that separately (below).

The `fix`-collapse on rare types is the other one. About 19% of type choices still misfire,
and they lean toward defaulting to the majority class. Both of these trace to the same source:
the fine-tune replaced the base model's `feat`-prior with a `fix`-lean inherited directly
from the training set's imbalance.

One distinction worth being precise about, because it's easy to state wrong. The dataset
build *was* stratified on type and language (ADR 0025/0026) — but that stratification was
tuned to keep the splits *representative* of the source distribution, which **preserves** the
`fix`≈49% imbalance into training rather than flattening it. Representative is not balanced.
The build wasn't failing to offset the `fix`-prior; it was never trying to — preserving the
real-world distribution was the design goal. Correcting the model's bias means changing that
goal, not fixing a bug.

### A note on where the brevity came from

The aggressive v1 normalization — subject line only, strip emoji and gitmoji, English
Conventional Commit types only, a tight length ceiling — did its job. It eliminated the early
problems: rambling messages, emoji, non-English output. But it trained the model toward
terseness as a side effect. The under-specific output is the downstream cost of the cleanup
that killed the noise. The next iteration has to thread that needle: relax normalization
enough to recover informative detail without letting the noise back in.

I also checked whether this was fixable with prompt wording before committing to a retrain.
It isn't. I ran three increasingly aggressive rewrites of the prompt's specificity guidance;
each changed a large share of the output phrasing but moved every quality axis by less than
the run-to-run noise at temperature 0.2. The fine-tuned model follows its training
distribution over prompt instructions — reshuffling the prompt reshuffles surface wording
without changing verbosity or quality. (This was an informal directional probe judged by an
agent, not the validated Gemini judge, so I'm not putting numbers to it here — but the
direction was unambiguous.) The practical consequence: specificity is a training-data lever
for i2, and the live demo ships on the exact evaluated config, so demo behavior matches these
numbers with no divergence.

---

## How much to trust the numbers

The headline is a fair-to-moderate signal, good enough for the direction and rough magnitude
of the before/after, which is all this report claims. The Gemini judge was validated against
50 genuine human ratings, with raw agreement of 0.72 / 0.68 / 0.76 / 0.84 across type /
faithfulness / completeness / specificity, and Cohen's κ of 0.377 / 0.384 / 0.543 / 0.254.

Two honest limits. n=50 is small, so that validation carries wide confidence intervals. And
specificity is the shakiest of the four axes: its κ (0.254) is the lowest and is
prevalence-deflated — the judge and human agreed often in raw terms (0.84) but disagreed
enough on the minority cases that the chance-corrected number is weak. So the specificity
regression is real enough to flag but should be read with the most caution of anything here.
It's also plausibly a rubric-calibration issue rather than purely a model one, which is why
re-checking the rubric anchors is on the list below.

---

## Next iteration

Both stories above point at the same root cause — the training data — so that's where the
leverage is. Roughly in order:

1. **Rebalance the training-set type distribution.** Highest leverage; this is the direct fix
   for the `fix`-lean. At build time, stratify toward a *flatter* type target — oversample the
   rare types (perf/build/ci/style), consider capping `fix` — instead of a representative one.
   This is a `build.py` change plus an amendment to ADR 0025/0026, and explicitly *not* a
   change to the eval strata sampler. Those are different knobs: the eval sampler controls what
   I measure on and cannot offset a bias baked into training.
2. **Improve label quality.** Filter training to pairs whose gold type is defensible against
   the diff, dropping the mislabels so the model trains on correct behavior, and optionally
   supplement with synthetic correctly-typed examples.
3. **Address brevity.** Relax the subject-only normalization (ADR 0017) to keep slightly longer
   subjects or a one-line body, so the targets carry more concrete detail. For a fine-tuned
   model the training distribution dominates the prompt, so this is a data lever, confirmed by
   the prompt probe above.
4. **Re-check the specificity rubric.** Given the low κ, the bar itself may be miscalibrated.
   If so the fix is the rubric anchor text, not the model — worth checking before pinning the
   regression entirely on the weights.

Each routes through an ADR.

---

## Examples

Curated side-by-side cases — where the model beats noisy gold, where its `fix`-bias misfires,
a clean win, and a degenerate-gold example — with per-case verdicts are in
[`docs/eval/examples_v1_i1.md`](examples_v1_i1.md).

---

*Methodology and every design decision behind this eval are in the decision log
(`docs/DECISION_LOG.md`, ADRs 0027–0037 cover the rubric and scoring). The dataset, adapter,
and quantized model are on the Hugging Face Hub.*
