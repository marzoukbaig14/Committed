"""
Committed — human-rating worksheet builder + validator (judge calibration).

The judge-vs-human agreement (Cohen's kappa per axis) is the credibility signal for the whole
eval — the number that says "trust this judge." To produce it you hand-rate a sample of the same
(diff, candidate) pairs the judge saw, then run_eval --human-ratings computes the agreement.

This module is the plumbing around that:

  build  -- pick a deterministic, gold-type-stratified sample (equal per type) from the judged
            candidates and write:
              (1) a markdown WORKSHEET showing ONLY the diff + candidate message (never the gold
                  message, never the judge's labels) so you rate BLIND — blind rating is what
                  makes the agreement meaningful; and
              (2) a jsonl SKELETON in the exact schema run_eval --human-ratings expects, with empty
                  axis fields for you to fill with "pass"/"fail".

  check  -- validate a filled skeleton before you spend a re-run on it: every row present, every
            axis labelled exactly "pass" or "fail". Catches the silent footgun where a blank field
            would be read as "" and scored as a fail.

Workflow:
  1. uv run python -m committed.eval.human_rate build \
         --candidates analysis/results/baseline_strata442.jsonl
  2. Rate every example in the worksheet; copy each pass/fail into the matching id in the skeleton.
  3. uv run python -m committed.eval.human_rate check --ratings analysis/human_ratings_50.jsonl
  4. Re-run run_eval with --human-ratings analysis/human_ratings_50.jsonl (the judge log is already
     full, so no judge spend) -> report.validation carries kappa + raw agreement per axis.

Rate by the SAME rubric the judge used (docs/eval/judge_rubric.md). In particular type_correctness
is plausibility-based (gold is NOT consulted) — which is why the worksheet hides the gold type.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

# Reuse the canonical loaders + join from run_eval so selection sees exactly the same id space the
# judge scored — no reinventing the reference/candidate alignment.
from committed.eval.run_eval import AXES, load_candidates, load_references_from_hub

DEFAULT_DATASET = "marzoukbaig14/committed-train"
# These live at analysis/ root (NOT analysis/results/), so they're tracked — only
# analysis/results/*.jsonl is gitignored, and the human ratings are a load-bearing artifact.
DEFAULT_WORKSHEET = "analysis/human_worksheet_50.md"
DEFAULT_SKELETON = "analysis/human_ratings_50.jsonl"


def select_stratified(ids_by_type: dict[str, list[str]], n: int, seed: int) -> list[str]:
    """Equal-allocation pick across gold types, deterministic.

    Shuffle each type's ids with `seed`, then draw round-robin across types (sorted for a stable
    order) one id at a time until we have `n`. Round-robin yields equal counts per type when every
    type has enough, and take-all-then-move-on for scarce types — same spirit as build_strata.
    """
    rng = random.Random(seed)
    pools: dict[str, list[str]] = {}
    for t in sorted(ids_by_type):
        pool = list(ids_by_type[t])
        rng.shuffle(pool)
        pools[t] = pool

    selected: list[str] = []
    while len(selected) < n and any(pools.values()):
        for t in sorted(pools):
            if pools[t]:
                selected.append(pools[t].pop())
                if len(selected) >= n:
                    break
    return selected


def render_worksheet(selected: list[str], refs: dict[str, dict], cands: dict[str, str],
                     seed: int) -> str:
    """Markdown worksheet. Interleaves examples (a seeded shuffle, distinct from the selection
    stream) so you're not rating one type in a block, and shows ONLY diff + candidate."""
    order = list(selected)
    random.Random(seed + 1).shuffle(order)

    head = [
        "# Committed — human rating worksheet",
        "",
        f"{len(order)} examples. Rate each on the four axes, **pass** or **fail**, using the rubric "
        "in `docs/eval/judge_rubric.md`. Rate only from the diff and the candidate below — the gold "
        "message and the judge's labels are deliberately hidden. type_correctness is plausibility-"
        "based (would a reviewer accept this type for this diff?), not match-to-gold.",
        "",
        "Axes: type_correctness · faithfulness (hard gate) · completeness · specificity.",
        "",
        "When done, copy each pass/fail into the matching id in the skeleton jsonl.",
    ]

    blocks = []
    for k, ex_id in enumerate(order, 1):
        blocks.append("\n".join([
            "",
            "---",
            "",
            f"## {k} of {len(order)}  ·  id `{ex_id}`",
            "",
            "**Diff**",
            "```diff",
            refs[ex_id]["diff"],
            "```",
            "",
            "**Candidate message**",
            "",
            f"> {cands[ex_id]}",
            "",
            "**Ratings** (pass / fail):",
            "- type_correctness: ",
            "- faithfulness: ",
            "- completeness: ",
            "- specificity: ",
        ]))
    return "\n".join(head + blocks) + "\n"


def write_skeleton(selected: list[str], path: Path) -> None:
    """jsonl skeleton: one line per id with empty axis fields, in run_eval --human-ratings schema.
    Sorted by int id so it lines up with the worksheet's `id` headers."""
    with path.open("w") as f:
        for ex_id in sorted(selected, key=lambda x: int(x) if x.isdigit() else x):
            row = {"id": ex_id, **{ax: "" for ax in AXES}}
            f.write(json.dumps(row) + "\n")


