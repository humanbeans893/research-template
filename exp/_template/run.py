"""Experiment entrypoint. Run from the project root:

    docker compose exec research-template uv run python exp/NNN_<slug>/run.py
"""

import sys
from pathlib import Path

# Bootstrap: make the project root importable (config, src.*). Python puts
# this script's directory, not the project root, on sys.path. Do not remove.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np  # noqa: E402

import config  # noqa: E402,F401  # shared paths and settings (config.RAW_DATA_DIR, config.FIGURE_DIR, ...)
import params  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent / "out"


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    rng = np.random.default_rng(params.SEED)

    # TODO: implement the experiment.
    #   - Reuse logic from src/ (add it there first if it is missing).
    #   - Read inputs from config data dirs (config.RAW_DATA_DIR, ...).
    #   - Write every output (figures, arrays, logs) under OUT_DIR.
    #   - When a figure is adopted for the paper, copy it to
    #     config.FIGURE_DIR here (in code), not by hand.
    sample = rng.standard_normal(3)  # placeholder so the template runs end-to-end

    # Record the exact parameters used, for reproducibility.
    (OUT_DIR / "params_used.txt").write_text(
        f"SEED = {params.SEED}\nPARAMS = {params.PARAMS}\nplaceholder_sample = {sample.tolist()}\n",
        encoding="utf-8",
    )
    print(f"[{Path(__file__).resolve().parent.name}] done -> {OUT_DIR}")


if __name__ == "__main__":
    main()
