"""Where things are: the project's directories and data locations, nothing else.

Every value that can change a result (data selections, analysis windows,
thresholds, model settings, seeds, figure settings) belongs in the experiment's
params.py, so that editing a shared value can never change a finished
experiment. A data file's format (columns, variable names) belongs in its loader
under src/models/. tests/test_config.py checks that this module holds only paths.
"""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent

# The one environment switch: where the raw data is mounted (docker-compose.yml).
DATA_ROOT = Path(os.environ.get("DATA_ROOT", PROJECT_ROOT / "data" / "raw"))
RESULT_DIR = PROJECT_ROOT / "result"
DRAFT_DIR = PROJECT_ROOT / "draft"
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"

RAW_DATA_DIR = DATA_ROOT
EXTERNAL_DATA_DIR = PROJECT_ROOT / "data" / "external"
INTERIM_DATA_DIR = PROJECT_ROOT / "data" / "interim"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

FIGURE_DIR = RESULT_DIR / "figures"
TABLE_DIR = RESULT_DIR / "tables"
ANIMATION_DIR = RESULT_DIR / "animations"
