"""Parameters for this experiment.

Keep every tunable value here so that run.py stays declarative. This module
is imported by run.py *after* the project root is put on sys.path, so
top-level imports (config, src) are available here.
"""

import config

SEED = config.RANDOM["default_seed"]

PARAMS = {
    # Add experiment parameters here, e.g.:
    # "n_samples": 1_000,
    # "threshold": 0.5,
}
