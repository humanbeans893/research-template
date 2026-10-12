# AGENTS.md

This file provides guidance to coding agents (Claude Code, Codex CLI, and others) when working with code in this repository.

Think in English. Answer in the user's requested language.

When writing Japanese, do not write ordinary words in English when natural Japanese exists (code identifiers and proper names excepted), and avoid prose that switches between Japanese and English frequently.

---

## Quick Reference

```bash
# Build the image (bakes the locked dependencies into /opt/venv) and start it
docker compose build
docker compose up -d
# GPU machines: set COMPOSE_FILE=docker-compose.yml:docker-compose.gpu.yml once in .env

# Run Python via Docker
docker compose exec research-template uv run python <script.py>
docker compose exec research-template uv run pytest

# Experiments: create one, run it small first, then in full
make experiment SLUG=<slug>
docker compose exec research-template uv run python experiments/NNN_<slug>/run.py --smoke
docker compose exec research-template uv run python experiments/NNN_<slug>/run.py

# Add packages via Docker, then rebake the image so it keeps the change
docker compose exec research-template uv add <package>
docker compose build && docker compose up -d

# Manuscript on the host: numbers from the CSVs, then the PDFs (draft/build/ holds the rest)
make paper
bash draft/compile.sh --review   # line-numbered, double-spaced draft/main_review.pdf

# Before every commit (ruff + pytest in the container; make help lists the targets), and before git
make check
pwd && git branch && git status
```

---

## Session State and Handoff

Chat context does not survive a new session or a switch between Claude Code and
Codex. Write anything worth keeping into its file when it happens, so that a
session cut off at any point can be resumed from the files alone.

- **At the start**, read `STATE.md` (where things stand, what comes next), then
  `experiments/EXP_SUMMARY.md` (what was tried, what survived, what was
  retracted), then `docs/guardrails.md` (failures not to repeat). Check the
  running jobs in `STATE.md` before starting anything, so a job left by the
  previous session is not ignored or run twice. Before building on or citing an
  experiment, read its `summary.md`; open its `README.md` only to reproduce,
  extend or audit the method.
- **While working**, record immediately, not "later":
  - experiment results → its `summary.md` and `README.md` and its index row, in one commit;
  - a retracted, corrected or superseded result → Experiments › Status and Retraction;
  - a failure not to repeat → `docs/guardrails.md`; an idea → `docs/ideas.md`;
  - a change of state (phase, a submitted or finished job, a decision) → `STATE.md`.
- **Before reporting a finished task** that changed results, decisions, jobs or
  next steps, **and before any long or costly job**, update `STATE.md` with the
  `write-handoff` skill and commit it, then report. You cannot tell when a
  session will end, and a report in chat does not survive it.
- Before any long or costly job, walk `docs/launch-checklist.md`, and log the job
  in `experiments/JOBS.md` at submission and again at completion.
- `STATE.md` holds operational state only; link to the canonical places below,
  do not duplicate them. The always-read files have character budgets, and index
  rows a length cap, checked by `tests/test_repo_structure.py`. Long lines do not
  help: move detail out (finished jobs to `JOBS.md`, older decisions to decision
  records, an experiment's detail to its `summary.md`, a guardrail's story to a
  research log).
- Agent memory (Claude Code auto memory, Codex memories) is per tool and per
  machine: keep no project state there. When memory and a file disagree, the file wins.

### Single Source of Truth

Each piece of information has one canonical place. Do not keep the same table in
two files.

| Information | Canonical place |
|---|---|
| Current state, running jobs and how to check them, next actions | `STATE.md` |
| History of long or costly jobs | `experiments/JOBS.md` |
| Experiment index and status word, including retractions | `experiments/EXP_SUMMARY.md` (a test keeps each `summary.md` status equal) |
| One experiment's current conclusion | `experiments/NNN_<slug>/summary.md` |
| One experiment's record (purpose, method, runs, discussion, corrections) | `experiments/NNN_<slug>/README.md` |
| Retracted claims and failures not to repeat | `docs/guardrails.md` |
| Promising and rejected ideas | `docs/ideas.md` |
| Rationale and history | `docs/` research logs and decision records |
| Working rules | `AGENTS.md` (experiment rules also in `experiments/README.md`, in Japanese) |
| Numbers in the manuscript | `result/tables/*.csv`, not the manuscript text |
| Bibliographic entries | `draft/reference.bib` |

---

