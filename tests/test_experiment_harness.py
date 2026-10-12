"""Checks the run harness (src/utils/experiment.py) and the experiment template.

A run records what produced it, --smoke never touches the full run or result/,
a completed run is not overwritten by accident, and promotion needs committed code.
"""

import json
import shutil
import signal
import subprocess
import sys
import types
from pathlib import Path

import pytest

from src.utils import experiment

ROOT = Path(__file__).resolve().parents[1]
PARAMS = types.SimpleNamespace(SEED=1, PARAMS={"n": 100}, SMOKE={"n": 2})


@pytest.fixture
def run_file(tmp_path, monkeypatch) -> str:
    monkeypatch.setattr(experiment, "git_state", lambda paths: {"commit": "abc", "dirty": []})
    (tmp_path / "001_toy").mkdir()
    return str(tmp_path / "001_toy" / "run.py")


def _record(run_file: str, *parts: str) -> dict:
    path = Path(run_file).parent.joinpath("out", *parts, experiment.RECORD)
    return json.loads(path.read_text(encoding="utf-8"))


def test_smoke_applies_its_values_never_promotes_and_leaves_the_full_run_alone(run_file) -> None:
    with experiment.start(run_file, PARAMS, ["--smoke"]) as run:
        assert run.params == {"n": 2}
        run.out("t.csv").write_text("a\n1\n", encoding="utf-8")
        with pytest.raises(AssertionError, match="--smoke"):
            run.promote("t.csv")
    record = _record(run_file, "smoke")
    assert (record["status"], record["smoke"], record["params"]) == ("completed", True, {"n": 2})
    assert not (Path(run_file).parent / "out" / experiment.RECORD).exists()


def test_a_completed_full_run_is_not_overwritten_without_the_flag(run_file) -> None:
    with experiment.start(run_file, PARAMS, []) as run:
        run.stage("only stage")
    record = _record(run_file)
    assert (record["status"], record["seed"], record["git"]["commit"]) == ("completed", 1, "abc")
    assert [stage["title"] for stage in record["stages"]] == ["only stage"]
    with pytest.raises(AssertionError, match="--overwrite"):
        with experiment.start(run_file, PARAMS, []):
            pass
    with experiment.start(run_file, PARAMS, ["--overwrite"]):
        pass


def test_a_rerun_clears_what_the_earlier_run_left(run_file) -> None:
    out = Path(run_file).parent / "out"
    with experiment.start(run_file, PARAMS, []) as run:
        run.out("kept.csv").write_text("1\n", encoding="utf-8")
        run.out("figures/stale.png").write_text("x", encoding="utf-8")
    with experiment.start(run_file, PARAMS, ["--smoke"]) as run:
        run.out("smoke.csv").write_text("1\n", encoding="utf-8")
    with experiment.start(run_file, PARAMS, ["--overwrite"]) as run:
        assert not (out / "figures").exists() and not (out / "kept.csv").exists()
        assert (out / "smoke" / "smoke.csv").is_file(), "a full run leaves out/smoke/ alone"
        run.out("kept.csv").write_text("2\n", encoding="utf-8")
    assert sorted(p.name for p in out.iterdir()) == ["kept.csv", experiment.RECORD, "smoke"]


