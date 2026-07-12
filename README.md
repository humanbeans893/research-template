# research-template

Reusable research project template for data analysis, figures, and manuscript drafting.

## Environment

```bash
cp .env.example .env   # set UID/GID for the container user mapping
docker compose up -d
docker compose exec research-template uv sync
```

### GPU (optional)

The base compose file runs CPU-only. On a machine with an NVIDIA GPU:

```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

## Container

```bash
docker compose start
docker compose stop
docker compose exec research-template bash
docker compose exec research-template uv add <package>
```

## Layout

```text
research-template/
├── src/                   # Analysis and reusable source code
├── scripts/               # Command-line helper scripts
├── tests/                 # Pytest test suite
├── data/
│   ├── raw/               # Local raw data, ignored by Git except structure
│   ├── interim/           # Intermediate generated data
│   └── processed/         # Local processed data, ignored by Git except structure
├── result/
│   ├── figures/           # Generated figures
│   ├── tables/            # Generated tables
│   └── animations/        # Generated animations and movies
├── draft/                 # Manuscript source
├── .claude/               # Claude Code skills and helper scripts
├── AGENTS.md              # Guidance for coding agents (canonical)
├── CLAUDE.md              # Imports AGENTS.md for Claude Code
├── config.py              # Shared paths and project settings
├── .env.example           # Template for local .env (UID/GID, DATA_ROOT)
├── Dockerfile
├── docker-compose.yml     # CPU-only base
├── docker-compose.gpu.yml # NVIDIA GPU override
├── pyproject.toml
└── uv.lock
```

## Data

The template keeps the `data/` directory structure, but does not include large raw datasets.

Inside Docker, `./data/raw` is mounted read-only at `/data`, and `DATA_ROOT` is set to `/data`.
Outside Docker, `config.py` defaults to `./data/raw`.

Place project-specific input data under `data/raw/`. Keep large or sensitive datasets out of Git.

## Tests

```bash
docker compose exec research-template uv run pytest
```

## Manuscript

`draft/main.tex` and `draft/supplementary.tex` contain heading-only manuscript templates.
