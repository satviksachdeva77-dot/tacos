"""
skill_rater.py — SkillPreferenceScore calculation and candidate eligibility.

SkillPreferenceScore (0–100):

  score < threshold              → 0        (ineligible)
  threshold ≤ score ≤ threshold+10 → 100 down to 50  (preferred range, linear)
  score > threshold+10           → decays below 50, never negative (overqualified)

Philosophy: reward the appropriately-qualified employee; penalize overqualification.
"""

from typing import List, Optional
from config import STAR_THRESHOLDS, PREFERRED_RANGE_OFFSET


def get_thresholds(importance: int) -> dict:
    """Return {mvp_minimum, candidate_minimum} for the given star rating."""
    if importance not in STAR_THRESHOLDS:
        raise ValueError(f"importance must be 1–5, got {importance}")
    return STAR_THRESHOLDS[importance]


def calculate_skill_preference_score(skill_score: int, threshold: int) -> float:
    """
    Calculate SkillPreferenceScore for a non-MVP candidate.

    Below threshold        → 0.0
    In [threshold, +10]   → 100.0 linearly decreasing to 50.0
    Above threshold+10    → 50.0 further decreasing by 1 per point, min 0.0
    """
    if skill_score < threshold:
        return 0.0

    upper = threshold + PREFERRED_RANGE_OFFSET

    if skill_score <= upper:
        # Linear from 100 (at threshold) to 50 (at threshold+10)
        proportion = (skill_score - threshold) / PREFERRED_RANGE_OFFSET
        return 100.0 - proportion * 50.0

    # Above preferred range: continues to decay by 1 per point above upper
    excess = skill_score - upper
    return max(0.0, 50.0 - excess * 1.0)


def is_eligible(skill_score: int, threshold: int) -> bool:
    """Return True if the candidate meets the minimum threshold."""
    return skill_score >= threshold


def rank_candidates_by_skill(candidates: List[dict], threshold: int) -> List[dict]:
    """
    Given a list of {employee_id, employee_name, skill_score},
    attach skill_preference_score, filter ineligible ones,
    and sort by skill_preference_score descending (ties broken by employee_id ascending).

    Returns the enriched + sorted list.
    """
    enriched = []
    for c in candidates:
        score = c["skill_score"]
        if not is_eligible(score, threshold):
            continue
        pref = calculate_skill_preference_score(score, threshold)
        enriched.append({**c, "skill_preference_score": round(pref, 4)})

    enriched.sort(key=lambda x: (-x["skill_preference_score"], x["employee_id"]))
    return enriched
