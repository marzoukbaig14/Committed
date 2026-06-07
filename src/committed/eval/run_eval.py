"""
Committed — eval harness orchestrator.

Ties the whole eval together:
  1. Load REFERENCES (test split): diff + gold message, from the Hub or a local jsonl.
  2. Load CANDIDATES (the model's generations) keyed by id, and align with references.
  3. Deterministic metrics (metrics.py): BLEU, ROUGE-L, prefix-accuracy + per-type + fix-floor.
  4. LLM judge (judge.py / judge_gemini.py): score each (diff, candidate) on the four axes.
  5. Aggregate the judge log into the per-axis vector + the gate-then-grade composite + per-type.
  6. (Optional) Validate the judge against human ratings: agreement + kappa per axis.
  7. Write a JSON report + a short markdown summary.

GENERATION IS DECOUPLED. This harness judges candidates it is GIVEN; it does not generate them.
The baseline / fine-tune produces a candidates jsonl separately (id -> message); run_eval consumes
it. That keeps eval independent of the inference path and lets the same harness score any model.

JOIN KEY. Candidates align to references by `id`. If a candidates row has no `id`, none is
assumed — so the generation step must emit ids that match the reference ids. References loaded
from the Hub are keyed by row index (stable for a fixed dataset version); a local --refs jsonl may
carry explicit ids.

COMPOSITE (ADR E). Implemented HERE, not in the judge:
  - per-axis pass rates (the vector — always reported alongside any headline).
  - conjunctive pass-rate (primary): a message passes iff ALL FOUR axes pass.
  - graded headline (optional, for A/B and checkpoint ranking): 0 if faithfulness fails, else
    1 + completeness({fail:0, pass:1}) + specificity({fail:0, pass:1}). Type is
    NOT in the graded number by default (it gates the conjunctive metric and shows in the vector);
    `--type-gate` additionally zeroes the graded score when type fails, if you want that.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from committed.eval import metrics

AXES = ("type_correctness", "faithfulness", "completeness", "specificity")
COMPLETENESS_VAL = {"fail": 0.0, "pass": 1.0}


# --------------------------------------------------------------------------------------------
# Load references + candidates
# --------------------------------------------------------------------------------------------

def load_references_from_hub(dataset: str, split: str) -> dict[str, dict]:
    """id (row index, as str) -> {diff, gold, type, language?}. `datasets` imported lazily."""
    from datasets import load_dataset

    ds = load_dataset(dataset, split=split)
    refs: dict[str, dict] = {}
    for i, row in enumerate(ds):
        gold = row["message"]
        refs[str(i)] = {
            "diff": row["diff"],
            "gold": gold,
            "type": metrics.parse_type(gold),       # derived, so we don't depend on a 'type' column
            "language": row.get("language"),          # present in this dataset; None-safe otherwise
        }
    return refs


def load_references_from_jsonl(path: Path) -> dict[str, dict]:
    """Local jsonl with at least 'diff' and 'message' (gold) per line; 'id' optional (else index)."""
    refs: dict[str, dict] = {}
    with path.open() as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            ex_id = str(row.get("id", i))
            gold = row["message"]
            refs[ex_id] = {
                "diff": row["diff"],
                "gold": gold,
                "type": metrics.parse_type(gold),
                "language": row.get("language"),
            }
    return refs


def load_candidates(path: Path) -> dict[str, str]:
    """jsonl with 'message' (the generated candidate) per line; 'id' optional (else index)."""
    cands: dict[str, str] = {}
    with path.open() as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            cands[str(row.get("id", i))] = row["message"]
    return cands


# --------------------------------------------------------------------------------------------
# Judge log -> per-axis labels
# --------------------------------------------------------------------------------------------

def load_judge_labels(judge_log: Path) -> dict[str, dict]:
    """Read the judge JSONL log into id -> {axis: label}. Skips malformed lines defensively."""
    labels: dict[str, dict] = {}
    if not judge_log.exists():
        return labels
    with judge_log.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                j = row["judgment"]
                labels[str(row["id"])] = {ax: j[ax]["label"] for ax in AXES}
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    return labels


# --------------------------------------------------------------------------------------------
# Composite (gate-then-grade, ADR E)
# --------------------------------------------------------------------------------------------

def passes_conjunctive(labels: dict) -> bool:
    """True iff all four axes pass."""
    return (
        labels.get("faithfulness") == "pass"
        and labels.get("type_correctness") == "pass"
        and labels.get("completeness") == "pass"
        and labels.get("specificity") == "pass"
    )


def graded_score(labels: dict, *, type_gate: bool = False) -> float:
    """0 if faithfulness fails (or type, when type_gate); else 1 + completeness + specificity.
    Range: {0} U {1, 2, 3} (all axes binary)."""
    if labels.get("faithfulness") == "fail":
        return 0.0
    if type_gate and labels.get("type_correctness") == "fail":
        return 0.0
    comp = COMPLETENESS_VAL.get(labels.get("completeness"), 0.0)
    spec = 1.0 if labels.get("specificity") == "pass" else 0.0
    return 1.0 + comp + spec


def aggregate_composite(
    judge_labels: dict[str, dict],
    ref_types: dict[str, str | None],
    *,
    type_gate: bool = False,
) -> dict:
    """Roll judge labels up into the per-axis vector + conjunctive pass-rate + graded mean, overall
    and broken down by gold commit type."""
    ids = list(judge_labels.keys())
    n = len(ids)
    if n == 0:
        return {"n": 0}

    # Per-axis vector (distribution of labels per axis).
    vector: dict[str, dict] = {}
    for ax in AXES:
        counts: dict[str, int] = defaultdict(int)
        for i in ids:
            counts[judge_labels[i].get(ax, "<missing>")] += 1
        vector[ax] = {lbl: counts[lbl] / n for lbl in counts}

    conjunctive = sum(passes_conjunctive(judge_labels[i]) for i in ids) / n
    graded_mean = sum(graded_score(judge_labels[i], type_gate=type_gate) for i in ids) / n

    # Per-type breakdown (by GOLD type), since 'fix' dominates and a global number can hide skew.
    by_type_ids: dict[str, list[str]] = defaultdict(list)
    for i in ids:
        by_type_ids[ref_types.get(i) or "<unknown>"].append(i)
    per_type = {
        t: {
            "n": len(tids),
            "conjunctive_pass_rate": sum(passes_conjunctive(judge_labels[i]) for i in tids) / len(tids),
            "graded_mean": sum(graded_score(judge_labels[i], type_gate=type_gate) for i in tids) / len(tids),
        }
        for t, tids in by_type_ids.items()
    }

    return {
        "n": n,
        "per_axis_vector": vector,
        "conjunctive_pass_rate": conjunctive,
        "graded_mean": graded_mean,
        "graded_max": 3.0,
        "type_gated": type_gate,
        "per_type": per_type,
    }


# --------------------------------------------------------------------------------------------
# Judge-vs-human validation (the headline trust number)
# --------------------------------------------------------------------------------------------

def validate_against_human(
    judge_labels: dict[str, dict],
    human_labels: dict[str, dict],
) -> dict:
    """Per-axis agreement between judge and human on the ids both rated. All four axes are binary
    -> Cohen's kappa + raw agreement."""
    from sklearn.metrics import cohen_kappa_score

    common = [i for i in judge_labels if i in human_labels]
    out: dict = {"n": len(common), "axes": {}}
    if not common:
        return out

    binary_enc = {"fail": 0, "pass": 1}

    for ax in AXES:
        j = [judge_labels[i].get(ax) for i in common]
        h = [human_labels[i].get(ax) for i in common]
        jj = [binary_enc.get(x, 0) for x in j]
        hh = [binary_enc.get(x, 0) for x in h]
        raw = sum(a == b for a, b in zip(jj, hh)) / len(common)
        try:
            kappa = float(cohen_kappa_score(jj, hh))
        except Exception:
            kappa = None
        out["axes"][ax] = {"raw_agreement": raw, "cohen_kappa": kappa}
    return out


