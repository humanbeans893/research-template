"""NNN_<slug>: <one-line purpose>.

Run from the project root, smoke first:

    docker compose exec research-template uv run python experiments/NNN_<slug>/run.py --smoke
    docker compose exec research-template uv run python experiments/NNN_<slug>/run.py

Stages run cheapest first and the slow part last. Each stage calls src/; move a
stage into src/ (with a test) when it outgrows a screen or a second experiment
needs it.
"""

import sys
from pathlib import Path

# Bootstrap: make the project root importable (config, src.*). Python puts
# this script's directory, not the project root, on sys.path. Do not remove.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

import config  # noqa: F401  # shared paths (config.RAW_DATA_DIR, config.TABLE_DIR, ...)
import params
from src.utils import experiment


def main() -> None:
    with experiment.start(__file__, params) as run:
        p = run.params  # params.PARAMS, with params.SMOKE applied under --smoke
        rng = np.random.default_rng(run.seed)

        run.stage("load and check inputs")
        # Read inputs through config paths and loaders in src/, and check them
        # here, before anything expensive.

        run.stage("compute")
        sample = rng.standard_normal(p["n_samples"])  # placeholder so the template runs end to end
        run.log(f"{sample.size} samples")

        run.stage("write outputs")
        pd.DataFrame({"n": [sample.size], "mean": [sample.mean()]}).to_csv(run.out("sample_mean.csv"), index=False)
        # A table or figure used outside this experiment (the manuscript, another
        # experiment) is promoted in code, last. It is copied when the run completes,
        # and refused under --smoke or with uncommitted code:
        # run.promote("sample_mean.csv")                        # -> result/tables/
        # run.promote("fig_x.png", dest_dir=config.FIGURE_DIR)  # -> result/figures/


if __name__ == "__main__":
    main()
