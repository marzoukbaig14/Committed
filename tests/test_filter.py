"""
test_filter.py — Regression tests for the dataset filter.

These are pure-logic tests (no tokenizer, no network), so they run fast in the
Codespace and in CI. build_row's token-cap step is tested with count_tokens
monkeypatched, so no model download happens.

Run:  uv run pytest tests/test_filter.py -v
"""

import pytest

from committed.data import filter as f


@pytest.mark.parametrize("subject, expected", [
    ("feat: add login",        "feat: add login"),
    ("Fix: handle error",      "fix: handle error"),         # type lowercased
    ("Fix(API): handle null.", "fix(API): handle null"),     # scope kept, period stripped
    ("feat!: drop support",    "feat: drop support"),        # breaking '!' stripped
    ("feat(api)!: drop x",     "feat(api): drop x"),
    ("doc: update readme",     "docs: update readme"),       # doc -> docs
    ("fix: handle a: b case",  "fix: handle a: b case"),     # colon inside description
    ("feat(a: b): do x",       "feat(a: b): do x"),          # colon-space inside scope (regression)
])
def test_normalize_target(subject, expected):
    assert f.normalize_target(subject) == expected


@pytest.mark.parametrize("subject, is_bot", [
    ("Bump lodash from 4.17.20 to 4.17.21",       True),
    ("build(deps): bump numpy from 1.21 to 1.22", True),
    ("chore: bump version to 2.0.1",              False),    # human bump — must be kept
    ("fix: handle null",                          False),
])
def test_is_bot_commit(subject, is_bot):
    assert f.is_bot_commit(subject) is is_bot


@pytest.mark.parametrize("subject, matches", [
    ("feat: x",           True),
    ("wip: x",            False),    # non-CC type
    ("revert: x",         False),    # revert excluded by design
    ("Merge branch main", False),
])
def test_match_conventional_commit(subject, matches):
    assert (f.match_conventional_commit(subject) is not None) is matches


def _rec(language="Python", mods=1):
    return {"language": language, "mods": [{"diff": "d"}] * mods}


@pytest.mark.parametrize("record, subject, ok", [
    (_rec(),              "feat: add x",        True),
    (_rec(language="Go"), "feat: add x",        False),
    (_rec(mods=2),        "feat: add x",        False),
    (_rec(),              "feat: " + "x" * 300, False),   # over the 200 ceiling
    (_rec(),              "Merge branch x",     False),
    (_rec(),              'Revert "feat: x"',   False),
])
def test_passes_structural_filters(record, subject, ok):
    assert f.passes_structural_filters(record, subject) is ok


def test_build_row_keeps_good_record(monkeypatch):
    # Patch out the token count so the test needs no tokenizer / network.
    monkeypatch.setattr(f, "count_tokens", lambda text: 10)
    record = {
        "language": "Python",
        "mods": [{"diff": "diff --git a/x.py..."}],
        "message": "Fix(API): handle null.\n\nlong body here",
        "repo": "octocat/hello",
        "license": "MIT",
    }
    assert f.build_row(record) == {
        "diff": "diff --git a/x.py...",
        "message": "fix(API): handle null",
        "reasoning_trace": None,
        "repo": "octocat/hello",
        "license": "MIT",
    }


def test_build_row_drops_overcap_diff(monkeypatch):
    monkeypatch.setattr(f, "count_tokens", lambda text: f.TOKEN_CAP + 1)
    record = {
        "language": "Python",
        "mods": [{"diff": "x"}],
        "message": "feat: add x",
        "repo": "r",
        "license": "MIT",
    }
    assert f.build_row(record) is None