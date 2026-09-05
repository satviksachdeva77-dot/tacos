"""
config.py — All configurable TACOS constants.
Change values here only; do not hardcode them elsewhere.
"""

import os

# ---------------------------------------------------------------------------
# Database path (relative to this file's directory so it works from any CWD)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "tacos.db")

# ---------------------------------------------------------------------------
# Star-based importance thresholds
# ---------------------------------------------------------------------------
STAR_THRESHOLDS = {
    5: {"mvp_minimum": 90, "candidate_minimum": 50},
    4: {"mvp_minimum": 80, "candidate_minimum": 40},
    3: {"mvp_minimum": 60, "candidate_minimum": 30},
    2: {"mvp_minimum": 50, "candidate_minimum": 25},
    1: {"mvp_minimum": 40, "candidate_minimum": 10},
}

# ---------------------------------------------------------------------------
# Skill preference range
# ---------------------------------------------------------------------------
PREFERRED_RANGE_OFFSET = 10          # preferred = [min_threshold, min_threshold + 10]

# ---------------------------------------------------------------------------
# Final candidate score weights
# ---------------------------------------------------------------------------
SKILL_WEIGHT = 0.80
CHEMISTRY_WEIGHT = 0.20

# ---------------------------------------------------------------------------
# Pair chemistry bounds
# ---------------------------------------------------------------------------
PAIR_CHEMISTRY_MIN = -2
PAIR_CHEMISTRY_MAX = 10

# ---------------------------------------------------------------------------
# Positive chemistry per shared project
# ---------------------------------------------------------------------------
SHARED_PROJECT_BONUS = 2

# ---------------------------------------------------------------------------
# Confirmed-report penalty (negative value)
# ---------------------------------------------------------------------------
CONFIRMED_REPORT_PENALTY = -2

# ---------------------------------------------------------------------------
# How many alternatives to keep per role
# ---------------------------------------------------------------------------
MAX_ALTERNATIVES = 2
