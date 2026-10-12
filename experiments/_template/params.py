"""Parameters for NNN_<slug>. Every value that defines this experiment lives here.

run.py records SEED and PARAMS in out/params_used.json. Pin values here rather
than reading them from config.py, so that a later edit of config.py cannot
change what a finished experiment computes.
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
