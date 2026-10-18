"""Tests for the shared project configuration in config.py."""

import importlib
import re
from pathlib import Path

import config


def test_path_constants_are_under_project_root():
    assert config.PROJECT_ROOT.is_dir()
    for path in (
        config.RESULT_DIR,
        config.DRAFT_DIR,
        config.EXPERIMENTS_DIR,
        config.EXTERNAL_DATA_DIR,
        config.INTERIM_DATA_DIR,
        config.PROCESSED_DATA_DIR,
        config.FIGURE_DIR,
        config.TABLE_DIR,
        config.ANIMATION_DIR,
    ):
        assert isinstance(path, Path)
        assert config.PROJECT_ROOT in path.parents


def test_template_directories_exist():
    for path in (
        config.DATA_ROOT,
        config.RESULT_DIR,
        config.DRAFT_DIR,
        config.EXPERIMENTS_DIR,
        config.EXTERNAL_DATA_DIR,
        config.INTERIM_DATA_DIR,
        config.PROCESSED_DATA_DIR,
        config.FIGURE_DIR,
        config.TABLE_DIR,
        config.ANIMATION_DIR,
    ):
        assert path.is_dir(), f"Expected directory to exist: {path}"


def test_data_root_honours_environment_override(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    try:
        importlib.reload(config)
        assert config.DATA_ROOT == tmp_path
    finally:
        monkeypatch.undo()
        importlib.reload(config)


def _only_paths(value) -> bool:
    if isinstance(value, Path):
        return True
    if isinstance(value, dict):
        return all(_only_paths(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_only_paths(item) for item in value)
    return False


def test_config_holds_only_locations():
    # A shared value that can change a result (a window, a threshold, a data
    # selection, figure settings) would silently change finished experiments.
    not_paths = sorted(
        name for name, value in vars(config).items() if name.isupper() and not _only_paths(value)
    )
    assert not not_paths, (
        f"config.py holds only paths; move {not_paths} to the experiment's params.py "
        "(values that change results) or to a loader in src/models/ (a data file's format)"
    )


def test_config_reads_no_environment_switch_but_the_data_location():
    # An environment variable that picks an analysis option is an input nobody records.
    source = Path(config.__file__).read_text(encoding="utf-8")
    variables = set(re.findall(r"""os\.(?:environ(?:\.get)?|getenv)\s*[\[(]\s*["'](\w+)["']""", source))
    assert variables <= {"DATA_ROOT"}, f"config.py reads environment variables {sorted(variables - {'DATA_ROOT'})}"
