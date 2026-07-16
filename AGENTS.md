# AGENTS.md

This file provides guidance to coding agents (Claude Code, Codex CLI, and others) when working with code in this repository.

Think in English. Answer in the user's requested language.

---

## Quick Reference

```bash
# Start the project container
docker compose up -d

# Optional: start with NVIDIA GPU access
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

# Run Python via Docker
docker compose exec research-template uv run python <script.py>
docker compose exec research-template uv run python exp/NNN_<slug>/run.py
docker compose exec research-template uv run pytest

# Add packages via Docker
docker compose exec research-template uv add <package>

# Compile LaTeX on the host
cd draft && lualatex -interaction=nonstopmode main.tex

# Pre-git check
pwd && git branch && git status
```

---

## Project Overview

This is a reusable research project template for analysis code, local data, generated results, and manuscript drafting. See `README.md` for the current directory layout.

**Key directories:**
- `data/raw/` — Raw input data. Treat as immutable and do not commit large files.
- `data/interim/` — Intermediate data generated from raw inputs.
- `data/processed/` — Analysis-ready derived data.
- `src/` — Reusable project code.
- `scripts/` — Execution scripts and one-off command entrypoints.
- `exp/` — Numbered self-contained experiment directories (`NNN_<slug>/`). Copy `exp/_template/` to start one; see the Experiments section and `exp/README.md`.
- `result/` — Generated figures, tables, and analysis outputs.
- `draft/` — Manuscript, supplementary material, references, and figure assets.
- `docs/` — Human-facing project documentation in Japanese (research logs, decision records); see `docs/README.md`.
- `tests/` — Pytest test suite; run via `docker compose exec research-template uv run pytest`.

---

## Workflow

### Before Starting Work

- Read target files before modifying them.
- Check the current branch and working tree: `pwd && git branch && git status`.
- `main` is protected (PR required, force pushes and deletion blocked). Do all work on a feature branch and merge via pull request; self-merge is allowed (0 required approvals).
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
- For manuscript changes, compile the relevant TeX file with host `lualatex`.
- Remove resolved TODO comments and local debug output.
- Stage only files intentionally changed for the task.
- Confirm `git status` before committing or pushing.

### Notebook vs Script vs Source

- `src/` — Reusable functions, classes, and modules.
- `scripts/` — Reproducible command entrypoints.
- `notebooks/` if present — Exploratory analysis, visualization, and prototyping.
- Move stable notebook logic into `src/` or `scripts/`.

---

## Experiments

Iterative experiments live under `exp/`, one numbered directory per experiment.

### Structure

- Name: `NNN_<slug>` (zero-padded sequence, e.g. `001_baseline_fit`); use the next unused number.
- Start a new experiment with `cp -r exp/_template exp/NNN_<slug>`.
- Each experiment is self-contained: `README.md` (purpose/method/results/notes), `run.py` (entrypoint), `params.py` (parameters), `out/` (all outputs).
- Run with `docker compose exec research-template uv run python exp/NNN_<slug>/run.py`.
- `run.py` begins with a sys.path bootstrap that makes `config` and `src` importable; keep it — the project is not installed as a package.

### Rules

- Everything an experiment produces goes into its own `out/`; `exp/*/out/` is git-ignored and never committed.
- Commit the experiment's code and README; update the experiment `README.md` with findings after each meaningful run.
- Treat finished experiments as immutable: never change a past experiment's `run.py`/`params.py` to produce new results — start a new numbered experiment instead. Appending notes or fixing typos in its README is fine.
- When logic is needed by a second experiment, move it into `src/` and import it from both; never copy-paste between experiment directories.
- Promote paper-ready figures to `result/figures/` via code (a final step in `run.py` or a script in `scripts/`), never by manual copying.

---

## Environment Rules

- Use Docker + `uv run` for normal script and test execution.
- Use Docker + `uv add` for package installation.
- Do not rely on host Python or host `.venv` for normal project execution.
- If you must enter the container interactively, use `docker compose exec research-template bash`, but prefer direct `docker compose exec ... uv run ...`.
- Cache and tool state inside Docker are stored under `/workspace/.cache/`.
- GPU access is opt-in via the `docker-compose.gpu.yml` override; the base compose file runs CPU-only.
- Copy `.env.example` to `.env` before the first `docker compose up` (sets `UID`/`GID`, optional `DATA_ROOT`).
- `uv.lock` is committed; after `uv add`/`uv remove`, commit the updated lockfile.

### LaTeX Compilation

- Use host `lualatex` to compile files under `draft/`.
- Standard command: `cd draft && lualatex -interaction=nonstopmode main.tex`.
- For bibliography updates, run the full sequence: `lualatex` -> `bibtex main` -> `lualatex` -> `lualatex`.

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

1. Search before writing: `rg -n "<concept-or-function-name>" src config.py scripts`.
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
- Avoid committing large generated artifacts unless the user explicitly asks for them.

### Import Management

- Keep import style consistent within the project.
- Avoid changing relative imports to absolute imports, or the reverse, unless the package layout requires it.

### Security

- Never hardcode passwords, tokens, API keys, or personal credentials.
- Keep secrets in environment variables or ignored local files such as `.env`.

---

## Zotero MCP (Optional, WSL2)

If Zotero is running on Windows and MCP access is needed from WSL2, use `/zotero-connect` to start the local port forwarder.

- **Skill**: `/zotero-connect`
- **Script**: `.claude/scripts/zotero-forward.py`
- **Collection**: project-specific; ask the user or list available collections before assuming a collection key.

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
