"""Checks the runtime environment rules in AGENTS.md (Environment Rules).

Project Python runs in Docker, the environment and tool state stay off the
bind-mounted repository, and raw data is read-only through every mount. These
checks never try to write to the raw data.
"""

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_python_runs_in_docker_without_a_host_virtualenv() -> None:
    assert Path("/.dockerenv").is_file(), "Run project Python and tests in Docker (docker compose exec ...)"
    assert not (ROOT / ".venv").exists() and not (ROOT / "venv").exists(), "A virtualenv exists in the repository"
    assert "UV_PROJECT_ENVIRONMENT" in os.environ, "UV_PROJECT_ENVIRONMENT is not set (see docker-compose.yml)"
    environment = Path(os.environ["UV_PROJECT_ENVIRONMENT"]).resolve()
    assert Path(sys.prefix).resolve() == environment
    assert not environment.is_relative_to(ROOT), environment


@pytest.mark.parametrize("variable", ["HOME", "UV_CACHE_DIR", "MPLCONFIGDIR", "PYTHONPYCACHEPREFIX", "RUFF_CACHE_DIR"])
def test_runtime_state_stays_outside_the_source_mount(variable: str) -> None:
    assert variable in os.environ, f"{variable} is not set (see docker-compose.yml)"
    path = Path(os.environ[variable])
    assert path.is_absolute() and not path.resolve().is_relative_to(ROOT), f"{variable}={path}"


@pytest.mark.parametrize("path", [Path("/data"), ROOT / "data" / "raw"])
def test_raw_data_mounts_are_read_only(path: Path) -> None:
    assert path.is_dir(), path
    assert os.statvfs(path).f_flag & os.ST_RDONLY, f"Raw data mount is writable: {path}"
