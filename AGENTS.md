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

# Optional: start with NVIDIA GPU access
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

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

# Compile the manuscript on the host (intermediates go to draft/build/)
bash draft/compile.sh
bash draft/compile.sh --review   # line-numbered, double-spaced draft/main_review.pdf

# Pre-git check
pwd && git branch && git status
```

---

## Session State and Handoff

Chat context does not survive a new session or a switch between Claude Code and
Codex. Write anything worth keeping into its file when it happens, so that a
session cut off at any point can be resumed from the files alone.

- **At the start**, read `STATE.md` (where things stand and what comes next),
  then `experiments/EXP_SUMMARY.md` (what was tried, what survived and what was
  retracted), then `docs/guardrails.md` (failures not to repeat). Check the
  running jobs in `STATE.md` before starting anything, so a job left by the
  previous session is not ignored or run twice.
- **Before building on or citing an experiment**, read its
  `experiments/NNN_<slug>/summary.md` (status, answer, what it cannot show, key
  numbers and their source). Open its `README.md` only to reproduce, extend or
  audit the method.
- **While working**, record immediately, not "later":
  - experiment results → that experiment's `summary.md` (answer, key numbers with
    their source, the full run) and `README.md` (the dated record), and its row in
    `experiments/EXP_SUMMARY.md`, in the same commit;
  - a retracted, corrected or superseded result → the procedure in Experiments ›
    Status and Retraction, in one commit;
  - a failure not to repeat → `docs/guardrails.md`;
  - a new or rejected idea → `docs/ideas.md`;
  - a change of state (phase, a submitted or finished job, a decision) → `STATE.md`.
- **Before reporting a finished task** that changed results, decisions, jobs or
  the next steps, **and before any long or costly job**, update `STATE.md` with
  the `write-handoff` skill and commit it on the working branch, then report. You
  cannot tell when a session will end, and a report in chat does not survive it.
  A running job needs how to check it and where its result must be recorded.
- `STATE.md` holds operational state only. Scientific narrative stays canonical
  in `docs/` research logs and decision records, each experiment's conclusion in
  its `summary.md` and its record in its `README.md` — link, do not duplicate.
- Before any long or costly job, walk `docs/launch-checklist.md`. Log every such
  job in `experiments/JOBS.md` immediately at submission and again at completion.
- The always-read files (`STATE.md`, `experiments/EXP_SUMMARY.md`,
  `docs/guardrails.md`) have character budgets, and each index row a length cap,
  checked by `tests/test_repo_structure.py`. Long lines do not help: move detail
  out instead — finished jobs to `experiments/JOBS.md`, older decisions to
  decision records, an experiment's detail to its `summary.md`, the story behind
  a guardrail to a research log.
- Agent memory (Claude Code auto memory, Codex memories) is per tool and per
  machine. Keep no project state, results or decisions there; when memory and a
  file disagree, the file wins.
- `tests/test_repo_structure.py` checks this structure mechanically.

### Single Source of Truth

Each piece of information has one canonical place. Do not keep the same table in
two files.

| Information | Canonical place |
|---|---|
| Current state and next actions | `STATE.md` |
| Running jobs and how to check them | `STATE.md` |
| History of long or costly jobs (submission, commit, resources, result) | `experiments/JOBS.md` |
| Experiment index and status word, including retractions | `experiments/EXP_SUMMARY.md` (each `summary.md` repeats the status word; a test keeps them equal) |
| One experiment's current conclusion: status, answer, what it cannot show, key numbers with their source, the full run | `experiments/NNN_<slug>/summary.md` |
| One experiment's record: purpose, method, each run, discussion, dated corrections | `experiments/NNN_<slug>/README.md` |
| Retracted claims and failures not to repeat | `docs/guardrails.md` |
| Promising and rejected ideas | `docs/ideas.md` |
| Rationale and history | `docs/` research logs and decision records |
| Working rules | `AGENTS.md` |
| Numbers in the manuscript | `result/tables/*.csv`, not the manuscript text |
| Bibliographic entries | `draft/reference.bib` |

---

## Project Overview

This is a reusable research project template for analysis code, local data, generated results, and manuscript drafting. See `README.md` for the current directory layout.

**Key directories:**
- `data/raw/` — Raw input data. Treat as immutable and do not commit large files.
- `data/interim/` — Intermediate data generated from raw inputs.
- `data/processed/` — Analysis-ready derived data.
- `src/` — Reusable project code.
- `scripts/` — Execution scripts and one-off command entrypoints.
- `experiments/` — Numbered self-contained experiment directories (`NNN_<slug>/`); `experiments/EXP_SUMMARY.md` indexes them and `experiments/JOBS.md` logs long or costly jobs. See the Experiments section.
- `result/` — Generated figures, tables, and analysis outputs.
- `draft/` — Manuscript, supplementary material, references, and figure assets.
- `docs/` — Human-facing project documentation in Japanese (research logs, decision records); see `docs/README.md`.
- `tests/` — Pytest test suite; run via `docker compose exec research-template uv run pytest`.

---

## Workflow

### Before Starting Work

- Read target files before modifying them.
- Check the current branch and working tree: `pwd && git branch && git status`.
- `main` is protected (PR required with 1 approving review, force pushes and deletion blocked). Do all work on a feature branch and merge via pull request. The repository admin has PR-only bypass and can self-merge without a review; direct pushes are blocked for everyone.
- If already on a working branch, continue as-is.
- Check remaining TODOs with `rg -n "TODO|FIXME" .`.
- Clarify assumptions when a request depends on unavailable data, missing credentials, or ambiguous research intent.

### During Work

- Prefer Docker for normal project execution: `docker compose exec research-template uv run ...`.
- Validate inputs early with explicit checks.
- Keep source code reusable; place shared logic under `src/`.
- Keep scripts thin; scripts should orchestrate reusable functions instead of holding complex logic.
- Avoid editing generated outputs by hand; regenerate them from code.

### Before Committing

- Run the smallest useful verification for the change.
- For Python changes, run targeted tests or the modified script via Docker.
- For manuscript changes, build with `bash draft/compile.sh` on the host.
- Remove resolved TODO comments and local debug output.
- Stage only files intentionally changed for the task.
- Confirm `git status` before committing or pushing.

### What to Test

- Test what guarantees a correct analysis: estimators on synthetic inputs with known answers, units, denominators and rounding against an independent calculation, and the reproduction entry points (bad input stops, existing results are not overwritten).
- Test the system constraints: the runtime environment and the read-only raw data (`tests/test_runtime_constraints.py`), and the handoff structure (`tests/test_repo_structure.py`).
- For the manuscript, test only structure that breaks the PDF silently: citation keys, cross-reference labels, and input and figure files (`tests/test_manuscript_structure.py`). Do not pin headings, word counts, wording or claims; the authors check the text.
- Add tests for new calculations, real bugs and system constraints, not for every edit of the prose. A suite that grows with every rewording stops being run.

### Notebook vs Script vs Source

- `src/` — Reusable functions, classes, and modules.
- `scripts/` — Reproducible command entrypoints.
- `notebooks/` if present — Exploratory analysis, visualization, and prototyping.
- Move stable notebook logic into `src/` or `scripts/`.

---

## Experiments

Iterative experiments live under `experiments/`, one numbered directory per experiment. `experiments/README.md` is the Japanese version of this section; change both in the same edit.

### Structure

- Name: `NNN_<slug>`, three digits and a lower_snake_case slug (e.g. `001_baseline_fit`). The number is the highest one in use plus one.
- Create one with `make experiment SLUG=<slug>`: it picks the number, copies `experiments/_template/`, fills in `NNN_<slug>` and the date, and adds the index row. Doing the same by hand after `cp -r experiments/_template experiments/NNN_<slug>` also works.
- Each experiment is self-contained:
  - `summary.md` — its current conclusion: status, question and decision rule, answer and what it cannot show, key numbers with their source, the full run. Kept short (the test sets the limit) and rewritten whenever the conclusion changes.
  - `README.md` — the dated record: purpose, method, each run, discussion, corrections. Append only.
  - `run.py` (entrypoint), `params.py` (every value that defines the experiment, pinned there rather than read from `config.py`), `out/` (all outputs).
- `run.py` goes through `src.utils.experiment.start()`. It gives `--smoke` (applies `params.SMOKE`, writes to `out/smoke/`, never promotes) and `--overwrite` (a completed full run is not replaced without it), prints each stage with its elapsed time, and writes `out/params_used.json` (status, seed, parameters, commit and uncommitted code, stage timings, promoted files). Extend that module rather than writing provenance or progress code in `run.py`.
- Run `--smoke` first; its stage timings are the pilot that `docs/launch-checklist.md` asks for.
- `run.py` begins with a sys.path bootstrap that makes `config` and `src` importable; keep it — the project is not installed as a package.

### Status and Retraction

- The index status cell and `summary.md`'s 状態 line start with the same word: 進行中 (no conclusion yet), 完了 (the answer stands), 中止 (stopped without a conclusion), 訂正 (partly corrected; the main conclusion stands), 撤回 (the main conclusion is withdrawn) or 置き換え (a later experiment answers the same question). A date and the experiment that shows it may follow, e.g. `撤回(2026-10-02、→ 025_threshold_check)`.
- Write `summary.md`'s question and decision rule when you create the experiment, and commit them with `params.py` before the full run. Fill in the answer, key numbers and full run after the full run, in the same commit as the index row. A smoke run changes neither; a rerun with `--overwrite` updates both in the same commit.
- To retract, correct or supersede a result, in one commit: rewrite the 状態 and 答え of `summary.md`, striking the withdrawn statement through rather than deleting it, and fill in its 訂正・撤回・置き換え line; start the index status cell with the same word; for 撤回, add a row to `docs/guardrails.md`. A heading that still reads as a live conclusion after the body retracted it misleads every later reader.
- Never delete an experiment directory or its index row; mark an abandoned experiment 中止, so that no number is ever reused.
- `tests/test_repo_structure.py` checks the names and numbers, the index, the size and status word of each `summary.md`, and that no template placeholder is left in a `summary.md` past 進行中.

### Rules

- Everything an experiment produces goes into its own `out/`; `experiments/*/out/` is git-ignored and never committed.
- Treat finished experiments as immutable: never change a past experiment's `run.py`/`params.py` to produce new results — start a new numbered experiment instead. In its `README.md`, only append and fix typos; `summary.md` is the one file you rewrite.
- When logic is needed by a second experiment, move it into `src/` and import it from both; never copy-paste between experiment directories.
- Never read another experiment's `out/` or import its `run.py`: `out/` is absent from a fresh clone and replaced by a rerun. Whatever a later experiment or the manuscript needs is promoted in code (`run.promote()` or a script in `scripts/`): small tables to `result/tables/` (committed), large data to `data/processed/`, figures to `result/figures/`. Never copy by hand.
- A number in `summary.md` or `README.md` carries its source (CSV, row, column); when they disagree, the CSV wins.

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

- Use Docker + `uv run` for normal script and test execution.
- Use Docker + `uv add` for package installation.
- Never create a project `.venv` or `venv` on the host, and never run `python -m venv`, `virtualenv`, `uv venv`, `uv sync`, `uv run` or a project `pip install` there. Git, file operations and Docker commands run on the host; project Python, uv and tests run in the container.
- The project environment is `/opt/venv` inside the image (`UV_PROJECT_ENVIRONMENT`), baked from `uv.lock` at build time. `HOME` (`/home/app`) and the uv cache (`/opt/uv-cache`) are Docker named volumes, and `PYTHONPYCACHEPREFIX` keeps `__pycache__` under `HOME`. Nothing environment-related is written under `/workspace`, so no `.venv`, uv cache or `__pycache__` appears on the host.
- `uv add` updates `pyproject.toml` and `uv.lock` on the host and the environment in the running container. Run `docker compose build` afterwards so the image keeps the change.
- The build installs `uv.lock` frozen, so a stale lock stops it (`Missing workspace member` after renaming the project in `pyproject.toml`). Update the lock with `make lock`, which runs `uv lock` in a throwaway uv container, before building.
- If you must enter the container interactively, use `docker compose exec research-template bash`, but prefer direct `docker compose exec ... uv run ...`.
- Raw data is mounted read-only at `/data` and, through an overlay, at `/workspace/data/raw`, so it cannot be modified through either path.
- GPU access is opt-in via the `docker-compose.gpu.yml` override; the base compose file runs CPU-only.
- Copy `.env.example` to `.env` before the first `docker compose build` (sets `UID`/`GID`, optional `DATA_ROOT`).
- `uv.lock` is committed; after `uv add`/`uv remove`, commit the updated lockfile.

### LaTeX Compilation

- Use host `lualatex`; the container has no TeX distribution.
- Build with `bash draft/compile.sh` (or `make tex`). It runs `lualatex` → `bibtex` (when the document declares a bibliography and cites something) → `lualatex` → `lualatex` for `main.tex` and `supplementary.tex`, writes every intermediate file to the git-ignored `draft/build/`, and leaves only the PDFs in `draft/`.
- Do not run `lualatex` by hand inside `draft/`. Stale `.aux` and `.bbl` files left there are picked up silently and produce a PDF with missing or outdated references.
- `bash draft/compile.sh --review` (or `make tex-review`) writes `draft/main_review.pdf` with line numbers and double spacing for submission. `main.tex` switches only its layout on `\reviewformat`; the text is identical.

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

- Do not use dummy values to make code run.
- Do not swallow exceptions silently.
- Avoid broad `try`/`except` unless the failure mode is intentionally handled.
- Make data assumptions visible in assertions, validation functions, or clear error messages.

### In Exploratory Work

- Defensive defaults are acceptable for quick exploration.
- Convert exploratory shortcuts into explicit validation before moving code into `src/` or production scripts.

---

## Code Reuse

Before writing a new function, class, or helper, inspect the existing project modules and reuse suitable implementations.

### Shared Module Areas

- `src/utils/` — General utilities such as paths, math helpers, plotting helpers, validation, randomness, and file I/O.
- `src/models/` — Domain objects, typed data containers, loaders, and parsers.
- `src/methods/` — Reusable analysis methods, statistical procedures, algorithms, and modeling code.
- `src/analysis/` — Higher-level analysis workflows that combine utilities, models, and methods.
- `config.py` — Shared paths, parameters, thresholds, and project-level constants.

### Reuse Procedure

1. Search before writing: `rg -n "<concept-or-function-name>" src config.py scripts experiments`.
2. Check nearby working examples before inventing a new calling pattern.
3. If a reusable implementation is missing, add it to the appropriate shared module first.
4. Keep script-local helpers small and task-specific.
5. Do not copy old or external code into a new script if it can be expressed through current project APIs.

### Avoid

- Reimplementing the same calculation in multiple scripts.
- Embedding parsing, validation, or plotting conventions in one-off scripts when they should be shared.
- Creating near-duplicate helper names with slightly different behavior.
- Changing public helper behavior without checking current callers.

### Exceptions

- Temporary exploratory notebook code may be duplicated while testing an idea.
- If reusing an existing implementation would produce incorrect behavior, update the shared implementation or add a clearly named alternative with tests.

---

## Prohibitions

### Git Operations

- Do not commit unnecessary files.
- Do not push without verification.
- Do not commit directly to `main`; it is protected. Use a feature branch and open a pull request.
- Do not rewrite shared history unless the user explicitly requests it.
- Do not revert changes you did not make unless the user explicitly requests it.

### Data Handling

- Never edit files in `data/raw/` directly; raw data should be immutable.
- Avoid editing `data/interim/` or `data/processed/` directly; regenerate derived data from scripts when possible.
- Never commit large data files to Git.
- Never delete data without explicit user confirmation.

### Generated Outputs

- Treat `result/` as generated output.
- Prefer regenerating figures and tables from source code.
- Generate the numbers and tables in the manuscript from the CSVs in `result/tables/`: write LaTeX macros or table files in code and `\input` them, instead of typing values into the `.tex` files. A test that passes on the CSV does not protect a number copied into the text by hand.
- Commit `result/tables/*.csv`: they are small and canonical for the manuscript. Avoid committing large generated artifacts (animations, figures of many MB) unless the user explicitly asks for them.

### Import Management

- Keep import style consistent within the project.
- Avoid changing relative imports to absolute imports, or the reverse, unless the package layout requires it.

### Security

- Never hardcode passwords, tokens, API keys, or personal credentials.
- Keep secrets in environment variables or ignored local files such as `.env`.

---

## References

- `draft/reference.bib` is the single source of truth for bibliographic entries. Do not sync it with a reference manager.
- Agents do not connect to Zotero or any other reference manager. When the user wants an entry from their own library, they hand it over (for example, as a BibTeX export).
- Before adding an entry, whether you found it or the user handed it over, check it against the original through its DOI (publisher page, PMC, Crossref, or an archived copy). Check any number you quote from it against the original text as well.

---

## Permissions

### Usually Safe

- Reading files.
- Running tests and non-destructive checks.
- Compiling TeX.
- Inspecting Git status, diffs, and logs.

### Confirm First

- Deleting files or directories.
- Installing packages.
- Changing repository visibility, remotes, or authentication.
- Any irreversible or high-cost operation.
