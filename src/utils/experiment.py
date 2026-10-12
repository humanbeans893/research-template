"""Run harness for experiments/NNN_<slug>/run.py (AGENTS.md, Experiments).

Every experiment gets the same flags and the same record:

- ``--smoke`` applies ``params.SMOKE``, writes to ``out/smoke/`` and never
  promotes, so a mistake surfaces in seconds and each stage can be timed.
- A completed full run is not replaced without ``--overwrite``.
- ``out/params_used.json`` records the status (running, completed or failed),
  seed, parameters, git commit and uncommitted code, Python, uv.lock, stage
  timings and promoted files.
"""

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

import config

RECORD = "params_used.json"
# Code whose uncommitted changes make a run unreproducible, besides the
# experiment's own *.py.
CODE_PATHS = ("src", "config.py", "pyproject.toml", "uv.lock")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _relative(path: Path) -> str:
    path, root = Path(path).resolve(), config.PROJECT_ROOT.resolve()
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def _write(path: Path, record: dict) -> None:
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def git_state(paths: list[str]) -> dict:
    """HEAD and the uncommitted files among paths. Without a commit, dirty says why."""

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=config.PROJECT_ROOT, capture_output=True, text=True, check=False)

    head = git("rev-parse", "HEAD")
    if head.returncode != 0:
        return {"commit": None, "dirty": [f"(no commit: {head.stderr.strip()})"]}
    status = git("status", "--porcelain", "--untracked-files=all", "--", *paths)
    assert status.returncode == 0, f"git status failed: {status.stderr.strip()}"
    return {"commit": head.stdout.strip(), "dirty": status.stdout.splitlines()}


class Run:
    """What run.py gets from ``with experiment.start(__file__, params) as run:``."""

    def __init__(self, name: str, out_dir: Path, smoke: bool, seed: int, params: dict, record: dict) -> None:
        self.name, self.out_dir, self.smoke = name, out_dir, smoke
        self.seed, self.params, self.record = seed, params, record
        self._start = time.perf_counter()

    def elapsed(self) -> float:
        return time.perf_counter() - self._start

    def stage(self, title: str) -> None:
        """Start a stage: printed at once and timed in the record."""
        stages = self.record["stages"]
        stages.append({"title": title, "start_s": round(self.elapsed(), 3)})
        print(f"[{self.name}] {len(stages)}. {title} (t = {self.elapsed():.1f} s)", flush=True)

    def log(self, text: str) -> None:
        print(f"    {text} ({self.elapsed():.1f} s)", flush=True)

    def out(self, name: str) -> Path:
        """Path for an output under out/ (out/smoke/ with --smoke)."""
        path = self.out_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def promote(self, name: str, dest_dir: Path = config.TABLE_DIR) -> Path:
        """Copy an output to result/ (tables by default). Do this last."""
        assert not self.smoke, "--smoke never writes to result/"
        dirty = self.record["git"]["dirty"]
        assert not dirty, f"Commit these, rerun, then promote: {dirty}"
        source = self.out_dir / name
        assert source.is_file(), f"{_relative(source)} does not exist: write it through run.out() first"
        dest = Path(dest_dir) / Path(name).name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        self.record["promoted"].append(_relative(dest))
        self.log(f"promoted -> {_relative(dest)}")
        return dest


@contextmanager
def start(run_file: str, params: ModuleType, argv: list[str] | None = None) -> Iterator[Run]:
    """Parse the flags, write out/params_used.json, and complete it when the run ends."""
    parser = argparse.ArgumentParser(description="Run this experiment (AGENTS.md, Experiments).")
    parser.add_argument("--smoke", action="store_true", help="apply params.SMOKE, write to out/smoke/, never promote")
    parser.add_argument("--overwrite", action="store_true", help="replace a completed full run in out/")
    args = parser.parse_args(argv)

    exp_dir = Path(run_file).resolve().parent
    out_dir = exp_dir / "out" / "smoke" if args.smoke else exp_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    record_path = out_dir / RECORD
    if record_path.is_file():
        previous = json.loads(record_path.read_text(encoding="utf-8"))
        assert args.smoke or args.overwrite or previous.get("status") != "completed", (
            f"{_relative(out_dir)} holds a completed run from {previous.get('started')}: "
            "pass --overwrite to replace it, or start a new experiment to keep it"
        )
        if previous.get("status") == "running":
            # A killed run (SIGKILL, out of memory) never records its end, so this does not block.
            print(f"[{exp_dir.name}] note: the run started {previous.get('started')} never finished; "
                  "if it is still running, stop this one", flush=True)

    values = dict(params.PARAMS)
    if args.smoke:
        assert hasattr(params, "SMOKE"), "--smoke needs params.SMOKE (the small values for a smoke run)"
        unknown = sorted(set(params.SMOKE) - set(values))
        assert not unknown, f"params.SMOKE keys missing from params.PARAMS: {unknown}"
        values.update(params.SMOKE)

    lock = config.PROJECT_ROOT / "uv.lock"
    record = {
        "experiment": exp_dir.name,
        "status": "running",
        "smoke": args.smoke,
        "argv": sys.argv[1:] if argv is None else list(argv),
        "started": _now(),
        "seed": params.SEED,
        "params": values,
        "git": git_state([*CODE_PATHS, f"{_relative(exp_dir)}/*.py"]),
        "python": platform.python_version(),
        "uv_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest() if lock.is_file() else None,
        "stages": [],
        "promoted": [],
    }
    _write(record_path, record)
    run = Run(exp_dir.name, out_dir, args.smoke, params.SEED, values, record)
    print(f"[{exp_dir.name}] {'smoke' if args.smoke else 'full'} run -> {_relative(out_dir)}", flush=True)
    if record["git"]["dirty"]:
        run.log(f"uncommitted code is recorded, and this run cannot promote: {record['git']['dirty']}")
    try:
        yield run
    except BaseException:
        record["status"], record["error"] = "failed", traceback.format_exc()
        raise
    else:
        record["status"] = "completed"
    finally:
        record["finished"], record["elapsed_s"] = _now(), round(run.elapsed(), 3)
        _write(record_path, record)
        print(f"[{exp_dir.name}] {record['status']} in {record['elapsed_s']:.1f} s", flush=True)
