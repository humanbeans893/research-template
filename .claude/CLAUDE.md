# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

Think in ENGLISH, answer in Japanese.

---

## Quick Reference

```bash
# Run Python via Docker
docker compose exec eddy-and-current uv run python script.py
docker compose exec eddy-and-current uv run pytest

# Add packages via Docker
docker compose exec eddy-and-current uv add <package>

# Start container
docker compose up -d

# Compile LaTeX (use host lualatex, NOT docker/pdflatex)
cd draft && lualatex -interaction=nonstopmode main.tex

# Pre-git check
pwd && git branch && git status
```

---

## Project Overview

Data science / Kaggle competition template. See `README.md` for full directory layout.

**Key directories:**
- `data/raw/` — Raw data (immutable)
- `data/interim/` — Intermediate processed data
- `data/processed/` — Analysis-ready data
- `data/result/` — Final outputs (submission.csv, etc.)
- `outputs/` — Trained models and checkpoints
- `scripts/` — Execution scripts and notebooks (`main.ipynb`)
- `src/` — Pipeline code
- `notebooks/` — Exploratory analysis notebooks
- `reference/` — Research notes and strategy documents

---

## Workflow

### Before Starting Work

- For new tasks, create a feature branch from `main` (e.g., `feat-<feature>`, `fix-<bug>`)
- If already on a working branch, continue as-is
- Never work directly on `main` branch
- Check remaining TODOs: `grep -rn 'TODO' src/`
- When user recommends creating or proposing an implementation plan, you must also create a corresponding GitHub Issue before starting the actual implementation. The issue should include: A clear title,The purpose of the task,The implementation plan,Expected changes,Any risks, assumptions, or open questions

### During Work

- Read target files before modifying them
- Always execute Python scripts and tools via Docker, e.g. `docker compose exec eddy-and-current uv run ...`
- Use `pwd && git branch && git status` before any git operation
- Validate data early with explicit checks
- Use `assert` to make preconditions explicit (see Error Handling section for scope)

### Before Committing

- review with codex ['codex review [prompt]']
- Run the modified script to verify functionality: `docker compose exec eddy-and-current uv run python <script>`
- Use debug mode if available (`--debug` flag)
- Remove TODO comments that are resolved
- Only `git add` the specific files you modified (never `git add .` or `git add -A`)
- Ensure no errors exist before committing

### Notebook vs Script

- `notebooks/` — Exploratory analysis, visualization, prototyping
- `scripts/main.ipynb` — Main execution pipeline
- `src/` — Reusable pipeline code (functions and modules)

### Docker Environment

```bash
# Start project container
docker compose up -d

# Sync dependencies
docker compose exec eddy-and-current uv sync

# Run a script
docker compose exec eddy-and-current uv run python src/analysis/eddy_association.py

# Run tests
docker compose exec eddy-and-current uv run pytest
```

---

## After Each Task Completion (Required)

Present the following upon task completion. **For small changes (bug fixes, 1-2 files), sections 1-2 only. For large features, all sections 1-5.**

#### 1. Show Code That Needs Review
**Only show code that requires human judgment or review.** Do not dump all changed code.
- Show decision points, business logic, and non-obvious implementations
- Use file path with line numbers (e.g., `src/foo.py:42-58`)
- Omit mechanical/boilerplate changes

#### 2. Review Checklist
- Provide around 5 review items that you judge most relevant to the specific change.
- Do not use a fixed template by default; adapt the checklist to the task type (e.g., code, analysis, paper writing, translation, documentation).
- Prefer concrete review questions that reflect the actual risks in the change over generic boilerplate.

#### 3. System Structure Diagram (large changes only)
Show where the change is located using an ASCII diagram.

#### 4. Test Results (large changes only)
Test names and results (passed/failed).

#### 5. Impact on Next Tasks (large changes only)
Which parts the next task depends on.

---

## Environment Rules

- **Always use Docker + `uv run`** to execute scripts and tools (e.g., `docker compose exec eddy-and-current uv run pytest`)
- **Always use Docker + `uv add`** for package installation (e.g., `docker compose exec eddy-and-current uv add <package>`)
- **Do not rely on host system Python or host `.venv`** for normal execution
- If you must enter the container interactively, use `docker compose exec eddy-and-current bash`, but prefer direct `docker compose exec ... uv run ...`
- Cache and tool state inside Docker are stored under `/workspace/.cache/`

### LaTeX Compilation (Exception)

- **Use host `lualatex`** to compile `draft/main.tex` — do NOT use Docker or `pdflatex` (the container lacks a TeX distribution, and host `pdflatex` fails on `pdftexcmds`)
- Standard command: `cd draft && lualatex -interaction=nonstopmode main.tex`
- For bibliography updates, run the full sequence: `lualatex` → `bibtex main` → `lualatex` → `lualatex`

---

## Error Handling

### In `src/` pipeline code — Fail Explicitly
```python
# FORBIDDEN: Fallback hiding the problem
value = data.get("key", "default")

# REQUIRED: Explicit assertion
assert "key" in data, f"Expected 'key' in data. Got: {list(data.keys())}"
value = data["key"]
```

- Never use dummy values — solve root causes
- Never swallow exceptions — propagate errors properly
- Never use broad try-except