def test_files_no_recorded_run_wrote_need_the_flag(run_file) -> None:
    out = Path(run_file).parent / "out"
    out.mkdir()
    (out / "manual.csv").write_text("1\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="no recorded run"):
        with experiment.start(run_file, PARAMS, []):
            pass
    assert (out / "manual.csv").is_file()


@pytest.mark.parametrize("name", ["../escape.csv", "/tmp/escape.csv", "."])
def test_outputs_cannot_leave_the_output_directory(run_file, name: str) -> None:
    with experiment.start(run_file, PARAMS, []) as run:
        with pytest.raises(AssertionError, match="not a file under"):
            run.out(name)
        with pytest.raises(AssertionError, match="not a file under"):
            run.promote(name)


def test_a_failed_run_is_recorded_and_can_be_rerun(run_file) -> None:
    with pytest.raises(RuntimeError, match="boom"):
        with experiment.start(run_file, PARAMS, []) as run:
            run.out("partial.csv").write_text("1\n", encoding="utf-8")
            raise RuntimeError("boom")
    record = _record(run_file)
    assert record["status"] == "failed" and "boom" in record["error"]
    with experiment.start(run_file, PARAMS, []):
        pass
    assert not (Path(run_file).parent / "out" / "partial.csv").exists(), "a retry clears the failed run's outputs"
    assert _record(run_file)["status"] == "completed"


def test_promotion_needs_committed_code(run_file, monkeypatch, tmp_path) -> None:
    with experiment.start(run_file, PARAMS, []) as run:
        run.out("t.csv").write_text("a\n1\n", encoding="utf-8")
        promoted = run.promote("t.csv", dest_dir=tmp_path / "tables")
    assert promoted.read_text(encoding="utf-8") == "a\n1\n"
    assert _record(run_file)["promoted"] == [str(promoted.resolve())]
    monkeypatch.setattr(experiment, "git_state", lambda paths: {"commit": "abc", "dirty": [" M src/x.py"]})
    with experiment.start(run_file, PARAMS, ["--overwrite"]) as run:
        run.out("t.csv").write_text("a\n2\n", encoding="utf-8")
        with pytest.raises(AssertionError, match="Commit"):
            run.promote("t.csv", dest_dir=tmp_path / "tables")


def test_smoke_values_must_be_parameters(run_file) -> None:
    with pytest.raises(AssertionError, match="SMOKE"):
        with experiment.start(run_file, types.SimpleNamespace(SEED=1, PARAMS={"n": 1}, SMOKE={"m": 1}), ["--smoke"]):
            pass


def _project_copy(tmp_path: Path) -> Path:
    # Runs happen in a copy, so that nothing is written into the repository.
    project = tmp_path / "project"
    shutil.copytree(ROOT / "src", project / "src", ignore=shutil.ignore_patterns("__pycache__"))
    for name in ("config.py", "uv.lock"):
        shutil.copy2(ROOT / name, project / name)
    return project


def test_a_run_stopped_by_sigterm_is_recorded_as_failed(tmp_path) -> None:
    project = _project_copy(tmp_path)
    target = project / "experiments" / "001_sleeper"
    target.mkdir(parents=True)
    (target / "run.py").write_text(
        "import sys, time, types\n"
        f"sys.path.insert(0, {str(project)!r})\n"
        "from src.utils import experiment\n"
        "params = types.SimpleNamespace(SEED=1, PARAMS={})\n"
        "with experiment.start(__file__, params, []):\n"
        "    print('ready', flush=True)\n"
        "    time.sleep(60)\n",
        encoding="utf-8",
    )
    process = subprocess.Popen([sys.executable, str(target / "run.py")], cwd=project, stdout=subprocess.PIPE, text=True)
    for line in process.stdout:
        if line.strip() == "ready":
            break
    process.send_signal(signal.SIGTERM)
    assert process.wait(timeout=30) == 128 + signal.SIGTERM
    record = json.loads((target / "out" / experiment.RECORD).read_text(encoding="utf-8"))
    assert record["status"] == "failed" and "finished" in record


def test_the_template_runs_and_writes_only_to_its_out(tmp_path) -> None:
    project = _project_copy(tmp_path)
    target = project / "experiments" / "999_probe"
    shutil.copytree(ROOT / "experiments" / "_template", target, ignore=shutil.ignore_patterns("__pycache__", "smoke"))
    before = set(project.rglob("*"))
    result = subprocess.run([sys.executable, str(target / "run.py"), "--smoke"], cwd=project,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    written = sorted(p for p in set(project.rglob("*")) - before if p.is_file())
    assert written and all(p.is_relative_to(target / "out" / "smoke") for p in written), written
    assert json.loads((target / "out" / "smoke" / experiment.RECORD).read_text(encoding="utf-8"))["status"] == "completed"
