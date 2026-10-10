"""Checks the handoff structure that lets Claude Code and Codex resume from files alone.

See AGENTS.md (Session State and Handoff). Only what can be enforced mechanically
is checked: the documents exist, the always-read ones stay short, the experiment
index matches the experiment directories, and both agents can load the skills.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HANDOFF_DOCUMENTS = (
    "AGENTS.md",
    "CLAUDE.md",
    "STATE.md",
    "exp/EXP_SUMMARY.md",
    "exp/JOBS.md",
    "docs/guardrails.md",
    "docs/ideas.md",
    "docs/launch-checklist.md",
)
ALWAYS_READ = ("STATE.md", "exp/EXP_SUMMARY.md")
# Claude Code reads .claude/skills/, Codex reads .agents/skills/.
SKILL_DIRS = (ROOT / ".claude" / "skills", ROOT / ".agents" / "skills")


def test_handoff_documents_exist() -> None:
    missing = [path for path in HANDOFF_DOCUMENTS if not (ROOT / path).is_file()]
    assert not missing, f"Missing handoff documents: {missing}"


def test_claude_md_only_points_at_agents_md() -> None:
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.strip() == "See @AGENTS.md", "CLAUDE.md is a pointer only; write rules in AGENTS.md"


@pytest.mark.parametrize("relative", ALWAYS_READ)
def test_always_read_documents_stay_short(relative: str) -> None:
    n_lines = len((ROOT / relative).read_text(encoding="utf-8").splitlines())
    assert n_lines <= 150, f"{relative} has {n_lines} lines; move older material out (AGENTS.md)"


def test_experiments_match_the_index_and_have_readmes() -> None:
    experiments = {
        path.name.split("_", 1)[0]: path
        for path in (ROOT / "exp").iterdir()
        if path.is_dir() and re.match(r"^\d{3}_", path.name)
    }
    index = (ROOT / "exp" / "EXP_SUMMARY.md").read_text(encoding="utf-8")
    listed = set(re.findall(r"^\| (\d{3}) \|", index, re.MULTILINE))
    assert set(experiments) == listed, (
        f"Experiment directories and exp/EXP_SUMMARY.md differ: {sorted(set(experiments) ^ listed)}"
    )
    missing = sorted(path.name for path in experiments.values() if not (path / "README.md").is_file())
    assert not missing, f"Experiments without README.md: {missing}"


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
