"""Create experiments/NNN_<slug>/ from experiments/_template and add its index row.

    make experiment SLUG=<slug>
    docker compose exec research-template uv run python scripts/new_experiment.py <slug>

The number is the highest one used by a directory or an index row, plus one.
"""

import argparse
import datetime
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z0-9]+(?:_[a-z0-9]+)*")
INDEX_ROW = re.compile(r"^\|\s*([0-9]{3})\s*\|")
# Template files whose NNN_<slug> and YYYY-MM-DD placeholders are filled in.
FILLED = ("summary.md", "README.md", "run.py", "params.py")


def next_number(experiments: Path) -> int:
    used = [int(path.name[:3]) for path in experiments.iterdir() if path.is_dir() and re.match(r"[0-9]{3}_", path.name)]
    index = (experiments / "EXP_SUMMARY.md").read_text(encoding="utf-8").splitlines()
    used += [int(match.group(1)) for match in map(INDEX_ROW.match, index) if match]
    return max(used, default=0) + 1


def add_index_row(index: Path, number: int, slug: str) -> None:
    lines = index.read_text(encoding="utf-8").splitlines()
    header = next((i for i, line in enumerate(lines) if re.match(r"^\|\s*#\s*\|\s*slug\s*\|", line)), None)
    assert header is not None, f"{index}: no table header starting | # | slug |"
    end = header + 2  # past the header and its separator row
    while end < len(lines) and INDEX_ROW.match(lines[end]):
        end += 1
    lines.insert(end, f"| {number:03d} | {slug} | (実行前) | 進行中 |")
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")


def create(root: Path, slug: str, today: datetime.date) -> Path:
    assert SLUG.fullmatch(slug) and len(slug) <= 40, f"Slug must be lower_snake_case ASCII, at most 40 characters: {slug!r}"
    experiments = root / "experiments"
    clash = sorted(path.name for path in experiments.glob(f"[0-9][0-9][0-9]_{slug}"))
    assert not clash, f"Slug already used: {clash}"
    number = next_number(experiments)
    assert number <= 999, "Experiment numbers have three digits"
    target = experiments / f"{number:03d}_{slug}"
    shutil.copytree(experiments / "_template", target, ignore=shutil.ignore_patterns("__pycache__", "out"))
    (target / "out").mkdir()
    (target / "out" / ".gitkeep").touch()
    for name in FILLED:
        path = target / name
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("NNN_<slug>", target.name).replace("YYYY-MM-DD", today.isoformat()), encoding="utf-8")
    add_index_row(experiments / "EXP_SUMMARY.md", number, slug)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug", help="lower_snake_case, e.g. baseline_fit")
    # The container clock is UTC; make passes the host's local date.
    parser.add_argument("--date", type=datetime.date.fromisoformat, default=datetime.date.today(),
                        help="date written into the new files, YYYY-MM-DD (default: today in the container)")
    args = parser.parse_args()
    target = create(ROOT, args.slug, args.date)
    print(f"Created {target.relative_to(ROOT)} and its index row.")
    print("Next: write 問い and 判定の規則 in summary.md, set params.py, commit both, then run --smoke.")


if __name__ == "__main__":
    main()
