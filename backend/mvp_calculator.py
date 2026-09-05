"""
mvp_calculator.py — MVP selection logic.

Rules:
  - Only available employees
  - Must have a score in the MVP skill
  - Score must be >= mvp_minimum for the project's importance
  - Highest score wins
  - Tie-break: lowest employee_id (deterministic)
"""

from typing import List, Optional
from database import get_candidates_for_skill, get_skill_id, get_available_employees
from skill_rater import get_thresholds


def select_mvp(mvp_skill_name: str, importance: int, available_ids: List[int]) -> Optional[dict]:
    """
    Select the MVP for the project.

    Returns a dict with:
      employee_id, employee_name, mvp_skill, skill_score
    or None if no eligible candidate exists.
    """
    skill_id = get_skill_id(mvp_skill_name)
    if skill_id is None:
        return None

    thresholds = get_thresholds(importance)
    mvp_minimum = thresholds["mvp_minimum"]

    candidates = get_candidates_for_skill(skill_id, available_ids)

    # Filter by mvp_minimum
    eligible = [c for c in candidates if c["skill_score"] >= mvp_minimum]

    if not eligible:
        return None

    # Already sorted DESC by skill_score, ASC by employee_id from DB query
    best = eligible[0]
    return {
        "employee_id": best["employee_id"],
        "employee_name": best["employee_name"],
        "mvp_skill": mvp_skill_name,
        "skill_score": best["skill_score"],
    }