## Project Overview

A reusable research project template for analysis code, local data, generated results and manuscript drafting. `README.md` shows the full layout.

- `data/raw/` — raw input, immutable; `data/interim/`, `data/processed/` — derived data, regenerated by code.
- `src/` — reusable code: `utils/` (paths, plotting, validation, I/O, the experiment harness), `models/` (data containers, loaders, parsers), `methods/` (analysis methods, statistics, algorithms), `analysis/` (workflows combining them). `config.py` holds only where things are (directories and data locations, all `Path`); `tests/test_config.py` enforces it.
- `scripts/` — thin command entry points. `notebooks/`, if present, is for exploration (duplicated code is fine while testing an idea); move stable logic into `src/` or `scripts/`.
- `experiments/` — numbered experiments; see Experiments.
- `result/` — generated figures, tables and outputs. `draft/` — manuscript, supplement, references, hand-made figures.
- `docs/` — human-facing documentation in Japanese (research logs, decision records); see `docs/README.md`.
- `tests/` — the pytest suite, run in the container.

---

## Workflow

### Before Starting Work

- Read target files before modifying them.
- Check the current branch and working tree: `pwd && git branch && git status`.
- `main` is protected (PR required with 1 approving review, force pushes and deletion blocked). Do all work on a feature branch and merge via pull request. The repository admin has PR-only bypass and can self-merge without a review; direct pushes are blocked for everyone. If already on a working branch, continue as-is.
- Check remaining TODOs with `rg -n "TODO|FIXME" .`.
- Clarify assumptions when a request depends on unavailable data, missing credentials, or ambiguous research intent.

### During Work

- Validate inputs early with explicit checks.
- Search before writing a function: `rg -n "<concept>" src config.py scripts experiments`. Reuse what exists and follow nearby working examples; add a missing reusable piece to the right `src/` module first; keep script-local helpers small. Do not reimplement a calculation in two places, create near-duplicate helpers, or change a shared helper's behaviour without checking its callers. If reuse would give a wrong result, fix the shared code or add a clearly named alternative with tests.
- Keep scripts thin: they orchestrate functions from `src/`.
- Do not edit generated outputs by hand; regenerate them from code.

### Before Committing

- Run the smallest useful check while working, and `make check` (ruff and every test, in the container) before committing code. After editing `experiments/`, `STATE.md`, `docs/` or a skill, run at least `tests/test_repo_structure.py`.
- For manuscript changes, build with `bash draft/compile.sh` on the host.
- Remove resolved TODO comments and local debug output. Stage only files intentionally changed, and confirm `git status` before committing or pushing.

### What to Test

- Test what guarantees a correct analysis: estimators on synthetic inputs with known answers, units, denominators and rounding against an independent calculation, and the reproduction entry points (bad input stops, existing results are not overwritten).
- Test the system constraints: the runtime environment and the read-only raw data (`tests/test_runtime_constraints.py`), and the handoff structure (`tests/test_repo_structure.py`).
- For the manuscript, test only structure that breaks the PDF silently: citation keys, cross-reference labels, and input and figure files (`tests/test_manuscript_structure.py`). Do not pin headings, word counts, wording or claims; the authors check the text.
- Add tests for new calculations, real bugs and system constraints, not for every edit of the prose. A suite that grows with every rewording stops being run.

---

## Experiments

Iterative experiments live under `experiments/`, one numbered directory each. `experiments/README.md` is the Japanese version of this section; change both in the same edit.

### Structure

- Name: `NNN_<slug>`, three digits and a lower_snake_case slug (e.g. `001_baseline_fit`); the number is the highest in use plus one. `make experiment SLUG=<slug>` picks it, copies `experiments/_template/`, fills in the name and date and adds the index row (or do the same by hand after `cp -r`).
- Each experiment is self-contained:
  - `summary.md` — the current conclusion: status, question and decision rule, answer and what it cannot show, key numbers with their source, the full run. Short (the test sets the limit); rewritten whenever the conclusion changes.
  - `README.md` — the dated record: purpose, method, runs, discussion, corrections. Append only.
  - `run.py` (entry point), `params.py` (every value that can change the result: data selections, windows, thresholds, model and figure settings, seed; pinned there, never read from `config.py` or switched by an environment variable), `out/` (all outputs). A data file's format (columns, variable names) belongs in its loader under `src/models/`.
