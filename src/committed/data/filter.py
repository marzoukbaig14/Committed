"""
filter.py — Convert raw CommitChronicle records into clean training rows.

This module is the dataset filter: the rules that decide which commits become
training examples, and how each example's target message is normalized. It is the
core of the Data phase — the dataset's quality is decided here.

Per record (one at a time, streaming-friendly):
    raw record  ->  predicates  ->  (reject -> None)  or  (assemble training row)

Key design points:
  - Language is identified per FILE by extension, never by CommitChronicle's
    per-repo `language` column, which mislabels polyglot repos (ADR 0022).
  - All languages are kept, not just Python (ADR 0023) — Python-only projected far
    below the dataset-size target.
  - Only code files are kept; a single-file commit touching only a non-code file
    (.md/.json/.yaml/...) is dropped, so the task stays "describe a code diff."

Loading lives in load.py; the build/push pass lives elsewhere. This module only
operates on already-loaded records (plain dicts), so it stays cheap to test.
"""

import os
import re
from functools import lru_cache

from transformers import AutoTokenizer

# --- Constants ---------------------------------------------------------------

MODEL_NAME = "Qwen/Qwen3-1.7B"   # tokenizer source for the cap; never tiktoken (MASTER.md)
TOKEN_CAP = 2048                 # max diff length in tokens; over-cap diffs are dropped.
                                 # Reversible hyperparameter — re-profile per language (ADR 0023).
MSG_MAX_CHARS = 200              # upper outlier ceiling on the subject line; no floor (ADR 0020)

# File extension -> canonical language. Identification is per file (ADR 0022): the
# repo-level `language` column is ignored entirely because it labels the whole repo,
# so a polyglot repo leaks non-matching files through. Code files only — config/docs
# extensions (.md/.json/.yaml/...) are deliberately absent, so commits that touch only
# such files are dropped. The language assigned here is also what the split stratifies on.
EXTENSION_TO_LANGUAGE = {
    ".py": "Python",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C", ".h": "C",                 # .h is ambiguous C/C++; treated as C
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++", ".hh": "C++", ".hxx": "C++",
    ".cs": "C#",
    ".rs": "Rust",
    ".kt": "Kotlin", ".kts": "Kotlin",
    ".swift": "Swift",
    ".scala": "Scala", ".sc": "Scala",
    ".sh": "Shell", ".bash": "Shell",
    ".m": "Objective-C", ".mm": "Objective-C",   # .m is ambiguous Obj-C/MATLAB; treated as Obj-C
    ".dart": "Dart",
    ".groovy": "Groovy",
    ".lua": "Lua",
    ".pl": "Perl", ".pm": "Perl",
    ".r": "R",
    ".ex": "Elixir", ".exs": "Elixir",
}


def file_language(path: str) -> str | None:
    """Return the language for a file path by its extension, or None if it is not a
    recognized code file. This is the per-file language signal we trust (ADR 0022)."""
    ext = os.path.splitext(path)[1].lower()
    return EXTENSION_TO_LANGUAGE.get(ext)


# --- Tokenizer + token counting ----------------------------------------------
# Loaded once and cached. Loading per call would re-read the tokenizer files every
# time and make the full pass crawl; lru_cache(maxsize=1) makes it a lazy singleton.
# Note: in the CPU Codespace, transformers prints a "PyTorch not found" warning on
# import — expected and harmless, since tokenizing needs no torch backend.

@lru_cache(maxsize=1)
def get_tokenizer():
    """Load and cache the Qwen3 tokenizer (the token-count authority for the cap)."""
    return AutoTokenizer.from_pretrained(MODEL_NAME)


def count_tokens(text: str) -> int:
    """Token count of `text` under the Qwen3 tokenizer.

    We count tokens (not lines or characters) because the cap exists to fit the
    model's context window, and the model sees tokens. add_special_tokens=False
    counts raw content only — the training template adds BOS/EOS later.
    """
    return len(get_tokenizer().encode(text, add_special_tokens=False))


# --- Filter logic ------------------------------------------------------------

# Conventional Commits matcher (ADR 0017), applied to the SUBJECT LINE, IGNORECASE.
#   group(1) = type   group(2) = (scope) or None   group(3) = description
# The description capture group lets normalization read the description directly
# rather than re-splitting the string, which is robust to a ': ' inside the scope.
# `doc` is accepted and normalized to `docs`; `revert` is intentionally absent
# (revert commits are dropped).
CC_PATTERN = re.compile(
    r"^(feat|fix|refactor|docs|test|chore|perf|style|build|ci|doc)(\([^)]+\))?!?: (.+)",
    re.IGNORECASE,
)