def cmd_build(args: argparse.Namespace) -> None:
    refs = load_references_from_hub(args.dataset, args.split)
    cands = load_candidates(Path(args.candidates))
    ids = [i for i in refs if i in cands]  # identical join to run_eval
    if not ids:
        sys.exit("[human_rate] no overlapping ids between references and candidates.")

    by_type: dict[str, list[str]] = defaultdict(list)
    for i in ids:
        by_type[refs[i]["type"] or "<unknown>"].append(i)

    selected = select_stratified(by_type, args.n, args.seed)

    alloc: dict[str, int] = defaultdict(int)
    for i in selected:
        alloc[refs[i]["type"] or "<unknown>"] += 1
    print(f"[human_rate] selected {len(selected)} ids (n requested={args.n}, seed={args.seed})")
    print("[human_rate] per-type:", dict(sorted(alloc.items())))

    Path(args.worksheet).write_text(render_worksheet(selected, refs, cands, args.seed))
    write_skeleton(selected, Path(args.skeleton))
    print(f"[human_rate] wrote worksheet -> {args.worksheet}")
    print(f"[human_rate] wrote skeleton  -> {args.skeleton}  (fill pass/fail, then run `check`)")


def cmd_check(args: argparse.Namespace) -> None:
    path = Path(args.ratings)
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    problems: list[str] = []
    seen: set[str] = set()
    for r in rows:
        ex_id = str(r.get("id", "<no id>"))
        seen.add(ex_id)
        for ax in AXES:
            v = r.get(ax)
            if v not in ("pass", "fail"):
                problems.append(f"  id {ex_id}: {ax}={v!r} (must be 'pass' or 'fail')")
    print(f"[human_rate] {len(rows)} rows, {len(seen)} unique ids in {path}")
    if problems:
        print(f"[human_rate] {len(problems)} unfilled/invalid field(s):")
        print("\n".join(problems))
        sys.exit(1)
    print("[human_rate] all rows fully labelled — ready for run_eval --human-ratings.")

def cmd_ingest(args: argparse.Namespace) -> None:
    """Parse a filled worksheet markdown back into the ratings jsonl, so you rate in ONE file (the
    worksheet, where the diff is right there) instead of hand-editing json. Accepts pass/fail or
    p/f, case-insensitive; leaves an axis blank if you left it blank (run `check` to catch those).
    """
    import re

    text = Path(args.worksheet).read_text()
    id_re = re.compile(r"id\s+`([^`]+)`")
    axis_re = re.compile(r"^-\s*(type_correctness|faithfulness|completeness|specificity)\s*:\s*(.*)$")
    norm = {"p": "pass", "pass": "pass", "f": "fail", "fail": "fail"}

    ratings: dict[str, dict] = {}
    cur: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        m = id_re.search(stripped)
        if stripped.startswith("##") and m:           # an example header -> switch current id
            cur = m.group(1)
            ratings.setdefault(cur, {})
            continue
        am = axis_re.match(stripped)
        if am and cur is not None:                     # a rating line under the current id
            ax, raw = am.group(1), am.group(2).strip().lower()
            if raw:
                if raw not in norm:
                    sys.exit(f"[human_rate] id {cur} {ax}: unrecognized rating {raw!r} (use pass/fail).")
                ratings[cur][ax] = norm[raw]

    with Path(args.out).open("w") as f:
        for ex_id in sorted(ratings, key=lambda x: int(x) if x.isdigit() else x):
            row = {"id": ex_id, **{ax: ratings[ex_id].get(ax, "") for ax in AXES}}
            f.write(json.dumps(row) + "\n")
    filled = sum(1 for r in ratings.values() for ax in AXES if r.get(ax))
    print(f"[human_rate] parsed {len(ratings)} ids, {filled}/{len(ratings) * len(AXES)} fields filled")
    print(f"[human_rate] wrote {args.out}  (now run `check`)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build / validate the human-rating set for judge calibration.")
    sub = ap.add_subparsers(dest="mode", required=True)

    b = sub.add_parser("build", help="Select a stratified sample and write the worksheet + skeleton.")
    b.add_argument("--candidates", required=True, help="The judged candidates jsonl (id -> message).")
    b.add_argument("--dataset", default=DEFAULT_DATASET, help="HF dataset for references (diff + gold type).")
    b.add_argument("--split", default="test")
    b.add_argument("--n", type=int, default=50, help="Sample size (default 50).")
    b.add_argument("--seed", type=int, default=0, help="Deterministic seed (default 0).")
    b.add_argument("--worksheet", default=DEFAULT_WORKSHEET)
    b.add_argument("--skeleton", default=DEFAULT_SKELETON)
    b.set_defaults(func=cmd_build)

    c = sub.add_parser("check", help="Validate a filled skeleton before running validation.")
    c.add_argument("--ratings", required=True, help="The filled human-ratings jsonl.")
    c.set_defaults(func=cmd_check)

    g = sub.add_parser("ingest", help="Parse a filled worksheet markdown into the ratings jsonl.")
    g.add_argument("--worksheet", default=DEFAULT_WORKSHEET, help="The filled worksheet.")
    g.add_argument("--out", default=DEFAULT_SKELETON, help="Ratings jsonl to write.")
    g.set_defaults(func=cmd_ingest)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()