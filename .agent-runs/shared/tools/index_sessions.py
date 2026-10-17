"""Index the Claude Code and Codex sessions that worked in this repository.

Both agents keep their own transcripts (Claude Code under ~/.claude/projects, Codex under
~/.codex/sessions). This writes one line per session to <ledger>/sessions.jsonl so that
either agent can find the other's history: engine, id, working directory, first and last
timestamp, the first user request, and the transcript path. Transcripts are referenced, not
copied. Standard library only; read-only on both stores.

A session belongs to the repository when its working directory is under one of the prefixes:
the repository root, its git worktrees (read from .git/worktrees), every line of the optional
local file <ledger>/prefixes.txt, and every --prefix.

usage: python3 index_sessions.py [--ledger DIR] [--repo DIR] [--claude-root DIR]
                                 [--codex-root DIR] [--prefix PATH ...] [--out FILE]
In a repository that forbids host Python, run it in a throwaway container with the stores
mounted read-only and the host paths passed explicitly (see the ledger README).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HOME = Path.home()
_HERE = Path(__file__).resolve()
# <ledger>/shared/tools/<tool>.py; fall back to ./.agent-runs when the tool is run from elsewhere.
DEFAULT_LEDGER = _HERE.parents[2] if len(_HERE.parents) > 2 else Path.cwd() / ".agent-runs"


def first_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") in ("text", "input_text"):
                return part.get("text", "")
    return ""


def repository_prefixes(repo: Path) -> list[str]:
    """The repository root and the paths of its git worktrees."""
    prefixes = [str(repo)]
    worktrees = repo / ".git" / "worktrees"
    if worktrees.is_dir():
        for gitdir in sorted(worktrees.glob("*/gitdir")):
            target = Path(gitdir.read_text(encoding="utf-8").strip())
            prefixes.append(str(target.parent))
    return prefixes


def claude_sessions(root: Path, relevant):
    for path in sorted(root.glob("*/*.jsonl")):
        cwd = start = end = prompt = None
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cwd = cwd or row.get("cwd")
                stamp = row.get("timestamp")
                if stamp:
                    start = start or stamp
                    end = stamp
                if prompt is None and row.get("type") == "user":
                    text = first_text((row.get("message") or {}).get("content"))
                    if text and not text.startswith("<"):
                        prompt = text
        if relevant(cwd):
            workflows = sorted(p.name for p in (path.with_suffix("") / "subagents" / "workflows").glob("wf_*"))
            yield {"engine": "claude-code", "id": path.stem, "cwd": cwd, "start": start, "end": end,
                   "first_request": (prompt or "")[:300], "transcript": str(path), "workflows": workflows}


def codex_sessions(root: Path, relevant):
    for path in sorted(root.glob("*/*/*/rollout-*.jsonl")):
        meta = end = prompt = None
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                payload = row.get("payload") or {}
                if meta is None and row.get("type") == "session_meta":
                    meta = payload
                end = row.get("timestamp") or end
                if prompt is None and payload.get("type") == "message" and payload.get("role") == "user":
                    text = first_text(payload.get("content"))
                    if text and not text.startswith("<") and not text.startswith("# AGENTS.md"):
                        prompt = text
        if meta and relevant(meta.get("cwd")):
            source = meta.get("source")
            yield {"engine": "codex", "id": meta.get("id"), "cwd": meta.get("cwd"), "start": meta.get("timestamp"),
                   "end": end, "source": "guardian" if isinstance(source, dict) else source,
                   "first_request": (prompt or "")[:300], "transcript": str(path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--repo", type=Path, help="repository root as the sessions saw it (default: the ledger's parent)")
    parser.add_argument("--claude-root", type=Path, default=HOME / ".claude" / "projects")
    parser.add_argument("--codex-root", type=Path, default=HOME / ".codex" / "sessions")
    parser.add_argument("--prefix", action="append", default=[], help="extra working-directory prefix (repeatable)")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    repo = args.repo or args.ledger.resolve().parent
    prefixes = repository_prefixes(repo) + list(args.prefix)
    extra = args.ledger / "prefixes.txt"
    if extra.exists():
        prefixes += [line.strip() for line in extra.read_text(encoding="utf-8").splitlines()
                     if line.strip() and not line.startswith("#")]
    prefixes = tuple(dict.fromkeys(prefixes))

    def relevant(cwd):
        return bool(cwd) and cwd.startswith(prefixes)

    rows = sorted([*claude_sessions(args.claude_root, relevant), *codex_sessions(args.codex_root, relevant)],
                  key=lambda r: r.get("start") or "")
    out = args.out or args.ledger / "sessions.jsonl"
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    counts = {}
    for row in rows:
        counts[row["engine"]] = counts.get(row["engine"], 0) + 1
    print(f"{out}: {len(rows)} sessions {counts}; prefixes {list(prefixes)}")


if __name__ == "__main__":
    main()
