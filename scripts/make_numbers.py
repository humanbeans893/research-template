r"""Write draft/tables/numbers.tex, every number the manuscript quotes, from result/tables/*.csv.

    make numbers
    docker compose exec research-template uv run python scripts/make_numbers.py

Register each number the text quotes as a Number below, run this, write \Name{}
in the text, and commit draft/tables/numbers.tex together with the CSVs it reads:
draft/compile.sh runs on the host, without Python. tests/test_tex_numbers.py fails
when the committed file is stale or was edited by hand.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from src.utils.tex_numbers import Number, write

OUTPUT = config.DRAFT_DIR / "tables" / "numbers.tex"
NUMBERS: list[Number] = [
    # Number("NSubjects", "summary.csv", {"quantity": "n_subjects"}, "value", "int"),
    # Number("EffectPct", "summary.csv", {"quantity": "effect"}, "value", "pct1"),
]


def main() -> None:
    state = "written" if write(NUMBERS, config.TABLE_DIR, OUTPUT) else "unchanged"
    print(f"{OUTPUT.relative_to(config.PROJECT_ROOT)}: {len(NUMBERS)} macros, {state}")


if __name__ == "__main__":
    main()