- `run.py` goes through `src.utils.experiment.start()`: `--smoke` (applies `params.SMOKE`, writes to `out/smoke/`, never promotes), `--overwrite` (needed to replace a completed run; each run holds a lock on its `out/`, so two runs never share one, and first clears what the earlier run left there), `run.promote()` (copies to `result/` only when the run completes), stage progress, and `out/params_used.json` (status, seed, parameters, commit and the list of uncommitted files, stage timings, promoted files; a run with uncommitted code cannot promote). Extend that module instead of writing provenance code in `run.py`. Keep the sys.path bootstrap at the top of `run.py`; the project is not installed as a package.
- Run `--smoke` first; its stage timings are the pilot `docs/launch-checklist.md` asks for.

### Status and Retraction

- The index status cell and the `summary.md` 状態 line start with the same word: 進行中 (no conclusion yet), 完了 (the answer stands), 中止 (stopped without a conclusion), 訂正 (partly corrected, main conclusion stands), 撤回 (main conclusion withdrawn) or 置き換え (a later experiment answers the same question), optionally followed by a date and the evidence, e.g. `撤回(2026-10-02、→ 025_threshold_check)`.
- Write the question and decision rule in `summary.md` at creation and commit them with `params.py` before the full run. Fill in the answer, key numbers and full run after it, in the same commit as the index row. A smoke run changes neither; an `--overwrite` rerun updates both.
- To retract, correct or supersede, in one commit: rewrite 状態 and 答え in `summary.md`, striking the withdrawn statement through instead of deleting it, and fill in its 訂正・撤回・置き換え line; start the index status with the same word; for 撤回, add a row to `docs/guardrails.md`. A heading that still reads as a live conclusion after the body retracted it misleads every later reader.
- Never delete an experiment directory or its index row; mark it 中止, so no number is reused.

### Rules

- Everything an experiment produces goes into its own `out/`, which is git-ignored.
- Finished experiments are immutable: never change a past `run.py`/`params.py` to produce new results; start a new number. In `README.md` only append and fix typos; `summary.md` is the one file you rewrite.
- Logic needed by a second experiment moves into `src/`; never copy it between experiments.
- Never read another experiment's `out/` or import its `run.py` (`out/` is absent from a fresh clone and replaced by a rerun). Promote what others need in code (`run.promote()` or a script): small tables to `result/tables/` (committed), large data to `data/processed/`, figures to `result/figures/`. Never copy by hand.
- A number in `summary.md` or `README.md` carries its source (CSV, row, column); the CSV wins.

### Write Experiments to Run Fast

An experiment that takes hours does not just cost time: it stops you re-running
it, and an analysis you will not re-run is one you will not check. Assume every
experiment will be run many times.

- **Measure before moving anywhere.** Do not port to HPC, add parallelism or
  subsample until a timing says you must. Data that looks too large for one
  machine often is not, once it is read efficiently.
- **Read only what you use.** Drop unneeded variables when you open a dataset
  (`xarray` materialises every remaining data variable in operations such as
  `interp`), open each file once and reuse it, and batch point lookups into one
  vectorised call instead of a loop.
- **Compute once per stratum** when a quantity is constant within it, not once
  per row.
- **Print progress at each stage**, with the row counts being carried. A run with
  no output cannot be told apart from a hung one.
- **Keep the slow part last.** Run extraction, validation gates and cheap exact
  tests before any expensive fit, so a mistake surfaces in seconds rather than
  after hours. If a cheap test can screen candidates before an expensive fit, run
  it first.

---

## Environment Rules

- Project Python, uv, package installs and tests run in the container (`docker compose exec research-template uv run|add ...`); Git, file operations and Docker run on the host. Never start `python` or `python3` on the host, not even for `--version`, `-c` or a heredoc that edits text (use the editor tool or `sed`), and never create a `.venv` or run `virtualenv`, `uv` or a project `pip install` there. For Claude Code, `.claude/settings.json` denies these commands; Codex has no such file, so for Codex this rule is the only guard.
- The environment is `/opt/venv` in the image, baked from `uv.lock`. `HOME` and the uv cache are named volumes, and the caches (`__pycache__`, pytest, ruff) live under `HOME`, so nothing environment-related is written under `/workspace`.
- `uv add` and `uv remove` update `pyproject.toml`, `uv.lock` and the running container; run `docker compose build` afterwards so the image keeps it, and commit `uv.lock`. The build installs the lock frozen, so a stale lock stops it (`Missing workspace member` after renaming the project); refresh it with `make lock`.
- Raw data (`data/raw/`, or `HOST_DATA_DIR` from `.env`) is mounted read-only at `/data` and, through an overlay, at `/workspace/data/raw`.
- GPU is opt-in: set `COMPOSE_FILE=docker-compose.yml:docker-compose.gpu.yml` in `.env`. Passing `-f` to one command is not enough: the next plain `docker compose up -d` (after `uv add`, say) recreates the container without the GPU, with no error.
- Copy `.env.example` to `.env` before the first build (`UID`/`GID`; optional `HOST_DATA_DIR`, `COMPOSE_FILE`, `COMPOSE_PROJECT_NAME`). No port is published and the container does not restart by itself; `make` targets start it. Start Jupyter on demand, on localhost (README.md).

