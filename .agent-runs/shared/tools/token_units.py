"""Sum token usage from Claude Code transcripts (deduplicated per message id).

units = input + 1.25*cache_creation + 0.1*cache_read + 5*output  (input-token equivalents)
usage: token_units.py <jsonl>... ; prints per file and the total; --since ISO limits entries.
"""

import argparse
import collections
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcripts", type=Path, nargs="*")
    parser.add_argument("--since", metavar="ISO", help="include only entries at or after this timestamp")
    args = parser.parse_args()
    grand = collections.Counter()
    for path in args.transcripts:
        total = collections.Counter()
        seen = set()
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if args.since and (row.get("timestamp") or "") < args.since:
                    continue
                message = row.get("message") or {}
                usage, mid = message.get("usage"), message.get("id")
                if not usage or mid in seen:
                    continue
                seen.add(mid)
                for key in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"):
                    total[key] += usage.get(key) or 0
        units = (total["input_tokens"] + 1.25 * total["cache_creation_input_tokens"]
                 + 0.1 * total["cache_read_input_tokens"] + 5 * total["output_tokens"])
        total["units"] = units
        grand.update(total)
        if len(args.transcripts) <= 12:
            print(f"{path.name[:40]:40s} units={units/1e6:7.2f}M "
                  f"read={total['cache_read_input_tokens']/1e6:7.1f}M "
                  f"create={total['cache_creation_input_tokens']/1e6:5.2f}M out={total['output_tokens']}")
    print(f"TOTAL units={grand['units']/1e6:.2f}M read={grand['cache_read_input_tokens']/1e6:.1f}M "
          f"create={grand['cache_creation_input_tokens']/1e6:.2f}M "
          f"out={grand['output_tokens']} files={len(args.transcripts)}")


if __name__ == "__main__":
    main()
