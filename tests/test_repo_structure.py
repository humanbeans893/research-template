"""Checks the handoff structure that lets Claude Code and Codex resume from files alone.

See AGENTS.md (Session State and Handoff, Experiments). Only what can be enforced
mechanically is checked: the documents exist, the always-read ones stay within their budgets,
every experiment directory is named and numbered once and matches the index, each
has a README.md and a short summary.md whose status word agrees with the index,
experiment outputs stay out of git, and both agents can load the skills.
"""

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = ROOT / "experiments"
HANDOFF_DOCUMENTS = (
    "AGENTS.md",
    "CLAUDE.md",
    "DYNAMIC_WORKFLOW.md",
    ".agent-runs/README.md",
    "STATE.md",
    "experiments/README.md",
    "experiments/EXP_SUMMARY.md",
    "experiments/JOBS.md",
    "docs/guardrails.md",
    "docs/ideas.md",
    "docs/launch-checklist.md",
)
# Character budgets of the files read at the start of every session (AGENTS.md,
# Session State and Handoff). Characters, not lines: long lines defeat a line count.
ALWAYS_READ_BUDGETS = {"STATE.md": 6_000, "experiments/EXP_SUMMARY.md": 15_000, "docs/guardrails.md": 8_000}
INDEX_ROW_MAX_CHARS = 160
# Claude Code reads .claude/skills/, Codex reads .agents/skills/.
SKILL_DIRS = (ROOT / ".claude" / "skills", ROOT / ".agents" / "skills")

# The status words of AGENTS.md (Experiments, Status and Retraction).
STATUSES = ("進行中", "完了", "中止", "訂正", "撤回", "置き換え")
EXPERIMENT_NAME = re.compile(r"[0-9]{3}_[a-z0-9]+(?:_[a-z0-9]+)*")
SUMMARY_MAX_LINES, SUMMARY_MAX_CHARS = 50, 3_000


def test_handoff_documents_exist() -> None:
    missing = [path for path in HANDOFF_DOCUMENTS if not (ROOT / path).is_file()]
    assert not missing, f"Missing handoff documents: {missing}"


def test_claude_md_only_points_at_agents_md() -> None:
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.strip() == "See @AGENTS.md", "CLAUDE.md is a pointer only; write rules in AGENTS.md"


@pytest.mark.parametrize(("relative", "budget"), ALWAYS_READ_BUDGETS.items())
def test_always_read_documents_stay_within_budget(relative: str, budget: int) -> None:
    n_chars = len((ROOT / relative).read_text(encoding="utf-8"))
    assert n_chars <= budget, f"{relative} has {n_chars} characters (budget {budget}): move detail out (AGENTS.md)"


def test_index_rows_stay_one_line_each() -> None:
    text = (EXPERIMENTS / "EXP_SUMMARY.md").read_text(encoding="utf-8")
    long = [line[:20] for line in text.splitlines() if re.match(r"^\|\s*[0-9]+\s*\|", line) and len(line) > INDEX_ROW_MAX_CHARS]
    assert not long, f"Index rows over {INDEX_ROW_MAX_CHARS} characters: {long}; move the detail to that summary.md"


def experiment_dirs() -> list[Path]:
    # Every directory except _template and hidden ones is an experiment.
    return sorted(p for p in EXPERIMENTS.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))


