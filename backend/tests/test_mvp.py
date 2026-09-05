"""
test_mvp.py — Tests for MVP selection using the real database.
"""
import pytest
from mvp_calculator import select_mvp
from database import get_available_employees


# Must be a list (not a set) so DB IN-clause ordering is consistent
AVAILABLE_IDS = sorted(e["employee_id"] for e in get_available_employees())


class TestMVPSelection:
    def test_mvp_is_selected(self):
        """MVP should be returned for a skill that exists."""
        mvp = select_mvp("Python", 3, AVAILABLE_IDS)
        assert mvp is not None

    def test_mvp_has_correct_fields(self):
        mvp = select_mvp("Python", 3, AVAILABLE_IDS)
        assert "employee_id" in mvp
        assert "employee_name" in mvp
        assert "mvp_skill" in mvp
        assert "skill_score" in mvp

    def test_mvp_meets_threshold_5_star(self):
        """For 5★, MVP must have skill_score >= 90."""
        mvp = select_mvp("Python", 5, AVAILABLE_IDS)
        if mvp is not None:
            assert mvp["skill_score"] >= 90

    def test_mvp_meets_threshold_3_star(self):
        """For 3★, MVP must have skill_score >= 60."""
        mvp = select_mvp("Python", 3, AVAILABLE_IDS)
        if mvp is not None:
            assert mvp["skill_score"] >= 60

    def test_unavailable_employee_cannot_be_mvp(self):
        """Passing an empty available_ids list should return None."""
        mvp = select_mvp("Python", 1, [])
        assert mvp is None

    def test_invalid_skill_returns_none(self):
        """A skill not in the DB should return None."""
        mvp = select_mvp("QuantumFortran", 3, AVAILABLE_IDS)
        assert mvp is None

    def test_mvp_is_highest_scorer(self):
        """MVP must be the highest available eligible scorer."""
        mvp = select_mvp("Python", 1, AVAILABLE_IDS)
        if mvp is None:
            pytest.skip("No MVP found for Python at 1 star")
        # Confirm the MVP's score is the maximum in the eligible pool
        from database import get_candidates_for_skill, get_skill_id
        from config import STAR_THRESHOLDS
        skill_id = get_skill_id("Python")
        candidates = get_candidates_for_skill(skill_id, AVAILABLE_IDS)
        threshold = STAR_THRESHOLDS[1]["mvp_minimum"]
        eligible = [c for c in candidates if c["skill_score"] >= threshold]
        max_score = max(c["skill_score"] for c in eligible)
        assert mvp["skill_score"] == max_score
        # Among ties, the lowest employee_id should win (deterministic)
        top = [c for c in eligible if c["skill_score"] == max_score]
        assert mvp["employee_id"] == min(c["employee_id"] for c in top)
