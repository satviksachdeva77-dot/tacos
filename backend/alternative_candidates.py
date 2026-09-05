"""
alternative_candidates.py — Extract and format alternative candidates per role.

After the team builder produces ranked candidate pools per role,
this module pulls the top N alternatives (excluding the selected employee).
"""

from typing import List, Dict
from config import MAX_ALTERNATIVES


def extract_alternatives(ranked_candidates: List[dict], selected_employee_id: int) -> List[dict]:
    """
    From an already-ranked list of candidates, exclude the selected employee
    and return up to MAX_ALTERNATIVES alternatives with their rank.

    Each alternative dict contains:
      rank, employee_id, employee_name, skill_score,
      skill_preference_score, final_candidate_score
    """
    alternatives = []
    rank = 2   # rank 1 is the selected candidate

    for candidate in ranked_candidates:
        if candidate["employee_id"] == selected_employee_id:
            continue
        if len(alternatives) >= MAX_ALTERNATIVES:
            break

        alternatives.append({
            "rank": rank,
            "employee_id": candidate["employee_id"],
            "employee_name": candidate["employee_name"],
            "skill_score": candidate["skill_score"],
            "skill_preference_score": round(candidate.get("skill_preference_score", 0), 4),
            "final_candidate_score": round(candidate.get("final_candidate_score", 0), 4),
        })
        rank += 1

    return alternatives


def format_role_result(
    skill_name: str,
    selected: dict,
    ranked_candidates: List[dict],
    selected_employee_ids: List[int],
) -> dict:
    """
    Build the final role result dict containing the selected candidate
    and ranked alternatives.

    selected_employee_ids: IDs of ALL employees already on the team
    (used to exclude them from alternatives).
    """
    alternatives = []
    rank = 2

    for candidate in ranked_candidates:
        if candidate["employee_id"] in selected_employee_ids:
            continue
        if len(alternatives) >= MAX_ALTERNATIVES:
            break

        alternatives.append({
            "rank": rank,
            "employee_id": candidate["employee_id"],
            "employee_name": candidate["employee_name"],
            "skill_score": candidate["skill_score"],
            "skill_preference_score": round(candidate.get("skill_preference_score", 0), 4),
            "final_candidate_score": round(candidate.get("final_candidate_score", 0), 4),
        })
        rank += 1

    return {
        "role": skill_name,
        "selected": {
            "employee_id": selected["employee_id"],
            "employee_name": selected["employee_name"],
            "skill_score": selected["skill_score"],
            "skill_preference_score": round(selected.get("skill_preference_score", 0), 4),
            "raw_team_chemistry": round(selected.get("raw_team_chemistry", 0), 4),
            "normalized_team_chemistry": round(selected.get("normalized_team_chemistry", 0), 4),
            "final_candidate_score": round(selected.get("final_candidate_score", 0), 4),
        },
        "alternatives": alternatives,
    }
