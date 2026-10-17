"""Export one Claude Code workflow run into the shared ledger.

Writes <ledger>/runs/<run>/: journal.jsonl (copy), results.json (label -> the last
result of that label), stages.jsonl (one line per agent: label, phase, status, agent id,
transcript path, input-token equivalents, and for Codex stages the stage directory and the
Codex session transcript), and script.js when the script file is given. Rerun it after the
workflow ends or is stopped; it overwrites only these files. Standard library only.
Malformed journal lines are skipped; explicit failures, null results, and failed Codex
reports are recorded as failed stages. Weekly percentages select the 10080-minute window
from either rate-limit slot and include its window_minutes.

usage: python3 export_workflow_run.py <journal.jsonl> [--run NAME] [--script FILE]
                                      [--ledger DIR] [--codex-root DIR] [--stages-dir DIR ...]
<run> defaults to the workflow run id (the journal's directory name); pass --run to file it
under the ledger run name recorded in that run's manifest.json.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

_HERE = Path(__file__).resolve()
# <ledger>/shared/tools/<tool>.py; fall back to ./.agent-runs when the tool is run from elsewhere.
DEFAULT_LEDGER = _HERE.parents[2] if len(_HERE.parents) > 2 else Path.cwd() / ".agent-runs"
HOME = Path.home()
CODEX_ROOT = HOME / ".codex" / "sessions"


def units(transcript: Path) -> float | None:
    """input + 1.25 cache creation + 0.1 cache read + 5 output, once per message id."""
    if not transcript.exists():
        return None
    seen, total = set(), 0.0
    for line in transcript.open(encoding="utf-8", errors="replace"):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = row.get("message") or {}
        usage, mid = message.get("usage"), message.get("id")
        if not usage or mid in seen:
            continue
        seen.add(mid)
        total += (usage.get("input_tokens") or 0) + 1.25 * (usage.get("cache_creation_input_tokens") or 0) \
            + 0.1 * (usage.get("cache_read_input_tokens") or 0) + 5 * (usage.get("output_tokens") or 0)
    return round(total)


def codex_session_for(stage_dir: Path) -> dict:
    """Find the Codex session of a stage from its events.jsonl (thread.started) and its usage."""
    events = stage_dir / "events.jsonl"
    thread, usage = None, None
    if events.exists():
        with events.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "thread.started":
                    thread = event.get("thread_id")
                if event.get("type") == "turn.completed":
                    usage = event.get("usage")
    rollout = None
    if thread:
        hits = sorted(CODEX_ROOT.glob(f"*/*/*/rollout-*{thread}.jsonl"))
        rollout = str(hits[0]) if hits else None
    percents = []
    if rollout:
        with open(rollout, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if '"token_count"' not in line:
                    continue
                try:
                    payload = json.loads(line).get("payload") or {}
                except json.JSONDecodeError:
                    continue
                if payload.get("type") != "token_count":
                    continue
                limits = payload.get("rate_limits") or {}
                for name in ("primary", "secondary"):
                    window = limits.get(name) or {}
                    if window.get("window_minutes") == 10080 and window.get("used_percent") is not None:
                        percents.append(window["used_percent"])
                        break
    return {"stage_dir": str(stage_dir), "thread_id": thread, "codex_transcript": rollout, "usage": usage,
            "window_minutes": 10080 if percents else None,
            "weekly_percent_first_last": [percents[0], percents[-1]] if percents else None}


def main() -> None:
    global CODEX_ROOT
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("journal", type=Path)
    parser.add_argument("--script", type=Path)
    parser.add_argument("--stages-dir", type=Path, action="append", default=[],
                        help="directories holding Codex stage directories (<key>-cx-<role>)")
    parser.add_argument("--run", help="ledger run name (default: the workflow run id)")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--codex-root", type=Path, default=CODEX_ROOT)
    args = parser.parse_args()
    CODEX_ROOT = args.codex_root
    out = args.ledger / "runs" / (args.run or args.journal.parent.name)
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.journal, out / "journal.jsonl")
    if args.script:
        shutil.copyfile(args.script, out / "script.js")
    rows = []
    with args.journal.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    started = {}
    results, stages = {}, []
    for row in rows:
        if row.get("type") == "started":
            started[row["agentId"]] = row
        elif row.get("type") in ("result", "failed"):
            begin = started.get(row.get("agentId"), {})
            label = begin.get("label")
            transcript = args.journal.parent / f"agent-{row.get('agentId')}.jsonl"
            result = row.get("result")
            status = result.get("codex_status") if isinstance(result, dict) else None
            failed = row["type"] == "failed" or result is None or (
                isinstance(status, str) and status.startswith("failed"))
            entry = {"label": label, "phase": begin.get("phase"), "status": "failed" if failed else "result",
                     "agent_id": row.get("agentId"),
                     "transcript": str(transcript), "units": units(transcript)}
            if row["type"] == "result":
                results[label] = result
            # Failed reports may still identify a stage; older/null reports need the directory fallback.
            match = re.search(r"\bstage ([^;]+);", status) if isinstance(status, str) else None
            dirs = [Path(match.group(1).strip())] if match else [
                d for base in args.stages_dir for d in sorted(base.glob(f"{(label or '').split(':')[-1]}-cx*"))]
            if status is not None or dirs:
                entry["codex"] = [codex_session_for(d) for d in dirs]
            stages.append(entry)
    (out / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    with (out / "stages.jsonl").open("w", encoding="utf-8") as handle:
        for entry in stages:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"{out}: {len(results)} results, {len(stages)} finished agents")


if __name__ == "__main__":
    main()
