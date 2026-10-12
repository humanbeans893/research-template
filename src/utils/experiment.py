"""Run harness for experiments/NNN_<slug>/run.py (AGENTS.md, Experiments).

Every experiment gets the same flags and the same record:

- ``--smoke`` applies ``params.SMOKE``, writes to ``out/smoke/`` and never
  promotes, so a mistake surfaces in seconds and each stage can be timed.
- A completed full run is not replaced without ``--overwrite``. Before a run
  starts, whatever an earlier run left in its output directory is cleared, so
  no stale file sits beside the new outputs.
- ``out/params_used.json`` records the status (running, completed or failed),
  seed, parameters, git commit and the list of uncommitted files, Python,
  uv.lock, stage timings and promoted files.
- SIGTERM and SIGHUP (kill, timeout, a batch scheduler's time limit) end the
  run through SystemExit, so it is recorded as failed. Only SIGKILL and an
  out-of-memory kill leave the status at running.
- One run at a time per output directory: a lock (out/.lock) is held for the
  whole run and released by the kernel however the process ends, so a run
  recorded as running whose lock is free is known to be dead.
- ``run.promote()`` copies an output to result/ only when the run completes,
  so result/ never holds part of a failed run.
"""

import argparse
import fcntl
import hashlib
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

import config

RECORD = "params_used.json"
LOCK = ".lock"
# Code whose uncommitted changes make a run unreproducible, besides the
# experiment's own *.py.
CODE_PATHS = ("src", "config.py", "pyproject.toml", "uv.lock")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _relative(path: Path) -> str:
    path, root = Path(path).resolve(), config.PROJECT_ROOT.resolve()
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def _write(path: Path, record: dict) -> None:
    # Through a temporary file, so that a kill mid-write never leaves a truncated record.
    part = path.with_name(path.name + ".part")
    part.write_text(json.dumps(record, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    os.replace(part, path)


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

    def __init__(self, name: str, out_dir: Path, smoke: bool, seed: int, params: dict, record: dict,
                 git_paths: list[str]) -> None:
        self.name, self.out_dir, self.smoke, self._git_paths = name, out_dir, smoke, git_paths
        self.seed, self.params, self.record = seed, params, record
        self._start = time.perf_counter()
        self._staged: list[tuple[Path, Path]] = []

    def elapsed(self) -> float:
        return time.perf_counter() - self._start

    def stage(self, title: str) -> None:
        """Start a stage: printed at once and timed in the record."""
        stages = self.record["stages"]
        stages.append({"title": title, "start_s": round(self.elapsed(), 3)})
        print(f"[{self.name}] {len(stages)}. {title} (t = {self.elapsed():.1f} s)", flush=True)

    def log(self, text: str) -> None:
        print(f"    {text} ({self.elapsed():.1f} s)", flush=True)

    def _inside(self, name: str) -> Path:
        path, out_dir = (self.out_dir / name).resolve(), self.out_dir.resolve()
        assert path != out_dir and path.is_relative_to(out_dir), f"{name!r} is not a file under {_relative(out_dir)}"
        return path

    def out(self, name: str) -> Path:
        """Path for an output under out/ (out/smoke/ with --smoke); a name that leaves it is refused."""
        path = self._inside(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def promote(self, name: str, dest_dir: Path = config.TABLE_DIR) -> Path:
        """Copy an output to result/ (tables by default) when the run completes.

        The arguments are checked now; nothing is copied if the run fails, so result/
        never holds part of a failed run.
        """
        assert not self.smoke, "--smoke never writes to result/"
        dirty = self.record["git"]["dirty"]
        assert not dirty, f"Commit these, rerun, then promote: {dirty}"
        source = self._inside(name)
        assert source.is_file(), f"{_relative(source)} does not exist: write it through run.out() first"
        dest = Path(dest_dir) / Path(name).name
        assert not dest.is_dir(), f"{_relative(dest)} is a directory"
        assert dest not in [staged for _, staged in self._staged], f"{_relative(dest)} is promoted twice"
        self._staged.append((source, dest))
        return dest

    def _publish(self) -> None:
        """Put the promoted outputs in place, all or none.

        The code must still be what the run started from. Every file is copied to a
        temporary name first; if a replacement then fails, the old files come back.
        """
        if not self._staged:
            return
        now = git_state(self._git_paths)
        assert now == self.record["git"], f"The code changed during the run (now {now}): commit, rerun, then promote"
        parts, replaced = [], []
        try:
            for source, dest in self._staged:
                dest.parent.mkdir(parents=True, exist_ok=True)
                assert not dest.is_dir(), f"{_relative(dest)} is a directory"
                # Names of this process only, so that two runs promoting at once never
                # take over each other's temporary files.
                part = dest.with_name(f".{dest.name}.{os.getpid()}.part")
                shutil.copyfile(source, part)
                parts.append((part, dest))
            for part, dest in parts:
                backup = dest.with_name(f".{dest.name}.{os.getpid()}.previous") if dest.exists() else None
                if backup is not None:
                    os.replace(dest, backup)
                replaced.append((dest, backup))
                os.replace(part, dest)
        except BaseException:
            for dest, backup in reversed(replaced):
                if backup is not None:
                    os.replace(backup, dest)
                else:
                    dest.unlink(missing_ok=True)
            for part, _ in parts:
                part.unlink(missing_ok=True)
            raise
        for dest, backup in replaced:
            if backup is not None:
                backup.unlink()
            self.record["promoted"].append(_relative(dest))
            self.log(f"promoted -> {_relative(dest)}")


@contextmanager
def start(run_file: str, params: ModuleType, argv: list[str] | None = None) -> Iterator[Run]:
    """Parse the flags, hold the output directory's lock, and keep out/params_used.json up to date."""
    parser = argparse.ArgumentParser(description="Run this experiment (AGENTS.md, Experiments).")
    parser.add_argument("--smoke", action="store_true", help="apply params.SMOKE, write to out/smoke/, never promote")
    parser.add_argument("--overwrite", action="store_true", help="replace a completed run; out/ is cleared first")
    args = parser.parse_args(argv)

    exp_dir = Path(run_file).resolve().parent
    out_dir = exp_dir / "out" / "smoke" if args.smoke else exp_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    # One run at a time per output directory. The kernel releases the lock when
    # the process ends, however it ends, so a free lock means no run is alive here.
    with open(out_dir / LOCK, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise AssertionError(f"Another run is using {_relative(out_dir)}: wait for it to finish") from None
        yield from _run(args, argv, exp_dir, out_dir, params)


def _run(args: argparse.Namespace, argv: list[str] | None, exp_dir: Path, out_dir: Path,
         params: ModuleType) -> Iterator[Run]:
    record_path = out_dir / RECORD
    previous = {}
    if record_path.is_file():
        try:
            previous = json.loads(record_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            assert args.overwrite, f"{_relative(record_path)} is unreadable: if its run died, pass --overwrite"
            previous = {"status": "unreadable"}
    # What an earlier run left here. A full run leaves out/smoke/ to the smoke runs.
    keep = {".gitkeep", LOCK} if args.smoke else {".gitkeep", LOCK, "smoke"}
    leftovers = sorted(p for p in out_dir.iterdir() if p.name not in keep)
    if not (args.smoke or args.overwrite):
        assert previous.get("status") != "completed", (
            f"{_relative(out_dir)} holds a completed run from {previous.get('started')}: "
            "pass --overwrite to replace it, or start a new experiment to keep it"
        )
        assert previous or not leftovers, (
            f"{_relative(out_dir)} holds files that no recorded run wrote: {[p.name for p in leftovers]}; "
            "pass --overwrite to replace them"
        )
    if previous.get("status") == "running":
        # We hold the lock, so that run is not alive: SIGKILL or out of memory ended it.
        print(f"[{exp_dir.name}] note: the run started {previous.get('started')} died without recording "
              "its end (killed, out of memory); its outputs are cleared", flush=True)

    values = dict(params.PARAMS)
    if args.smoke:
        assert hasattr(params, "SMOKE"), "--smoke needs params.SMOKE (the small values for a smoke run)"
        unknown = sorted(set(params.SMOKE) - set(values))
        assert not unknown, f"params.SMOKE keys missing from params.PARAMS: {unknown}"
        values.update(params.SMOKE)

    # Clear the earlier run, so that no stale output sits beside the new ones and
    # gets cited or promoted as if this run had written it.
    for path in leftovers:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()
    if leftovers:
        print(f"[{exp_dir.name}] cleared {len(leftovers)} entries left in {_relative(out_dir)} by the earlier run", flush=True)

    git_paths = [*CODE_PATHS, f"{_relative(exp_dir)}/*.py"]
    uv_lock = config.PROJECT_ROOT / "uv.lock"
    record = {
        "experiment": exp_dir.name,
        "status": "running",
        "smoke": args.smoke,
        "argv": sys.argv[1:] if argv is None else list(argv),
        "started": _now(),
        "seed": params.SEED,
        "params": values,
        "git": git_state(git_paths),
        "python": platform.python_version(),
        "uv_lock_sha256": hashlib.sha256(uv_lock.read_bytes()).hexdigest() if uv_lock.is_file() else None,
        "stages": [],
        "promoted": [],
    }
    _write(record_path, record)
    run = Run(exp_dir.name, out_dir, args.smoke, params.SEED, values, record, git_paths)
    print(f"[{exp_dir.name}] {'smoke' if args.smoke else 'full'} run -> {_relative(out_dir)}", flush=True)
    if record["git"]["dirty"]:
        run.log(f"uncommitted files are listed in the record, and this run cannot promote: {record['git']['dirty']}")
    # Turn SIGTERM and SIGHUP into SystemExit, so that a stopped run is recorded as failed.
    previous_handlers = {}
    if threading.current_thread() is threading.main_thread():
        for signum in (signal.SIGTERM, signal.SIGHUP):
            previous_handlers[signum] = signal.signal(signum, lambda number, frame: sys.exit(128 + number))
    try:
        yield run
        run._publish()
    except BaseException:
        record["status"], record["error"] = "failed", traceback.format_exc()
        raise
    else:
        record["status"] = "completed"
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
        record["finished"], record["elapsed_s"] = _now(), round(run.elapsed(), 3)
        _write(record_path, record)
        print(f"[{exp_dir.name}] {record['status']} in {record['elapsed_s']:.1f} s", flush=True)
