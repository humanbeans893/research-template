"""Shared project configuration for research-template."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent

DATA_ROOT = Path(os.environ.get("DATA_ROOT", PROJECT_ROOT / "data" / "raw"))
RESULT_DIR = PROJECT_ROOT / "result"
DRAFT_DIR = PROJECT_ROOT / "draft"
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"

RAW_DATA_DIR = DATA_ROOT
INTERIM_DATA_DIR = PROJECT_ROOT / "data" / "interim"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

FIGURE_DIR = RESULT_DIR / "figures"
TABLE_DIR = RESULT_DIR / "tables"
ANIMATION_DIR = RESULT_DIR / "animations"

RANDOM = {
    "default_seed": 42,
}

VISUALIZATION = {
    "dpi": 300,
    "format": "png",
    "font": {
        "family": "DejaVu Sans",
        "size": 12,
    },
}