### LaTeX Compilation

- Use host `lualatex` (the container has no TeX) through `bash draft/compile.sh` (`make tex`): `lualatex` → `bibtex` (when something is cited) → `lualatex` ×2 for `main.tex` and `supplementary.tex`, every intermediate in the git-ignored `draft/build/`, the PDFs in `draft/`. It prints only `file:line` errors (transcripts in `draft/build/<job>.log`) and exits non-zero while a citation or reference is undefined.
- Do not run `lualatex` by hand inside `draft/`: stale `.aux` and `.bbl` files left there are read silently and give a PDF with missing or outdated references.
- `--review` (`make tex-review`) writes `draft/main_review.pdf` with line numbers and double spacing; `main.tex` switches only its layout on `\reviewformat`.

---

## Error Handling

### In `src/` Code — Fail Explicitly

```python
# Avoid hiding missing required inputs.
value = data.get("key", "default")

# Prefer explicit validation for required inputs.
assert "key" in data, f"Expected 'key' in data. Got: {list(data.keys())}"
value = data["key"]
```

- Do not use dummy values to make code run, and do not swallow exceptions silently.
- Avoid broad `try`/`except` unless the failure mode is intentionally handled.
- Make data assumptions visible in assertions, validation functions, or clear error messages.
- Defensive defaults are acceptable in quick exploration; convert them into explicit validation before the code moves into `src/` or a script.

---

## Prohibitions

### Git Operations

- Do not commit unnecessary files, and do not push without verification.
- Do not commit directly to `main`; it is protected. Use a feature branch and open a pull request.
- Do not rewrite shared history, or revert changes you did not make, unless the user explicitly requests it.

### Data Handling

- Never edit files in `data/raw/`. Avoid editing `data/interim/` or `data/processed/`; regenerate them from scripts.
- Never commit large data files, and never delete data without explicit user confirmation.

### Generated Outputs

- `result/` is generated output: regenerate figures and tables from code.
- Generate the numbers and tables in the manuscript from `result/tables/*.csv` in code and `\input` them; never type a value into the `.tex` files. A test that passes on the CSV does not protect a number copied by hand. For a number in the text, register a `Number` in `scripts/make_numbers.py`, run `make numbers`, write `\Name{}`, and commit `draft/tables/numbers.tex` with its CSVs (a test fails when it is stale). Format table cells with `src.utils.tex_numbers.format_value`, so tables and text round alike.
- The manuscript reads promoted figures from `result/figures/` (`\graphicspath`); `draft/figures/` holds only hand-made ones.
- Commit `result/tables/*.csv` (small, canonical for the manuscript). Do not commit large generated artifacts unless the user asks.

### Imports and Security

- Keep import style consistent; do not switch between relative and absolute imports unless the package layout requires it.
- Never hardcode passwords, tokens, API keys, or personal credentials; keep secrets in environment variables or ignored files such as `.env`.

---

## References

- `draft/reference.bib` is the single source of truth for bibliographic entries. Do not sync it with a reference manager.
- Agents do not connect to Zotero or any other reference manager. When the user wants an entry from their own library, they hand it over (for example, as a BibTeX export).
- Before adding an entry, whether you found it or the user handed it over, check it against the original through its DOI (publisher page, PMC, Crossref, or an archived copy). Check any number you quote from it against the original text as well.

---

## Permissions

- Usually safe: reading files, running tests and non-destructive checks, compiling TeX, inspecting Git status, diffs and logs.
- Confirm first: deleting files or directories, installing packages, changing repository visibility, remotes or authentication, and any irreversible or high-cost operation.
