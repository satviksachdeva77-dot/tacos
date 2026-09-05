"""
test_team_builder.py — Integration tests for team building using the real database.
"""
import pytest
from team_builder import build_team
from database import get_available_employees


AVAILABLE_IDS = {e["employee_id"] for e in get_available_employees()}


def run_default_build():
    return build_team(
        project_name="Test Project",
        team_size=5,
        importance=5,
        required_skills=["Python", "React", "SQL", "Machine Learning"],
        mvp_skill="Python",
    )


class TestTeamBuilderBasic:
    def test_result_has_expected_keys(self):
        result = run_default_build()
        assert "project_summary" in result
        assert "mvp" in result
        assert "selected_team" in result
        assert "team_chemistry" in result

    def test_mvp_is_in_selected_team(self):
        result = run_default_build()
        mvp_id = result["mvp"]["employee_id"]
        team_ids = [m["employee_id"] for m in result["selected_team"]]
        assert mvp_id in team_ids

    def test_no_duplicate_employees(self):
        result = run_default_build()
        team_ids = [m["employee_id"] for m in result["selected_team"]]
        assert len(team_ids) == len(set(team_ids))

    def test_all_selected_employees_are_available(self):
        result = run_default_build()
        for member in result["selected_team"]:
            assert member["employee_id"] in AVAILABLE_IDS

    def test_team_size_respected(self):
        result = run_default_build()
        # Team may be smaller if not enough eligible candidates, but never larger
        assert len(result["selected_team"]) <= 5

    def test_mvp_has_no_final_score(self):
        """MVP is not scored with the candidate formula."""
        result = run_default_build()
        mvp_entry = next(m for m in result["selected_team"] if m["is_mvp"])
        assert mvp_entry["final_candidate_score"] is None

    def test_non_mvp_members_have_scores(self):
        result = run_default_build()
        for m in result["selected_team"]:
            if not m["is_mvp"]:
                assert m["final_candidate_score"] is not None
                assert 0 <= m["final_candidate_score"] <= 100

    def test_invalid_importance_returns_error(self):
        result = build_team("P", 3, 9, ["Python"], "Python")
        assert "error" in result

    def test_mvp_skill_not_in_required_returns_error(self):
        result = build_team("P", 3, 5, ["Python", "SQL"], "React")
        assert "error" in result

    def test_determinism(self):
        """Running twice with the same input should produce the same result."""
        r1 = run_default_build()
        r2 = run_default_build()
        assert r1["mvp"]["employee_id"] == r2["mvp"]["employee_id"]
        ids1 = [m["employee_id"] for m in r1["selected_team"]]
        ids2 = [m["employee_id"] for m in r2["selected_team"]]
        assert ids1 == ids2


class TestTeamBuilderSizeHandling:
    def test_team_size_smaller_than_skills(self):
        result = build_team(
            project_name="Small Team",
            team_size=2,
            importance=3,
            required_skills=["Python", "SQL", "React"],
            mvp_skill="Python",
        )
        # Should warn and fill only up to team_size
        assert len(result["selected_team"]) <= 2

    def test_team_size_larger_fills_extra_slots(self):
        result = build_team(
            project_name="Large Team",
            team_size=6,
            importance=3,
            required_skills=["Python", "SQL"],
            mvp_skill="Python",
        )
        # Should attempt to fill extra slots
        assert len(result["selected_team"]) >= 2


class TestAlternatives:
    def test_alternatives_do_not_include_selected(self):
        result = run_default_build()
        selected_ids = {m["employee_id"] for m in result["selected_team"]}
        for rr in result["role_results"]:
            for alt in rr.get("alternatives", []):
                assert alt["employee_id"] not in selected_ids

    def test_alternatives_are_eligible(self):
        """All alternatives must meet skill threshold."""
        from config import STAR_THRESHOLDS
        from database import get_skill_id, get_employee_skill_score
        result = run_default_build()
        threshold = STAR_THRESHOLDS[5]["candidate_minimum"]
        for rr in result["role_results"]:
            if rr.get("error"):
                continue
            skill_id = get_skill_id(rr["role"])
            for alt in rr.get("alternatives", []):
                score = get_employee_skill_score(alt["employee_id"], skill_id)
                if score is not None:
                    assert score >= threshold
