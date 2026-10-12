"""Manuscript numbers as LaTeX macros generated from result/tables/*.csv (AGENTS.md, Generated Outputs).

Each Number names one cell of one CSV and how to show it, and the generated file
keeps that source as a comment above the macro. Rounding is half-up in decimal,
from the text in the CSV: in binary floating point round(2.675, 2) is 2.67. A
value exactly halfway at the shown digit is refused unless the Number is marked
exact, because a CSV written with fixed decimals may already have rounded it.
"""

import csv
import re
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

MACRO_NAME = re.compile(r"[A-Za-z]+")
ROUNDING = re.compile(r"int|text|(dec|pct)([0-9])")
NUMBER = re.compile(r"-?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?")
MINUS = r"\ensuremath{-}"  # the same minus sign in running text and in math
THOUSANDS = "{,}"  # the thousands separator; set "" if the journal uses none
TEX_SPECIALS = {
    "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "$": r"\$", "&": r"\&", "%": r"\%",
    "#": r"\#", "_": r"\_", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}
HEADER = "% Generated from result/tables/*.csv by scripts/make_numbers.py (make numbers). Do not edit by hand."


@dataclass(frozen=True)
class Number:
    """Column `column` of the one row of result/tables/<csv> that matches `where`.

    rounding: "int" (must be integral), "decN" (N decimals), "pctN" (a fraction
    times 100 with N decimals, no % sign) or "text" (escaped, not rounded).
    exact: the CSV value is not itself rounded (a count, k/n), so an exact half
    rounds up instead of being refused.
    """

    macro: str
    csv: str
    where: dict = field(hash=False)
    column: str
    rounding: str
    exact: bool = False


def read_cell(number: Number, table_dir: Path) -> str:
    path = (table_dir / number.csv).resolve()
    assert path.is_relative_to(table_dir.resolve()), f"{number.macro}: {number.csv} is outside {table_dir}"
    assert path.is_file(), f"{number.macro}: {path} is missing; run the analysis that writes it"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        absent = [name for name in (*number.where, number.column) if name not in (reader.fieldnames or [])]
        assert not absent, f"{number.macro}: {number.csv} has no column {absent}"
        rows = [row for row in reader if all(row[key] == value for key, value in number.where.items())]
    assert len(rows) == 1, f"{number.macro}: {number.where} matches {len(rows)} rows of {number.csv}; need exactly one"
    value = rows[0][number.column]
    assert value != "", f"{number.macro}: {number.csv} {number.where} {number.column} is empty"
    return value


def format_value(raw: str, rounding: str, *, exact: bool = False) -> str:
    match = ROUNDING.fullmatch(rounding)
    assert match, f"Unknown rounding {rounding!r}: int, decN, pctN or text"
    if rounding == "text":
        return "".join(TEX_SPECIALS.get(char, char) for char in raw)
    assert NUMBER.fullmatch(raw.strip()), f"Not a finite number: {raw!r}"
    value = Decimal(raw.strip())
    assert rounding != "int" or value == value.to_integral_value(), f"{raw!r} is not an integer"
    digits = 0 if rounding == "int" else int(match.group(2))
    if match.group(1) == "pct":
        value *= 100
    halfway = (value.scaleb(digits) % 1).copy_abs() == Decimal("0.5")
    assert exact or not halfway, (
        f"{raw!r} is exactly halfway at {digits} decimals: write the CSV at full precision, or mark the Number exact"
    )
    rounded = value.quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
    assert not (rounded.is_zero() and value < 0), f"{raw!r} would be shown as -0: show more decimals"
    integer, point, fraction = f"{abs(rounded):f}".partition(".")
    return (MINUS if rounded < 0 else "") + f"{int(integer):,}".replace(",", THOUSANDS) + point + fraction


def render(numbers: list[Number], table_dir: Path) -> str:
    names = [number.macro for number in numbers]
    bad = sorted({name for name in names if not MACRO_NAME.fullmatch(name) or names.count(name) > 1})
    assert not bad, f"Macro names must be letters only and unique: {bad}"
    lines = [HEADER]
    for number in numbers:
        where = ";".join(f"{key}={value}" for key, value in number.where.items())
        value = format_value(read_cell(number, table_dir), number.rounding, exact=number.exact)
        lines += [f"% {number.csv} [{where}] {number.column}, {number.rounding}", f"\\newcommand{{\\{number.macro}}}{{{value}}}"]
    return "\n".join(lines) + "\n"


def write(numbers: list[Number], table_dir: Path, path: Path) -> bool:
    """Write path only when its content changes; return whether it did."""
    content = render(numbers, table_dir)
    if path.is_file() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True