def index_rows() -> list[list[str]]:
    """Cells of each experiment row of experiments/EXP_SUMMARY.md (its one table)."""
    text = (EXPERIMENTS / "EXP_SUMMARY.md").read_text(encoding="utf-8")
    return [
        [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
        for line in text.splitlines()
        if re.match(r"^\|\s*[0-9]+\s*\|", line)
    ]


def indexed_name(row: list[str]) -> str:
    return f"{row[0]}_{row[1].strip('`')}"


def status_word(text: str) -> str | None:
    text = text.strip().lstrip("*")
    return next((word for word in STATUSES if text.startswith(word)), None)


def test_experiments_are_named_numbered_and_indexed_once() -> None:
    names = [path.name for path in experiment_dirs()]
    misnamed = [name for name in names if not EXPERIMENT_NAME.fullmatch(name)]
    assert not misnamed, f"Experiment directories must be NNN_<lower_snake_case_slug>: {misnamed}"
    numbers = [name[:3] for name in names]
    reused = sorted({number for number in numbers if numbers.count(number) > 1})
    assert not reused, f"Experiment numbers used twice: {reused}"
    rows = index_rows()
    short = [row for row in rows if len(row) < 3]
    assert not short, f"Index rows need at least # | slug | ... | status: {short}"
    listed = [indexed_name(row) for row in rows]
    twice = sorted({name for name in listed if listed.count(name) > 1})
    assert not twice, f"experiments/EXP_SUMMARY.md lists these twice: {twice}"
    assert sorted(listed) == names, (
        f"Experiment directories and experiments/EXP_SUMMARY.md rows differ: {sorted(set(listed) ^ set(names))}"
    )


def test_each_experiment_has_a_readme_and_a_short_summary_that_agrees_with_the_index() -> None:
    index_status = {indexed_name(row): row[-1] for row in index_rows() if len(row) >= 3}
    template = (EXPERIMENTS / "_template" / "summary.md").read_text(encoding="utf-8")
    placeholders = sorted(set(re.findall(r"<[^<>\n]+>", template)) - {"<slug>"})
    problems = []
    for path in experiment_dirs():
        name, files = path.name, {child.name for child in path.iterdir()}  # exact case, also on macOS
        problems += [f"{name}: no {file}" for file in ("README.md", "summary.md") if file not in files]
        if "summary.md" not in files:
            continue
        text = (path / "summary.md").read_text(encoding="utf-8")
        n_lines = len(text.splitlines())
        if n_lines > SUMMARY_MAX_LINES or len(text) > SUMMARY_MAX_CHARS:
            problems.append(
                f"{name}/summary.md has {n_lines} lines and {len(text)} characters "
                f"(at most {SUMMARY_MAX_LINES} and {SUMMARY_MAX_CHARS}): move detail to README.md"
            )
        line = re.search(r"^- \*\*状態\*\*:(.*)$", text, re.MULTILINE)
        word = status_word(line.group(1)) if line else None
        if word is None or word != status_word(index_status.get(name, "")):
            problems.append(f"{name}: summary.md 状態 and the index status must start with the same word, one of {STATUSES}")
        left = [placeholder[:16] + "…" for placeholder in placeholders if placeholder in text]
        if word not in (None, "進行中") and left:
            problems.append(f"{name} is {word}, but summary.md still has {len(left)} template placeholders: {left}")
    assert not problems, "\n".join(problems)


def ignored(path: str) -> bool:
    result = subprocess.run(["git", "check-ignore", "-q", "--no-index", path], cwd=ROOT,
                            capture_output=True, text=True, check=False)
    assert result.returncode in (0, 1), f"git check-ignore failed: {result.stderr.strip()}"
    return result.returncode == 0


def test_experiment_outputs_are_git_ignored() -> None:
    # A rename or an edit that misses .gitignore makes every out/ committable, silently.
    assert ignored("experiments/999_probe/out/table.csv"), "experiments/*/out/ is not git-ignored: fix .gitignore"
    assert not ignored("experiments/_template/out/.gitkeep"), "experiments/*/out/.gitkeep must stay tracked"


@pytest.mark.parametrize(("relative", "expected"), [
    ("runs/x", True),
    ("sessions.jsonl", True),
    ("prefixes.txt", True),
    ("notes/estimate.md", True),
    ("shared/codex/common.md", True),
    ("shared/tools/__pycache__/index_sessions.cpython-311.pyc", True),
    ("README.md", False),
    ("shared/tools/index_sessions.py", False),
    ("shared/tools/export_workflow_run.py", False),
    ("shared/tools/token_units.py", False),
    ("shared/tools/tail_agent.py", False),
])
def test_agent_run_records_stay_local_but_guidance_and_tools_can_be_tracked(relative: str, expected: bool) -> None:
    path = f".agent-runs/{relative}"
    assert ignored(path) == expected, f"{path}: expected git-ignored={expected}"


def test_skills_declare_frontmatter() -> None:
    # Codex does not load a skill without YAML frontmatter, and Claude Code needs
    # the description to know when to use one.
    skills = sorted(path for directory in SKILL_DIRS for path in directory.glob("*/SKILL.md"))
    assert skills, "No skills found"
    for path in skills:
        name = path.relative_to(ROOT)
        match = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
        assert match, f"{name} has no YAML frontmatter"
        assert re.search(rf"^name: {re.escape(path.parent.name)}$", match.group(1), re.MULTILINE), (
            f"{name}: frontmatter name must be {path.parent.name}"
        )
        assert re.search(r"^description: \S", match.group(1), re.MULTILINE), f"{name}: no description"


def test_handoff_skill_is_identical_for_both_agents() -> None:
    claude, codex = (directory / "write-handoff" / "SKILL.md" for directory in SKILL_DIRS)
    assert claude.read_text(encoding="utf-8") == codex.read_text(encoding="utf-8"), (
        "Keep .agents/skills/write-handoff/SKILL.md identical to .claude/skills/write-handoff/SKILL.md"
    )
