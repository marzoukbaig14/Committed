"""
test_filter.py — Regression tests for the dataset filter.

Pure-logic tests (no tokenizer, no network). build_row's token-cap step is tested
with count_tokens monkeypatched. Run: uv run pytest tests/test_filter.py -v
"""

import pytest

from committed.data import filter as f


@pytest.mark.parametrize("subject, expected", [
    ("feat: add login",        "feat: add login"),
    ("Fix: handle error",      "fix: handle error"),
    ("Fix(API): handle null.", "fix(API): handle null"),
    ("feat!: drop support",    "feat: drop support"),
    ("feat(api)!: drop x",     "feat(api): drop x"),
    ("doc: update readme",     "docs: update readme"),
    ("fix: handle a: b case",  "fix: handle a: b case"),
    ("feat(a: b): do x",       "feat(a: b): do x"),
])
def test_normalize_target(subject, expected):
    assert f.normalize_target(subject) == expected


@pytest.mark.parametrize("subject, is_bot", [
    ("Bump lodash from 4.17.20 to 4.17.21",       True),
    ("build(deps): bump numpy from 1.21 to 1.22", True),
    ("chore: bump version to 2.0.1",              False),
    ("fix: handle null",                          False),
])
def test_is_bot_commit(subject, is_bot):
    assert f.is_bot_commit(subject) is is_bot


@pytest.mark.parametrize("subject, matches", [
    ("feat: x",           True),
    ("wip: x",            False),
    ("revert: x",         False),
    ("Merge branch main", False),
])
def test_match_conventional_commit(subject, matches):
    assert (f.match_conventional_commit(subject) is not None) is matches


@pytest.mark.parametrize("path, lang", [
    ("a/b/c.py",     "Python"),
    ("src/app.tsx",  "TypeScript"),
    ("main.go",      "Go"),
    ("Foo.java",     "Java"),
    ("lib.rs",       "Rust"),
    ("README.md",    None),       # not a code file
    ("config.json",  None),
    ("noext",        None),
])
def test_file_language(path, lang):
    assert f.file_language(path) == lang


def _rec(mods=1, path="src/x.py"):
    return {"mods": [{"diff": "d", "new_path": path}] * mods, "repo": "r", "license": "MIT"}


@pytest.mark.parametrize("record, subject, ok", [
    (_rec(),                   "feat: add x",        True),    # .py
    (_rec(path="src/app.ts"),  "feat: add x",        True),    # .ts now kept (all-languages)
    (_rec(path="main.go"),     "feat: add x",        True),    # .go
    (_rec(path="README.md"),   "feat: add x",        False),   # non-code file dropped
    (_rec(path="config.json"), "feat: add x",        False),   # non-code file dropped
    (_rec(mods=2),             "feat: add x",        False),   # multi-file
    (_rec(),                   "feat: " + "x" * 300, False),   # over the 200 ceiling
    (_rec(),                   "Merge branch x",     False),
    (_rec(),                   'Revert "feat: x"',   False),
])
def test_passes_structural_filters(record, subject, ok):
    assert f.passes_structural_filters(record, subject) is ok


def test_build_row_keeps_good_record(monkeypatch):
    monkeypatch.setattr(f, "count_tokens", lambda text: 10)
    record = {
        "mods": [{"diff": "diff --git a/app.ts...", "new_path": "src/app.ts"}],
        "message": "Fix(API): handle null.\n\nlong body here",
        "repo": "octocat/hello",
        "license": "MIT",
    }
    assert f.build_row(record) == {
        "diff": "diff --git a/app.ts...",
        "message": "fix(API): handle null",
        "reasoning_trace": None,
        "repo": "octocat/hello",
        "license": "MIT",
        "language": "TypeScript",
    }


def test_build_row_drops_overcap_diff(monkeypatch):
    monkeypatch.setattr(f, "count_tokens", lambda text: f.TOKEN_CAP + 1)
    record = {
        "mods": [{"diff": "x", "new_path": "x.py"}],
        "message": "feat: add x",
        "repo": "r",
        "license": "MIT",
    }
    assert f.build_row(record) is None