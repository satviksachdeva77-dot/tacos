"""
team_builder.py — Main TACOS orchestration module.

Algorithm:
  1. Validate input
  2. Filter available employees
  3. Determine star thresholds
  4. Select MVP
  5. Progressively build the team role by role
  6. Handle team_size > or < required_skills count
  7. Calculate final team chemistry
  8. Return structured result

No AI, no random selection, no threshold relaxation.
"""

from typing import List, Optional
from database import (
    get_available_employees,
    get_skill_id,
    get_candidates_for_skill,
    get_all_skills,
)
from config import SKILL_WEIGHT, CHEMISTRY_WEIGHT, STAR_THRESHOLDS
from skill_rater import get_thresholds, rank_candidates_by_skill
from mvp_calculator import select_mvp
from chemistry_calculator import (
    calculate_candidate_team_chemistry,
    normalize_chemistry,
    calculate_final_team_chemistry,
)
from alternative_candidates import format_role_result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _score_candidates_with_chemistry(
    ranked_by_skill: List[dict],
    current_team_ids: List[int],
) -> List[dict]:
    """
    Attach raw_team_chemistry, normalized_team_chemistry, and final_candidate_score
    to every candidate, then re-sort by final_candidate_score DESC, employee_id ASC.
    """
    for c in ranked_by_skill:
        raw_chem = calculate_candidate_team_chemistry(c["employee_id"], current_team_ids)
        norm_chem = normalize_chemistry(raw_chem)
        final = SKILL_WEIGHT * c["skill_preference_score"] + CHEMISTRY_WEIGHT * norm_chem
        c["raw_team_chemistry"] = round(raw_chem, 4)
        c["normalized_team_chemistry"] = round(norm_chem, 4)
        c["final_candidate_score"] = round(final, 4)

    ranked_by_skill.sort(
        key=lambda x: (-x["final_candidate_score"], x["employee_id"])
    )
    return ranked_by_skill


def _fill_role(
    skill_name: str,
    importance: int,
    available_ids: List[int],
    selected_ids: List[int],
    current_team_ids: List[int],
) -> dict:
    """
    Fill one role. Returns a role_result dict or an error dict.
    """
    thresholds = get_thresholds(importance)
    candidate_minimum = thresholds["candidate_minimum"]

    skill_id = get_skill_id(skill_name)
    if skill_id is None:
        return {
            "error": True,
            "role": skill_name,
            "message": f"Skill '{skill_name}' not found in database.",
        }

    # Eligible pool (available and not yet selected)
    eligible_pool_ids = [eid for eid in available_ids if eid not in selected_ids]

    raw_candidates = get_candidates_for_skill(skill_id, eligible_pool_ids)

    # Apply skill threshold + compute preference scores
    ranked_by_skill = rank_candidates_by_skill(raw_candidates, candidate_minimum)

    if not ranked_by_skill:
        return {
            "error": True,
            "role": skill_name,
            "message": (
                f"No eligible candidate found for '{skill_name}'. "
                f"Minimum required score: {candidate_minimum}. "
                f"Available employees checked: {len(eligible_pool_ids)}."
            ),
        }

    # Attach chemistry and compute final scores
    fully_ranked = _score_candidates_with_chemistry(ranked_by_skill, current_team_ids)

    selected = fully_ranked[0]
    return {"error": False, "skill_name": skill_name, "selected": selected, "ranked": fully_ranked}


