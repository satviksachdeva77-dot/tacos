"""
chemistry_calculator.py — All chemistry calculations for TACOS.

PairChemistry:
  = clamp( (common_projects × 2) + confirmed_report_penalty, -2, +10 )

NormalizedChemistry:
  = ((raw + 2) / 12) × 100   clamped 0–100

CandidateTeamChemistry:
  = average PairChemistry between candidate and every current team member

TeamChemistry:
  = average PairChemistry across all unique pairs in the final team
"""

from typing import List
from database import get_common_projects, get_confirmed_report
from config import (
    PAIR_CHEMISTRY_MIN,
    PAIR_CHEMISTRY_MAX,
    SHARED_PROJECT_BONUS,
    CONFIRMED_REPORT_PENALTY,
)


# ---------------------------------------------------------------------------
# Pair chemistry
# ---------------------------------------------------------------------------

def calculate_pair_chemistry(employee_a_id: int, employee_b_id: int) -> float:
    """
    Calculate raw PairChemistry between two employees.
    Result is clamped to [PAIR_CHEMISTRY_MIN, PAIR_CHEMISTRY_MAX].
    """
    common = get_common_projects(employee_a_id, employee_b_id)
    positive = common * SHARED_PROJECT_BONUS

    penalty = CONFIRMED_REPORT_PENALTY if get_confirmed_report(employee_a_id, employee_b_id) else 0

    raw = positive + penalty
    return float(max(PAIR_CHEMISTRY_MIN, min(PAIR_CHEMISTRY_MAX, raw)))


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_chemistry(raw: float) -> float:
    """
    Normalize a raw chemistry score from [-2, +10] to [0, 100].
    Formula: ((raw + 2) / 12) × 100
    """
    span = PAIR_CHEMISTRY_MAX - PAIR_CHEMISTRY_MIN   # = 12
    normalized = ((raw - PAIR_CHEMISTRY_MIN) / span) * 100.0
    return max(0.0, min(100.0, normalized))


# ---------------------------------------------------------------------------
# Candidate chemistry with the growing team
# ---------------------------------------------------------------------------

def calculate_candidate_team_chemistry(candidate_id: int, team_ids: List[int]) -> float:
    """
    Calculate the average PairChemistry between the candidate and every
    current team member.

    If the team is empty, returns 0.0 (no chemistry context yet).
    """
    if not team_ids:
        return 0.0

    total = sum(calculate_pair_chemistry(candidate_id, tid) for tid in team_ids)
    return total / len(team_ids)


# ---------------------------------------------------------------------------
# Final team chemistry
# ---------------------------------------------------------------------------

def calculate_final_team_chemistry(team_ids: List[int]) -> dict:
    """
    Calculate the overall team chemistry for the final selected team.
    Returns {raw, normalized}.

    TeamChemistry = average of all unique pair chemistries.
    """
    if len(team_ids) < 2:
        return {"raw": 0.0, "normalized": normalize_chemistry(0.0)}

    pairs = []
    for i in range(len(team_ids)):
        for j in range(i + 1, len(team_ids)):
            pairs.append(calculate_pair_chemistry(team_ids[i], team_ids[j]))

    raw = sum(pairs) / len(pairs)
    return {
        "raw": round(raw, 4),
        "normalized": round(normalize_chemistry(raw), 4),
    }
