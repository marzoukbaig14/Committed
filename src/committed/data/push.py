"""
push.py — Publish the local train/val/eval splits to the Hugging Face Hub.

Runs AFTER build.py has written data/train.jsonl, data/val.jsonl, data/eval.jsonl.
Loads the three splits into a DatasetDict, pushes them to <repo_id>, then writes a
documented dataset card on top of the auto-generated metadata.

The Hub is the source of truth for artifacts (MASTER.md): once pushed, the dataset
is durable and pullable from anywhere (Colab, the cluster, the eval harness) by
name — independent of this ephemeral Codespace.

Split naming: local val.jsonl -> Hub "validation", local eval.jsonl -> Hub "test"
(the conventional HF split names).

Auth: needs HF_TOKEN (write scope) in the environment.

Run:
  uv run python -m committed.data.push --dry-run    # load + print the card, no upload
  uv run python -m committed.data.push              # publish to the Hub
"""

from __future__ import annotations

import argparse
import os
from collections import Counter
from pathlib import Path

from datasets import load_dataset
from huggingface_hub import DatasetCard

DEFAULT_REPO = "marzoukbaig14/committed-train"
DEFAULT_DATA = Path("data")

# local split file -> Hub split name (HF convention)
SPLIT_FILES = {
    "train": "train.jsonl",
    "validation": "val.jsonl",
    "test": "eval.jsonl",
}

CITATION = (
    "Eliseeva et al., *From Commit Message Generation to History-Aware Commit "
    "Message Generation*, arXiv:2308.07655."
)


def _commit_type(message: str) -> str:
    """CC type prefix (text before '(' or ':'), matching build.py."""
    return message.split("(")[0].split(":")[0]


def load_splits(data_dir: Path):
    """Load the three local JSONL splits into a DatasetDict keyed by Hub names."""
    data_files = {}
    for hub_split, fname in SPLIT_FILES.items():
        path = data_dir / fname
        if not path.exists():
            raise FileNotFoundError(
                f"missing split file: {path} — run `build.py` (without --dry-run) first"
            )
        data_files[hub_split] = str(path)
    return load_dataset("json", data_files=data_files)


def _composition_tables(dsdict) -> str:
    """Markdown tables of split sizes, language mix, and commit-type mix,
    computed from the actual data so the card never drifts from reality."""
    lines = ["| Split | Rows |", "|---|---|"]
    for split in ("train", "validation", "test"):
        lines.append(f"| {split} | {len(dsdict[split]):,} |")

    # aggregate language + type counts across all splits
    all_langs: Counter = Counter()
    all_types: Counter = Counter()
    total = 0
    for split in dsdict:
        all_langs.update(dsdict[split]["language"])
        all_types.update(_commit_type(m) for m in dsdict[split]["message"])
        total += len(dsdict[split])

    lines.append("\n**Languages** (identified by file extension):\n")
    lines += ["| Language | Rows | % |", "|---|---|---|"]
    for lang, n in all_langs.most_common():
        lines.append(f"| {lang} | {n:,} | {100 * n / total:.1f}% |")

    lines.append("\n**Commit types:**\n")
    lines += ["| Type | Rows | % |", "|---|---|---|"]
    for t, n in all_types.most_common():
        lines.append(f"| {t} | {n:,} | {100 * n / total:.1f}% |")

    return "\n".join(lines)