# --------------------------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------------------------

def write_markdown(report: dict, path: Path) -> None:
    det = report["deterministic"]
    comp = report["composite"]
    lines = [
        "# Committed — eval report",
        "",
        f"- Examples judged: **{comp.get('n', 0)}**  |  candidate model: `{report.get('model','?')}`",
        "",
        "## Deterministic",
        f"- BLEU: {det['bleu']:.2f}  (short-text caveat — not a headline)",
        f"- ROUGE-L (F): {det['rouge_l']:.3f}",
        f"- Prefix-type accuracy: {det['prefix']['accuracy']:.3f}  "
        f"(always-`fix` floor: {det['prefix']['always_fix_floor']:.3f})",
        "",
        "## LLM judge — composite (gate-then-grade)",
        f"- Conjunctive pass-rate (all four axes pass): "
        f"**{comp['conjunctive_pass_rate']:.3f}**",
        f"- Graded mean (0–3, type-gated={comp['type_gated']}): {comp['graded_mean']:.3f}",
        "",
        "### Per-axis vector",
    ]
    for ax, dist in comp["per_axis_vector"].items():
        dist_str = ", ".join(f"{k}={v:.2f}" for k, v in sorted(dist.items()))
        lines.append(f"- {ax}: {dist_str}")
    if report.get("validation"):
        v = report["validation"]
        lines += ["", f"## Judge-vs-human validation (n={v['n']})"]
        for ax, m in v["axes"].items():
            lines.append(f"- {ax}: " + ", ".join(f"{k}={('NA' if val is None else round(val,3))}"
                                                 for k, val in m.items()))
    path.write_text("\n".join(lines) + "\n")


