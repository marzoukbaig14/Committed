"""
Committed — deterministic eval metrics.

The non-LLM half of the eval: metrics that are objective and reproducible, computed in code (per
the "heuristic checks belong in code, not the judge" principle). run_eval.py calls these and the
LLM judge, then combines everything.

Metrics here (all on candidate-vs-gold pairs):
  - BLEU (sacrebleu, corpus-level): reported for completeness; unreliable on text this short.
  - ROUGE-L (rouge-score, mean F): complementary overlap signal.
  - Prefix-classification accuracy: did the candidate pick the same Conventional Commits TYPE as
    the gold? Categorical and deterministic. Reported with a per-type breakdown and against the
    always-predict-`fix` floor (~49% on this dataset) so the headline number is read honestly.

The one real choice in here is `parse_type` — how the type prefix is extracted from a message.
It mirrors the ADR 0017 filter regex (same type codebook, same `doc`->`docs` normalization) so
"the type" means the same thing in eval as it did at data-build time. If the filter regex changes,
change this with it.

Heavy deps (sacrebleu, rouge_score, sklearn) are imported lazily inside the functions that use
them, so this module (and `parse_type`) imports with no extra packages installed.
"""

from __future__ import annotations

import re
from collections import defaultdict

# Conventional Commits type codebook (ADR 0017). `doc` is an accepted alias normalized to `docs`.
CC_TYPES = ("feat", "fix", "refactor", "docs", "test", "chore", "perf", "style", "build", "ci")
_TYPE_RE = re.compile(
    r"^\s*(feat|fix|refactor|docs|test|chore|perf|style|build|ci|doc)(\([^)]*\))?!?:",
    re.IGNORECASE,
)


def parse_type(message: str | None) -> str | None:
    """Extract the Conventional Commits type from a message subject line, or None if it doesn't
    match the CC form. Mirrors the ADR 0017 filter regex: case-insensitive, optional (scope),
    optional breaking `!`, required `:`. `doc` normalizes to `docs`."""
    if not message:
        return None
    m = _TYPE_RE.match(message)
    if not m:
        return None
    t = m.group(1).lower()
    return "docs" if t == "doc" else t


# --------------------------------------------------------------------------------------------
# BLEU / ROUGE-L
# --------------------------------------------------------------------------------------------

def compute_bleu(candidates: list[str], references: list[str]) -> float:
    """Corpus BLEU (0-100) via sacrebleu. Short-text caveat applies — report, don't lead with it."""
    import sacrebleu

    # sacrebleu wants references as a list of reference-streams: [[ref1, ref2, ...]].
    return float(sacrebleu.corpus_bleu(candidates, [references]).score)


def compute_rouge_l(candidates: list[str], references: list[str]) -> float:
    """Mean ROUGE-L F-measure (0-1) via rouge-score, with stemming."""
    from rouge_score import rouge_scorer

    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    if not candidates:
        return 0.0
    total = 0.0
    for cand, ref in zip(candidates, references):
        total += scorer.score(ref, cand)["rougeL"].fmeasure
    return total / len(candidates)


# --------------------------------------------------------------------------------------------
# Prefix-classification accuracy
# --------------------------------------------------------------------------------------------

def compute_prefix_accuracy(candidates: list[str], references: list[str]) -> dict:
    """Type-prefix accuracy of candidate vs gold, with per-type breakdown and the always-`fix`
    floor. A candidate whose type can't be parsed counts as wrong.

    Returns:
      {
        "accuracy": float,                 # overall, candidate type == gold type
        "n": int,
        "per_type": {gold_type: {"n": int, "accuracy": float}},
        "always_fix_floor": float,         # fraction of gold == 'fix' (trivial-baseline accuracy)
        "unparseable_candidates": int,     # candidates with no parseable type
      }
    """
    n = len(references)
    if n == 0:
        return {"accuracy": 0.0, "n": 0, "per_type": {}, "always_fix_floor": 0.0,
                "unparseable_candidates": 0}

    correct = 0
    unparseable = 0
    fix_count = 0
    per_type_total: dict[str, int] = defaultdict(int)
    per_type_correct: dict[str, int] = defaultdict(int)

    for cand, ref in zip(candidates, references):
        gold_t = parse_type(ref)
        cand_t = parse_type(cand)
        if cand_t is None:
            unparseable += 1
        if gold_t == "fix":
            fix_count += 1
        # bucket by gold type (the true label) for the per-type view
        key = gold_t if gold_t is not None else "<unparseable_gold>"
        per_type_total[key] += 1
        if cand_t is not None and cand_t == gold_t:
            correct += 1
            per_type_correct[key] += 1

    per_type = {
        t: {"n": per_type_total[t], "accuracy": per_type_correct[t] / per_type_total[t]}
        for t in per_type_total
    }
    return {
        "accuracy": correct / n,
        "n": n,
        "per_type": per_type,
        "always_fix_floor": fix_count / n,
        "unparseable_candidates": unparseable,
    }


# --------------------------------------------------------------------------------------------
# Top-level convenience
# --------------------------------------------------------------------------------------------

def compute_deterministic(candidates: list[str], references: list[str]) -> dict:
    """Run all deterministic metrics over aligned candidate/reference lists."""
    return {
        "bleu": compute_bleu(candidates, references),
        "rouge_l": compute_rouge_l(candidates, references),
        "prefix": compute_prefix_accuracy(candidates, references),
    }