def build_card_body(dsdict) -> str:
    """Human-readable dataset-card body (markdown). Frontmatter/tags are set
    separately on the card loaded back from the Hub, so the auto-generated split
    metadata is preserved."""
    body = """
# Committed — Conventional Commits dataset

Filtered (diff -> Conventional Commits message) pairs derived from
[CommitChronicle](https://huggingface.co/datasets/JetBrains-Research/commit-chronicle),
for fine-tuning small models to write commit messages from a diff. Built by the
[Committed](https://github.com/marzoukbaig14/Committed) project.

## Schema

| Field | Type | Notes |
|---|---|---|
| `diff` | string | The code diff for a single-file change. |
| `message` | string | Normalized Conventional Commits subject line (the training target). |
| `reasoning_trace` | string \\| null | Reserved for v2 (reasoning distillation); always `null` here. |
| `repo` | string | Source repository (provenance). |
| `license` | string | Source repository's license (provenance). |
| `language` | string | Programming language, identified by file extension. |

## Composition

__COMPOSITION__

## How it was built

Starting from CommitChronicle, a commit is kept only if:

- the subject line matches a relaxed Conventional Commits pattern
  (`feat|fix|refactor|docs|test|chore|perf|style|build|ci`, optional scope,
  optional breaking `!`), then normalized (lowercase type, `doc` -> `docs`, strip
  `!`, subject line only, trim, strip one trailing period);
- the subject is 5-200 characters;
- it touches exactly one file, and that file is a recognized **code** file by
  extension (the per-repo language attribute is ignored because it mislabels
  polyglot repos);
- it is not a merge, revert, or bot commit (e.g. Dependabot, detected by message
  pattern);
- the diff is at most 2048 tokens (Qwen3-1.7B tokenizer); over-cap diffs are
  dropped, not truncated.

The pool is then balanced (each language capped to 6,000 rows, languages with
fewer than 500 rows dropped) and split 90/5/5 train/validation/test, **stratified
by commit type** so each split preserves the type distribution.

## Provenance & license

Each row keeps its source `repo` and `license`. CommitChronicle aggregates
permissively-licensed repositories (MIT, Apache-2.0, BSD-3-Clause); this
derivative is redistributed under those source terms. Please cite CommitChronicle
and its paper:

> __CITATION__

## Known limitations

- The source scan covered ~85-90% of CommitChronicle's train split, not a full
  pass, so the language mix is near-complete rather than exhaustive.
- Commit types are imbalanced (`fix` is the plurality); a trivial
  always-predict-`fix` baseline scores around its share, so read prefix-accuracy
  against that floor.
- Description casing is not normalized (acronyms are preserved) — an accepted v1
  limitation.
- No automated scrubbing of secrets/PII; the sensitive-data caveat from
  CommitChronicle is carried forward.
"""
    body = body.replace("__COMPOSITION__", _composition_tables(dsdict))
    body = body.replace("__CITATION__", CITATION)
    return body


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-id", default=DEFAULT_REPO,
                    help=f"Hub dataset id (default: {DEFAULT_REPO})")
    ap.add_argument("--data", default=DEFAULT_DATA, type=Path,
                    help="directory holding the split JSONL files")
    ap.add_argument("--private", action="store_true",
                    help="create the Hub dataset as private")
    ap.add_argument("--dry-run", action="store_true",
                    help="load splits and print the card; do not upload")
    args = ap.parse_args()

    dsdict = load_splits(args.data)
    print("loaded splits:")
    for split in dsdict:
        print(f"  {split:<11} {len(dsdict[split]):,} rows")

    card_body = build_card_body(dsdict)

    if args.dry_run:
        print("\n----- dataset card body (dry run, not uploaded) -----\n")
        print(card_body)
        print("\n(dry run — nothing pushed)")
        return

    token = os.environ.get("HF_TOKEN")
    if not token:
        raise SystemExit("HF_TOKEN not set in the environment (needs write scope).")

    print(f"\npushing dataset to {args.repo_id} …")
    dsdict.push_to_hub(args.repo_id, private=args.private, token=token)

    # push_to_hub wrote a README with auto split/feature metadata. Load it back so
    # we keep that metadata, then layer on our documentation and tags.
    print("writing dataset card …")
    card = DatasetCard.load(args.repo_id, repo_type="dataset", token=token)
    card.text = card_body
    card.data.license = "other"
    card.data.language = ["en", "code"]
    card.data.task_categories = ["text-generation"]
    card.data.tags = ["code", "commit-messages", "conventional-commits", "git"]
    card.push_to_hub(args.repo_id, repo_type="dataset", token=token)

    print(f"done → https://huggingface.co/datasets/{args.repo_id}")


if __name__ == "__main__":
    main()