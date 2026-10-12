"""Checks scripts/new_experiment.py (make experiment SLUG=<slug>)."""

import datetime
import shutil
from pathlib import Path

import pytest

from scripts import new_experiment

ROOT = Path(__file__).resolve().parents[1]
TODAY = datetime.date(2026, 1, 2)
# A header-only index, so the test does not depend on this project's experiments.
EMPTY_INDEX = "# 実験インデックス\n\n| # | slug | 一行で | 状態 |\n|---|---|---|---|\n"


@pytest.fixture
def root(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "experiments" / "_template", tmp_path / "experiments" / "_template",
                    ignore=shutil.ignore_patterns("__pycache__", "smoke"))
    (tmp_path / "experiments" / "EXP_SUMMARY.md").write_text(EMPTY_INDEX, encoding="utf-8")
    return tmp_path


def test_creates_numbered_filled_experiments_and_index_rows(root: Path) -> None:
    first, second = new_experiment.create(root, "a", TODAY), new_experiment.create(root, "b_c", TODAY)
    assert (first.name, second.name) == ("001_a", "002_b_c")
    for path in (first, second):
        assert (path / "out" / ".gitkeep").is_file()
        for name in new_experiment.FILLED:
            text = (path / name).read_text(encoding="utf-8")
            assert "NNN_<slug>" not in text and "YYYY-MM-DD" not in text, f"{path.name}/{name}"
    rows = [line for line in (root / "experiments" / "EXP_SUMMARY.md").read_text(encoding="utf-8").splitlines()
            if line.startswith("| 0")]
    assert rows == ["| 001 | a | (実行前) | 進行中 |", "| 002 | b_c | (実行前) | 進行中 |"]


def test_numbers_continue_after_the_highest_directory_or_index_row(root: Path) -> None:
    (root / "experiments" / "007_old").mkdir()
    assert new_experiment.create(root, "next", TODAY).name == "008_next"


@pytest.mark.parametrize("slug", ["Bad-Slug", "", "a" * 41, "trailing_"])
def test_invalid_slugs_stop(root: Path, slug: str) -> None:
    with pytest.raises(AssertionError):
        new_experiment.create(root, slug, TODAY)


def test_a_reused_slug_stops(root: Path) -> None:
    new_experiment.create(root, "a", TODAY)
    with pytest.raises(AssertionError, match="already used"):
        new_experiment.create(root, "a", TODAY)
