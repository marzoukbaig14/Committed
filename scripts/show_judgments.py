"""
Pretty-print a judge JSONL log: per example, the candidate message and each axis's label +
rationale, with diffs omitted for readability. For eyeballing judge behavior. Plumbing.

Usage:
  uv run python scripts/show_judgments.py judge_check_log.jsonl
"""

import json
import sys

AXES = ["type_correctness", "faithfulness", "completeness", "specificity"]


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "judge_check_log.jsonl"
    n = 0
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        j = r.get("judgment", {})
        print("=" * 88)
        print(f"id {r.get('id')}  |  message: {r.get('message')!r}")
        if j.get("diff_summary"):
            print(f"diff_summary: {j['diff_summary']}")
        for a in AXES:
            ax = j.get(a, {})
            print(f"  {a:18} [{ax.get('label', '?')}]  {ax.get('rationale', '')}")
        n += 1
    print("=" * 88)
    print(f"{n} judgments")


if __name__ == "__main__":
    main()