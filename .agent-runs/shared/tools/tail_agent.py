"""Show the last message and tool entries in a Claude Code agent transcript."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("count", type=int, nargs="?", default=25, help="number of entries (default: 25)")
    args = parser.parse_args()
    out = []
    with args.transcript.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = row.get("message") or {}
            content = message.get("content")
            if not isinstance(content, list):
                if isinstance(content, str):
                    out.append((row.get("type"), content[:600]))
                continue
            for part in content:
                kind = part.get("type")
                if kind == "text":
                    out.append(("TEXT", part["text"][:1200]))
                elif kind == "tool_use":
                    out.append(("TOOL", json.dumps(part.get("input"), ensure_ascii=False)[:400]))
                elif kind == "tool_result":
                    value = part.get("content")
                    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
                    out.append(("RES", text[:300]))
    for kind, text in out[-args.count:]:
        print("--", kind, text)


if __name__ == "__main__":
    main()