### In `notebooks/` exploratory code — Defensive defaults acceptable
- `data.get("key", default)` is acceptable for handling missing/optional data
- `hasattr()` and `isinstance()` are acceptable for pandas/numpy duck typing
- Focus on exploration speed over strict validation

---

## Code Reuse (既存実装の再利用)

新しい関数・クラス・ヘルパーを書く前に、`src/utils/`・`src/models/`・`src/methods/` を必ず確認し、目的に合う実装があれば **そのまま再利用する**。手元で似たロジックを書き直さない。

### 主な共有モジュール
- `src/utils/vector2d.py` — `Vector2D` クラス (`angle_to`, `norm`, `direction`, `is_zero`)、`movement_vector`、`movement_vector_meters`
- `src/utils/geo.py` — `haversine_distance(lat1, lon1, lat2, lon2)` ほか地理計算
- `src/utils/seed.py` — 乱数シード初期化
- `src/models/current.py` — `OceanCurrent` (単点 `get_current` と一括補間 `get_current_batch`)
- `src/models/shark_loader.py` — `load_gps_data`、`qualify_gps_data`、時空間範囲算出
- `src/models/shark.py` / `src/models/eddy.py` — ドメインモデル
- `src/methods/crw.py` — CRW 帰無モデル
- `config.py` — パス・パラメータ・しきい値

### 手順
1. **書く前に grep**: `grep -rn "<やりたい計算名>" src/utils src/models src/methods` で既存実装を確認
2. **似た既存呼び出しを参照**: 既に動いている `src/analysis/*.py` (例: `current_angle.py`) がどう既存ユーティリティを使っているかを真似る
3. **欠けている場合のみ追加**: 既存実装がないと判断したら、まず該当する `src/utils/` か `src/models/` に **共有可能な関数として** 追加し、呼び出し側からは import して使う
4. **新規スクリプト内に「移植版」を持ち込まない**: 古いブランチや削除済みコードを復元する際も、現行の `src/utils/`・`src/models/` の API に合わせて **既存実装を呼び出す形に書き直す**

### NG 例 (してはいけない)
- ベクトル間角度を `np.arctan2(cross, dot)` で書き直す (→ `Vector2D.angle_to()` を使う)
- haversine 公式を再実装する (→ `src.utils.geo.haversine_distance` を使う)
- 海流の格子点ループで `get_current` をスカラー呼び出しする (→ `OceanCurrent.get_current_batch` を使う)
- 個体GPS の読み込み・品質フィルタを自前で書く (→ `src.models.shark_loader` を使う)

### 例外
- 探索的なノートブック (`notebooks/`) で一時的に書く分には許容
- 既存実装の挙動を変えると他箇所に影響する場合は、再利用ではなく既存実装を直す PR を切る

---

## Prohibitions

### Git Operations
- Never work on `main` branch directly
- Never use `git add .` or `git add -A`
- Never commit unnecessary files
- Never push without verification

### Data Handling
- **Never edit files in `data/raw/` directly** — Raw data is immutable
- **Never edit files in `data/processed/` directly** — Regenerate from scripts
- **Never commit large data files to git**

### Model Artifacts (CRITICAL)
- **NEVER delete or move trained artifacts under `outputs/`** — LoRA adapters, checkpoints, and trained models are valuable assets that require significant time and resources to retrain
- **NEVER run `rm` or `mv` on model directories** — `outputs/sft_*`, `outputs/**/lora_adapter`, `*.safetensors`, etc.
- **Always ask for explicit confirmation** before any operation that could affect trained models

### HPC Sync (CRITICAL)

Never delete large-scale data on HPC when syncing from local:

```bash
# DANGEROUS: --delete removes files that only exist on HPC
rsync -avz --delete local/ hpc:nishika/  # NG!

# SAFE: omit --delete, or use exclusions
rsync -avz local/ hpc:nishika/  # OK
rsync -avz --delete --exclude='outputs/' --exclude='.cache/' local/ hpc:nishika/  # OK
```

**Important directories that exist only on HPC:**
- `outputs/sft_*/` — Trained LoRA adapters
- `outputs/*/lora_adapter/` — LoRA checkpoints
- `outputs/descriptions/` — Image description JSONs
- `outputs/ocr/` — OCR results
- `.cache/huggingface/` — Downloaded models

### Import Management
- Never change relative imports to absolute (or vice versa)
- Never use command-line argument parsing for data paths (Exception: `--debug` flag)

### Security
- Never hardcode passwords or API keys
- Never delete data without user confirmation

---

## Zotero MCP (WSL2)

ZoteroはWindows側で動作。WSL2からは直接接続できないため、セッション開始時にポートフォワーダーが必要。

- **スキル**: `/zotero-connect` で接続手順を実行
- **スクリプト**: `.claude/scripts/zotero-forward.py` — ゲートウェイIP自動検出、冪等（二重起動安全）
- **コレクション**: EddyAndCuurent (`BVS7T5VA`)

---

## Permissions

### No Permission Needed
- Code execution, reading files, running tests
- Git operations (commit, push, branch) — auto-allowed in settings

### Permission Required
- File deletion
- Package installation (`docker compose exec eddy-and-current uv add <package>`)
- Any irreversible operation
