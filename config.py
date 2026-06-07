"""Shared project configuration for research-template."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent

DATA_ROOT = Path(os.environ.get("DATA_ROOT", PROJECT_ROOT / "data" / "raw"))
RESULT_DIR = PROJECT_ROOT / "result"
DRAFT_DIR = PROJECT_ROOT / "draft"

RAW_DATA_DIR = DATA_ROOT
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

SHARK_DATA_DIR = RAW_DATA_DIR / "shark"
OCEAN_DATA_DIR = RAW_DATA_DIR / "ocean"
WHALE_DATA_DIR = RAW_DATA_DIR / "whale"
SEAL_DATA_DIR = RAW_DATA_DIR / "seal"

GEO = {
    "earth_radius_m": 6_371_000.0,
}

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