def _fill_extra_slot(
    importance: int,
    available_ids: List[int],
    selected_ids: List[int],
    current_team_ids: List[int],
    all_skill_names: List[str],
) -> Optional[dict]:
    """
    Fill an extra team slot (team_size > required_skills count) by finding
    the best overall candidate across all skills.
    """
    thresholds = get_thresholds(importance)
    candidate_minimum = thresholds["candidate_minimum"]
    eligible_pool_ids = [eid for eid in available_ids if eid not in selected_ids]

    best_candidate = None
    best_score = -1.0
    best_skill_name = None
    best_ranked = []

    for skill_name in all_skill_names:
        skill_id = get_skill_id(skill_name)
        if skill_id is None:
            continue
        raw = get_candidates_for_skill(skill_id, eligible_pool_ids)
        ranked_skill = rank_candidates_by_skill(raw, candidate_minimum)
        if not ranked_skill:
            continue
        ranked_full = _score_candidates_with_chemistry(ranked_skill, current_team_ids)
        if ranked_full and ranked_full[0]["final_candidate_score"] > best_score:
            best_score = ranked_full[0]["final_candidate_score"]
            best_candidate = ranked_full[0]
            best_skill_name = skill_name
            best_ranked = ranked_full

    if best_candidate is None:
        return None

    return {
        "error": False,
        "skill_name": f"{best_skill_name} (extra)",
        "selected": best_candidate,
        "ranked": best_ranked,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_team(
    project_name: str,
    team_size: int,
    importance: int,
    required_skills: List[str],
    mvp_skill: str,
) -> dict:
    """
    Main entry point. Returns a fully structured TACOS result dict.
    """
    warnings: List[str] = []
    role_results: List[dict] = []

    # --- Validate -------------------------------------------------------
    if importance not in STAR_THRESHOLDS:
        return {"error": "importance must be between 1 and 5."}

    if mvp_skill not in required_skills:
        return {"error": f"mvp_skill '{mvp_skill}' must be one of the required_skills."}

    if team_size < 1:
        return {"error": "team_size must be at least 1."}

    # --- Step 2: available employees ------------------------------------
    available_employees = get_available_employees()
    available_ids = [e["employee_id"] for e in available_employees]

    # --- Step 3: thresholds ---------------------------------------------
    thresholds = get_thresholds(importance)

    # --- Step 4: select MVP ---------------------------------------------
    mvp = select_mvp(mvp_skill, importance, available_ids)
    if mvp is None:
        return {
            "error": (
                f"No eligible MVP found for skill '{mvp_skill}' "
                f"with importance {importance} ★ "
                f"(minimum score required: {thresholds['mvp_minimum']})."
            )
        }

    # --- Step 5: initialise team ----------------------------------------
    selected_ids: List[int] = [mvp["employee_id"]]
    current_team_ids: List[int] = [mvp["employee_id"]]

    # Build ordered skill list: non-MVP skills first, then MVP last
    # (MVP already filled; we process the remaining skills)
    non_mvp_skills = [s for s in required_skills if s != mvp_skill]

    # How many slots remain after MVP
    remaining_slots = team_size - 1

    # Determine how many required roles we can actually fill
    roles_to_fill = non_mvp_skills[:remaining_slots]  # may be fewer than non_mvp_skills

    if len(non_mvp_skills) > remaining_slots:
        skipped = non_mvp_skills[remaining_slots:]
        warnings.append(
            f"Team size ({team_size}) is smaller than the number of required skills "
            f"({len(required_skills)}). "
            f"Skipped roles (lower priority): {', '.join(skipped)}."
        )

    # --- Step 6: fill roles progressively --------------------------------
    for skill_name in roles_to_fill:
        result = _fill_role(
            skill_name=skill_name,
            importance=importance,
            available_ids=available_ids,
            selected_ids=selected_ids,
            current_team_ids=current_team_ids,
        )

        if result["error"]:
            warnings.append(result["message"])
            role_results.append({
                "role": skill_name,
                "error": result["message"],
                "selected": None,
                "alternatives": [],
            })
        else:
            sel = result["selected"]
            # Include the newly selected candidate in the exclusion set
            # so they don't appear as their own alternative
            all_selected_so_far = list(selected_ids) + [sel["employee_id"]]
            role_result = format_role_result(
                skill_name=result["skill_name"],
                selected=sel,
                ranked_candidates=result["ranked"],
                selected_employee_ids=all_selected_so_far,
            )
            role_results.append(role_result)
            selected_ids.append(sel["employee_id"])
            current_team_ids.append(sel["employee_id"])

    # --- Step 7: fill extra slots if team_size > required_skills --------
    extra_slots = remaining_slots - len(roles_to_fill)
    all_skill_names = [s["skill_name"] for s in get_all_skills()]

    for _ in range(extra_slots):
        extra = _fill_extra_slot(
            importance=importance,
            available_ids=available_ids,
            selected_ids=selected_ids,
            current_team_ids=current_team_ids,
            all_skill_names=all_skill_names,
        )
        if extra is None:
            warnings.append("Could not find any eligible candidate for an extra team slot.")
            break

        sel = extra["selected"]
        all_selected_so_far = list(selected_ids)
        role_result = format_role_result(
            skill_name=extra["skill_name"],
            selected=sel,
            ranked_candidates=extra["ranked"],
            selected_employee_ids=all_selected_so_far,
        )
        role_results.append(role_result)
        selected_ids.append(sel["employee_id"])
        current_team_ids.append(sel["employee_id"])

    # --- Post-build cleanup: strip team members from alternatives ----------
    # Because alternatives are computed progressively, a candidate selected for
    # a later role may still appear as an alternative for an earlier role.
    final_selected_set = set(selected_ids)
    for rr in role_results:
        if rr.get("alternatives"):
            rr["alternatives"] = [
                a for a in rr["alternatives"]
                if a["employee_id"] not in final_selected_set
            ]
            # Re-number ranks
            for i, a in enumerate(rr["alternatives"], start=2):
                a["rank"] = i

    # --- Step 8: final team chemistry -----------------------------------
    team_chemistry = calculate_final_team_chemistry(current_team_ids)

    # --- Step 9: build output -------------------------------------------
    selected_team = []

    # MVP entry
    selected_team.append({
        "employee_id": mvp["employee_id"],
        "employee_name": mvp["employee_name"],
        "role": mvp_skill,
        "is_mvp": True,
        "skill_score": mvp["skill_score"],
        "skill_preference_score": None,
        "raw_team_chemistry": None,
        "normalized_team_chemistry": None,
        "final_candidate_score": None,
    })

    for rr in role_results:
        if rr.get("selected") is None:
            continue
        sel = rr["selected"]
        selected_team.append({
            "employee_id": sel["employee_id"],
            "employee_name": sel["employee_name"],
            "role": rr["role"],
            "is_mvp": False,
            "skill_score": sel["skill_score"],
            "skill_preference_score": sel["skill_preference_score"],
            "raw_team_chemistry": sel["raw_team_chemistry"],
            "normalized_team_chemistry": sel["normalized_team_chemistry"],
            "final_candidate_score": sel["final_candidate_score"],
        })

    return {
        "project_summary": {
            "project_name": project_name,
            "team_size": team_size,
            "importance": importance,
            "required_skills": required_skills,
            "mvp_skill": mvp_skill,
            "thresholds": thresholds,
        },
        "mvp": mvp,
        "selected_team": selected_team,
        "role_results": role_results,
        "team_chemistry": team_chemistry,
        "warnings": warnings,
    }
