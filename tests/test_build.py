"""
test_build.py — Tests for apply_cap_and_floor and make_split (type-stratified split).

Pure-logic tests: no network, no tokenizer, no file I/O.
Run: uv run pytest tests/test_build.py -v
"""

from committed.data.build import (
    apply_cap_and_floor,
    make_split,
)


def _rows(lang: str, commit_type: str = "feat", n: int = 1) -> list[dict]:
    """Synthetic rows with unique diffs so leakage tests work correctly."""
    return [
        {
            "diff": f"diff-{lang}-{commit_type}-{i}",
            "message": f"{commit_type}: change {i}",
            "reasoning_trace": None,
            "repo": "r/r",
            "license": "MIT",
            "language": lang,
        }
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# apply_cap_and_floor
# ---------------------------------------------------------------------------

class TestApplyCapAndFloor:
    def test_floor_drops_thin_language(self):
        rows = _rows("Python", n=600) + _rows("Groovy", n=10)
        result = apply_cap_and_floor(rows, cap=6000, floor=500)
        langs = {r["language"] for r in result}
        assert "Python" in langs
        assert "Groovy" not in langs

    def test_cap_downsamples_large_language(self):
        rows = _rows("JavaScript", n=8000)
        result = apply_cap_and_floor(rows, cap=6000, floor=500)
        assert len(result) == 6000
        assert all(r["language"] == "JavaScript" for r in result)

    def test_mid_range_language_kept_in_full(self):
        rows = _rows("Go", n=1500)
        result = apply_cap_and_floor(rows, cap=6000, floor=500)
        assert len(result) == 1500

    def test_language_at_floor_is_kept(self):
        rows = _rows("Ruby", n=500)
        result = apply_cap_and_floor(rows, cap=6000, floor=500)
        assert len(result) == 500

    def test_language_one_below_floor_is_dropped(self):
        rows = _rows("Ruby", n=499)
        result = apply_cap_and_floor(rows, cap=6000, floor=500)
        assert result == []

    def test_deterministic_with_same_seed(self):
        rows = _rows("TypeScript", n=8000)
        r1 = apply_cap_and_floor(rows, cap=6000, floor=500, seed=42)
        r2 = apply_cap_and_floor(rows, cap=6000, floor=500, seed=42)
        assert [r["diff"] for r in r1] == [r["diff"] for r in r2]

    def test_different_seeds_produce_different_samples(self):
        rows = _rows("TypeScript", n=8000)
        r1 = apply_cap_and_floor(rows, cap=6000, floor=500, seed=42)
        r2 = apply_cap_and_floor(rows, cap=6000, floor=500, seed=99)
        assert [r["diff"] for r in r1] != [r["diff"] for r in r2]

    def test_multiple_languages(self):
        rows = (
            _rows("JavaScript", n=8000)   # capped to 6000
            + _rows("Python", n=1200)     # kept in full
            + _rows("R", n=3)             # dropped (< floor 500)
        )
        result = apply_cap_and_floor(rows, cap=6000, floor=500)
        by_lang = {r["language"] for r in result}
        assert by_lang == {"JavaScript", "Python"}
        js = [r for r in result if r["language"] == "JavaScript"]
        py = [r for r in result if r["language"] == "Python"]
        assert len(js) == 6000
        assert len(py) == 1200


# ---------------------------------------------------------------------------
# make_split  (type-stratified)
# ---------------------------------------------------------------------------

class TestMakeSplit:
    def test_total_rows_preserved(self):
        rows = _rows("Python", n=100) + _rows("Go", n=80)
        train, val, eval_ = make_split(rows)
        assert len(train) + len(val) + len(eval_) == 180

    def test_approximate_fractions(self):
        rows = _rows("Python", n=1000) + _rows("Go", n=1000)
        train, val, eval_ = make_split(rows, val_frac=0.05, eval_frac=0.05)
        total = len(train) + len(val) + len(eval_)
        assert abs(len(eval_) / total - 0.05) < 0.02
        assert abs(len(val) / total - 0.05) < 0.02

    def test_no_data_leakage_between_splits(self):
        rows = _rows("Python", n=200) + _rows("Go", n=200)
        train, val, eval_ = make_split(rows)
        train_diffs = {r["diff"] for r in train}
        val_diffs = {r["diff"] for r in val}
        eval_diffs = {r["diff"] for r in eval_}
        assert not train_diffs & val_diffs
        assert not train_diffs & eval_diffs
        assert not val_diffs & eval_diffs

    def test_stratifies_by_type(self):
        # A skewed type mix must be preserved in every split: a type-stratified
        # split keeps the same ~90% feat / 10% fix ratio in train, val, and eval,
        # instead of a split missing the rare type by chance.
        rows = _rows("Python", "feat", 900) + _rows("Python", "fix", 100)
        train, val, eval_ = make_split(rows)
        for split in (train, val, eval_):
            feat = sum(1 for r in split if r["message"].startswith("feat"))
            assert abs(feat / len(split) - 0.9) < 0.05

    def test_deterministic_with_same_seed(self):
        rows = _rows("Python", n=200) + _rows("Go", n=200)
        t1, v1, e1 = make_split(rows, seed=42)
        t2, v2, e2 = make_split(rows, seed=42)
        assert [r["diff"] for r in t1] == [r["diff"] for r in t2]
        assert [r["diff"] for r in e1] == [r["diff"] for r in e2]

    def test_all_splits_non_empty(self):
        rows = (
            _rows("Python", "feat", 40) + _rows("Python", "fix", 40)
            + _rows("Go", "feat", 40) + _rows("Go", "fix", 40)
        )
        train, val, eval_ = make_split(rows)
        assert len(train) > 0
        assert len(val) > 0
        assert len(eval_) > 0