"""Parameters for NNN_<slug>: every value that can change this experiment's result.

That includes the data selection (which file, variant, period or subset), analysis
windows, thresholds, model settings, the seed and, if the experiment draws figures,
their settings (dpi, format, font). Pin them here; never read them from config.py
(it holds only locations) or switch them with an environment variable, so that
editing a shared file can never change a finished experiment. run.py records SEED
and PARAMS in out/params_used.json.
"""

SEED = 42

PARAMS = {
    "n_samples": 1_000,
}

# --smoke: the same code path on a small input, to fail in seconds and to time
# each stage before the full run. Every key must exist in PARAMS.
SMOKE = {
    "n_samples": 10,
}