def match_conventional_commit(subject: str):
    """Return the regex match for a CC subject line, else None. Returning the match
    (not a bool) lets callers read the type group for normalization and the split."""
    return CC_PATTERN.match(subject)


# Bot detector: the dependency-bump template (Dependabot, Renovate, etc.). The author
# field is anonymized to an integer in CommitChronicle, so detection is message-based
# (ADR 0021). `search` (not `match`) so it also catches CC-prefixed bumps like
# `build(deps): bump ...`. The structured "bump X from Y to Z" shape keeps this
# precise — it does not fire on a human "bump version".
BOT_PATTERN = re.compile(r"bump .+ from .+ to .+", re.IGNORECASE)


def is_bot_commit(subject: str) -> bool:
    """True if the subject matches the dependency-bump template."""
    return BOT_PATTERN.search(subject) is not None


def _single_file_path(record: dict) -> str:
    """Path of the single modified file (new_path, falling back to old_path for deletes)."""
    mod = record["mods"][0]
    return mod.get("new_path") or mod.get("old_path") or ""


def passes_structural_filters(record: dict, subject: str) -> bool:
    """Cheap, non-token structural gates. Return True only if ALL hold:
      - exactly one file changed
      - that file is a recognized code file (any language) by extension (ADR 0022/0023)
      - subject length <= MSG_MAX_CHARS (upper outlier guard; no floor — the CC regex
        already guarantees a non-empty description)
      - not a merge, revert, or bot commit
    """
    if len(record.get("mods", [])) != 1:
        return False
    if file_language(_single_file_path(record)) is None:   # code file in any known language
        return False
    if len(subject) > MSG_MAX_CHARS:
        return False
    if subject.lower().startswith("merge"):                 # raw merge commits
        return False
    if subject.lower().startswith("revert"):                # revert commits
        return False
    if is_bot_commit(subject):
        return False
    return True


def normalize_target(subject: str) -> str:
    """Build the training target from the matched subject line (ADR 0017, 8 steps)."""
    subject = subject.splitlines()[0] if subject else ""    # 4. subject line only
    match = CC_PATTERN.match(subject)
    if not match:
        # Unreachable from build_row (it matches first); defensive only.
        result = subject.strip()
        return result[:-1] if result.endswith(".") else result

    commit_type = match.group(1).lower()          # 1. lowercase the type
    if commit_type == "doc":                       # 2. map doc -> docs
        commit_type = "docs"
    scope = match.group(2) or ""                   # 7. scope casing left unchanged
    description = match.group(3)                   # 8. description casing left unchanged
    # 3. the breaking '!' is dropped by rebuilding from type + scope (it sits between
    #    the scope and the colon, so it simply is not carried over).

    result = f"{commit_type}{scope}: {description}".strip()  # 5. strip surrounding whitespace
    if result.endswith("."):                       # 6. strip a single trailing period
        result = result[:-1]
    return result


# --- Assembly + driver -------------------------------------------------------

def assemble_diff(record: dict) -> str:
    """Diff for a single-file commit — just the one mod's diff. Kept as a function so
    relaxing the single-file filter later is a one-line change."""
    return record["mods"][0]["diff"]


def build_row(record: dict):
    """Apply all filters to one raw record; return a training row or None.

    Filter order is deliberate — the cheap, most-rejecting checks first and the
    expensive token count last — so we tokenize as few diffs as possible on the
    full pass.
    """
    message = record.get("message") or ""
    subject = message.splitlines()[0] if message else ""

    if not passes_structural_filters(record, subject):   # cheap structural gates
        return None
    if match_conventional_commit(subject) is None:        # cheap CC match
        return None

    # Expensive (tokenization) last. Over-cap diffs are DROPPED, not truncated — a
    # truncated diff could omit the very change the message describes.
    diff = assemble_diff(record)
    if count_tokens(diff) > TOKEN_CAP:
        return None

    # reasoning_trace is None in v1 (v2 fills it); repo + license retained for per-row
    # provenance (ADR 0012); language is per-file (from the extension) for the
    # stratified split (ADR 0023).
    return {
        "diff": diff,
        "message": normalize_target(subject),
        "reasoning_trace": None,
        "repo": record["repo"],
        "license": record["license"],
        "language": file_language(_single_file_path(record)),
    }


def filter_stream(dataset, limit: int | None = None):
    """Yield filtered training rows from an iterable (streaming) dataset. `limit` caps
    how many RAW records are read — use it for the spot-check before a full pass."""
    for i, record in enumerate(dataset):
        if limit is not None and i >= limit:
            break
        row = build_row(record)
        if row is not None:
            yield row