"""Tests for the shared project configuration in config.py."""

import importlib
from pathlib import Path

import config


def test_path_constants_are_under_project_root():
    assert config.PROJECT_ROOT.is_dir()
    for path in (
        config.RESULT_DIR,
        config.DRAFT_DIR,
        config.EXPERIMENTS_DIR,
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
