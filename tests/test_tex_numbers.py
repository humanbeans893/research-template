"""Checks the manuscript numbers generated from result/tables/*.csv (src/utils/tex_numbers.py).

Expected values are worked out by hand. The last test fails when the committed
draft/tables/numbers.tex differs from what the CSVs give now.
"""

import pytest

import config
from scripts import make_numbers
from src.utils.tex_numbers import Number, format_value, read_cell, render


@pytest.mark.parametrize(("raw", "rounding", "expected"), [
    ("218.000000", "int", "218"),
    ("0.688073", "pct1", "68.8"),
    ("0.1", "dec3", "0.100"),
    ("-0.302420", "dec3", r"\ensuremath{-}0.302"),
    ("1234567.4", "dec0", "1{,}234{,}567"),
    ("2.5e-3", "dec4", "0.0025"),
    ("a_b & 5%", "text", r"a\_b \& 5\%"),
])
def test_values_are_shown_as_worked_out_by_hand(raw: str, rounding: str, expected: str) -> None:
    assert format_value(raw, rounding) == expected


def test_exact_halves_round_up_not_to_even() -> None:
    # In binary floating point round(2.675, 2) == 2.67.
    assert format_value("2.675", "dec2", exact=True) == "2.68"
    assert format_value("0.5625", "pct1", exact=True) == "56.3"


@pytest.mark.parametrize(("raw", "rounding"), [
    ("0.167500", "pct1"),  # exactly halfway: the CSV may already have rounded it
    ("5322.5", "int"),
    ("-0.0004", "dec3"),  # would show as -0
    ("nan", "dec1"),
    ("", "dec1"),
    ("0.5", "pct"),
])
def test_ambiguous_or_invalid_values_are_refused(raw: str, rounding: str) -> None:
    with pytest.raises(AssertionError):
        format_value(raw, rounding)


@pytest.mark.parametrize(("name", "where", "column"), [
    ("toy.csv", {"key": "x"}, "value"),  # no row
    ("toy.csv", {"key": "a"}, "value"),  # two rows
    ("toy.csv", {"key": "b"}, "absent"),  # no such column
    ("toy.csv", {"key": "c"}, "value"),  # empty cell
    ("../toy.csv", {"key": "b"}, "value"),  # outside the table directory
    ("none.csv", {}, "value"),  # no such file
])
def test_missing_ambiguous_or_outside_sources_are_refused(tmp_path, name: str, where: dict, column: str) -> None:
    tables = tmp_path / "tables"
    tables.mkdir()
    (tables / "toy.csv").write_text("key,value\na,1\na,2\nb,3\nc,\n", encoding="utf-8")
    (tmp_path / "toy.csv").write_text("key,value\nb,3\n", encoding="utf-8")
    with pytest.raises(AssertionError):
        read_cell(Number("Toy", name, where, column, "int"), tables)


def test_render_names_each_source(tmp_path) -> None:
    (tmp_path / "toy.csv").write_text("key,value\nb,3\n", encoding="utf-8")
    text = render([Number("Toy", "toy.csv", {"key": "b"}, "value", "int")], tmp_path)
    assert text.splitlines()[1:] == ["% toy.csv [key=b] value, int", r"\newcommand{\Toy}{3}"]
    with pytest.raises(AssertionError, match="unique"):
        render([Number("Toy", "toy.csv", {"key": "b"}, "value", "int")] * 2, tmp_path)


def test_committed_numbers_are_what_the_csvs_give() -> None:
    assert make_numbers.OUTPUT.is_file(), "draft/tables/numbers.tex is missing: run make numbers"
    assert make_numbers.OUTPUT.read_text(encoding="utf-8") == render(make_numbers.NUMBERS, config.TABLE_DIR), (
        "draft/tables/numbers.tex is stale or was edited by hand: run make numbers and commit it"
    )


def test_a_csv_with_a_byte_order_mark_is_read(tmp_path) -> None:
    # Excel's "CSV UTF-8" and pandas' encoding="utf-8-sig" start the file with a BOM.
    (tmp_path / "bom.csv").write_text("key,value\nb,3\n", encoding="utf-8-sig")
    assert read_cell(Number("Bom", "bom.csv", {"key": "b"}, "value", "int"), tmp_path) == "3"