# --------------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Run the full Committed eval over a candidates file.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--dataset", help="HF dataset id for references (e.g. marzoukbaig14/committed-train).")
    src.add_argument("--refs", help="Local jsonl of references (diff + message[+id]).")
    ap.add_argument("--split", default="test", help="Dataset split when using --dataset.")
    ap.add_argument("--candidates", required=True, help="jsonl of generations (message[+id]).")
    ap.add_argument("--backend", choices=["gemini", "claude"], default="gemini",
                    help="LLM judge backend (default: free Gemini).")
    ap.add_argument("--judge-log", required=True, help="JSONL path for judge output (resumable).")
    ap.add_argument("--report", required=True, help="Output path stem for the report (.json/.md).")
    ap.add_argument("--human-ratings", help="Optional jsonl of human axis labels for validation.")
    ap.add_argument("--type-gate", action="store_true", help="Also zero the graded score on type fail.")
    ap.add_argument("--limit", type=int, default=None, help="Max NEW examples to judge this run.")
    ap.add_argument("--ceiling", type=float, default=None, help="USD ceiling (Claude backend only).")
    args = ap.parse_args()

    # 1-2. references + candidates, aligned on id.
    refs = (load_references_from_hub(args.dataset, args.split) if args.dataset
            else load_references_from_jsonl(Path(args.refs)))
    cands = load_candidates(Path(args.candidates))
    ids = [i for i in refs if i in cands]
    if not ids:
        sys.exit("[run_eval] no overlapping ids between references and candidates — check the join key.")
    print(f"[run_eval] {len(ids)} aligned examples (refs={len(refs)}, cands={len(cands)})", file=sys.stderr)

    cand_list = [cands[i] for i in ids]
    gold_list = [refs[i]["gold"] for i in ids]

    # 3. deterministic metrics.
    det = metrics.compute_deterministic(cand_list, gold_list)

    # 4. LLM judge (lazy backend import so we don't require both SDKs).
    if args.backend == "claude":
        from committed.eval import judge as backend
    else:
        from committed.eval import judge_gemini as backend
    judge_records_kwargs = {"limit": args.limit}
    if args.backend == "claude" and args.ceiling is not None:
        judge_records_kwargs["ceiling_usd"] = args.ceiling
    records = ({"id": i, "diff": refs[i]["diff"], "message": cands[i]} for i in ids)
    backend.judge_records(records, args.judge_log, **judge_records_kwargs)

    # 5. aggregate the judge log.
    judge_labels = load_judge_labels(Path(args.judge_log))
    ref_types = {i: refs[i]["type"] for i in ids}
    composite = aggregate_composite(judge_labels, ref_types, type_gate=args.type_gate)

    # 6. optional human validation.
    validation = None
    if args.human_ratings:
        human = _load_human(Path(args.human_ratings))
        validation = validate_against_human(judge_labels, human)

    # 7. report.
    report = {"model": args.backend, "deterministic": det, "composite": composite,
              "validation": validation}
    report_stem = Path(args.report)
    report_stem.with_suffix(".json").write_text(json.dumps(report, indent=2))
    write_markdown(report, report_stem.with_suffix(".md"))
    print(f"[run_eval] wrote {report_stem.with_suffix('.json')} and {report_stem.with_suffix('.md')}")

    os._exit(0)  # Codespaces streaming/shutdown guard


def _load_human(path: Path) -> dict[str, dict]:
    """Human ratings jsonl: one line per example with {id, type_correctness, faithfulness,
    completeness, specificity} as label strings."""
    out: dict[str, dict] = {}
    with path.open() as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            ex_id = str(row.get("id", i))
            out[ex_id] = {ax: row[ax] for ax in AXES if ax in row}
    return out


if __name__ == "__main__":
    main()