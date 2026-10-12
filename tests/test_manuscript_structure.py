"""Checks that citations, cross-references and input files in the manuscript resolve.

Only structure that would silently break the PDF is checked. Headings, word
counts, wording and claims are deliberately not pinned: the authors check the
text, and general TeX syntax is left to draft/compile.sh.
"""

import re
from pathlib import Path

import pytest

DRAFT = Path(__file__).resolve().parents[1] / "draft"
DOCUMENTS = ("main.tex", "supplementary.tex")
INPUT = re.compile(r"\\(?:input|include)\{([^{}]+)\}")
# Every natbib/biblatex command with "cite" or "Cite" in its name takes keys,
# except natbib's \citetext (free text) and the style setters \citestyle and
# \setcitestyle.
CITE = re.compile(
    r"\\(?!(?:citetext|citestyle|setcitestyle)(?![a-zA-Z]))"
    r"(?:[a-zA-Z]*[cC]ite[a-zA-Z]*|nocite)\*?(?:\s*\[[^\]]*\]){0,2}\s*\{([^{}]+)\}"
)
GRAPHICSPATH = re.compile(r"\\graphicspath\s*\{((?:\s*\{[^{}]*\})+)\s*\}")
FIGURE_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".mps", ".jbig2", ".jb2")


def _without_comments(text: str) -> str:
    return re.sub(r"(?<!\\)%[^\n]*", "", text)


def _tex_file(name: str) -> Path:
    # TeX resolves \input relative to the directory it runs in (draft/).
    path = DRAFT / name
    return path if path.suffix else path.with_suffix(".tex")


def _read(path: Path) -> str:
    """Return the source as TeX reads it: comments removed, existing \\input files expanded.

    An \\input whose file is missing stays in the text, so the input check finds it.
    """
    assert path.is_file(), f"Missing manuscript file: {path}"
    text = _without_comments(path.read_text(encoding="utf-8"))

    def expand(match: re.Match) -> str:
        target = _tex_file(match.group(1))
        return _read(target) if target.is_file() else match.group(0)

    return INPUT.sub(expand, text)


@pytest.fixture(scope="module", params=DOCUMENTS)
def document(request) -> tuple[str, str]:
    return request.param, _read(DRAFT / request.param)


def test_citations_resolve_in_the_declared_bibliography(document) -> None:
    name, text = document
    keys = []
    declarations = re.findall(r"\\bibliography\{([^{}]+)\}", text) + re.findall(r"\\addbibresource\{([^{}]+)\}", text)
    for declaration in declarations:
        for entry in declaration.split(","):
            bibliography = DRAFT / entry.strip()
            if not bibliography.suffix:
                bibliography = bibliography.with_suffix(".bib")
            assert bibliography.is_file(), f"{name}: missing bibliography {bibliography}"
            keys.extend(re.findall(r"@(?!(?:comment|string|preamble)\b)\w+\s*\{\s*([^,\s]+)",
                                   bibliography.read_text(encoding="utf-8"), flags=re.IGNORECASE))
    assert len(keys) == len(set(keys)), f"{name}: duplicate bibliography keys"
    cited = {key.strip() for group in CITE.findall(text) for key in group.split(",")}
    missing = cited - set(keys) - {"*"}
    assert not missing, f"{name}: cited keys not in the bibliography {sorted(missing)}"


def test_references_resolve_within_each_document(document) -> None:
    name, text = document
    labels = re.findall(r"\\label\{([^{}]+)\}", text)
    assert len(labels) == len(set(labels)), f"{name}: duplicate labels"
    references = {
        label.strip()
        for group in re.findall(r"\\(?:ref|eqref|pageref|autoref|nameref|cref|Cref)\*?\{([^{}]+)\}", text)
        for label in group.split(",")
    }
    missing = references - set(labels)
    assert not missing, f"{name}: references to labels not defined in this document {sorted(missing)}"


def test_input_and_figure_files_exist(document) -> None:
    name, text = document
    missing_inputs = INPUT.findall(text)
    assert not missing_inputs, f"{name}: missing input files {missing_inputs}"
    # graphicx looks in draft/ and in every directory named by \graphicspath{{a/}{b/}}.
    directories = [DRAFT] + [
        DRAFT / directory for group in GRAPHICSPATH.findall(text) for directory in re.findall(r"\{([^{}]*)\}", group)
    ]
    extensions = FIGURE_EXTENSIONS + tuple(extension.upper() for extension in FIGURE_EXTENSIONS)
    for figure in re.findall(r"\\includegraphics\*?(?:\[[^\]]*\])?\{([^{}]+)\}", text):
        names = [figure] if Path(figure).suffix else [figure + extension for extension in extensions]
        assert any((directory / name_).is_file() for directory in directories for name_ in names), (
            f"{name}: missing figure {figure}"
        )


@pytest.mark.parametrize(("source", "keys"), [
    (r"\citep[see][p.~5]{b,c}", ["b,c"]),
    (r"\Citet{a}", ["a"]),
    (r"\nocite{*}", ["*"]),
    (r"\setcitestyle{square,numbers}", []),
    (r"\citestyle{nature}", []),
    (r"\citetext{free text}", []),
])
def test_citation_commands_are_recognised(source: str, keys: list[str]) -> None:
    assert CITE.findall(source) == keys
