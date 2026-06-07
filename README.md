# research-template

Reusable research project template for data analysis, figures, and manuscript drafting.

## Environment

```bash
docker compose up -d
docker compose exec research-template uv sync
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
├── src/                 # Analysis and reusable source code
├── scripts/             # Command-line helper scripts
├── data/
│   ├── raw/             # Local raw data, ignored by Git except structure
│   ├── interim/         # Intermediate generated data
│   └── processed/       # Local processed data, ignored by Git except structure
├── result/
│   ├── figures/         # Generated figures
│   ├── tables/          # Generated tables
│   └── animations/      # Generated animations and movies
├── draft/               # Manuscript source
├── config.py            # Shared paths and project settings
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Data

The template keeps the `data/` directory structure, but does not include large raw datasets.

Inside Docker, `./data/raw` is mounted read-only at `/data`, and `DATA_ROOT` is set to `/data`.
Outside Docker, `config.py` defaults to `./data/raw`.

Place project-specific input data under `data/raw/`. Keep large or sensitive datasets out of Git.

## Manuscript

`draft/main.tex` and `draft/supplementary.tex` contain heading-only manuscript templates.
