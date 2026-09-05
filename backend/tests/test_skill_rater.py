"""
test_skill_rater.py — Tests for skill preference scoring and eligibility.
"""
import pytest
from skill_rater import calculate_skill_preference_score, is_eligible, rank_candidates_by_skill


THRESHOLD = 40  # Using 4-star candidate_minimum as a test baseline


class TestEligibility:
    def test_below_threshold_ineligible(self):
        assert not is_eligible(39, THRESHOLD)
        assert not is_eligible(0, THRESHOLD)

    def test_at_threshold_eligible(self):
        assert is_eligible(40, THRESHOLD)

    def test_above_threshold_eligible(self):
        assert is_eligible(50, THRESHOLD)
        assert is_eligible(100, THRESHOLD)


class TestSkillPreferenceScore:
    def test_below_threshold_returns_zero(self):
        assert calculate_skill_preference_score(35, THRESHOLD) == 0.0
        assert calculate_skill_preference_score(0, THRESHOLD) == 0.0

    def test_at_threshold_returns_100(self):
        assert calculate_skill_preference_score(40, THRESHOLD) == 100.0

    def test_at_upper_preferred_returns_50(self):
        assert calculate_skill_preference_score(50, THRESHOLD) == 50.0

    def test_preferred_range_is_monotonically_decreasing(self):
        scores = [calculate_skill_preference_score(s, THRESHOLD) for s in range(40, 51)]
        assert scores == sorted(scores, reverse=True)

    def test_overqualified_is_lower_than_preferred(self):
        in_range = calculate_skill_preference_score(42, THRESHOLD)
        overqualified = calculate_skill_preference_score(70, THRESHOLD)
        assert in_range > overqualified

    def test_highly_overqualified_is_lower_than_moderately_overqualified(self):
        moderate = calculate_skill_preference_score(62, THRESHOLD)
        high = calculate_skill_preference_score(90, THRESHOLD)
        assert moderate > high

    def test_score_never_negative(self):
        for score in range(0, 101):
            assert calculate_skill_preference_score(score, THRESHOLD) >= 0.0

    def test_score_never_exceeds_100(self):
        for score in range(0, 101):
            assert calculate_skill_preference_score(score, THRESHOLD) <= 100.0


class TestRankCandidates:
    def test_ineligible_filtered_out(self):
        candidates = [
            {"employee_id": 1, "employee_name": "A", "skill_score": 35},
            {"employee_id": 2, "employee_name": "B", "skill_score": 42},
        ]
        result = rank_candidates_by_skill(candidates, THRESHOLD)
        assert len(result) == 1
        assert result[0]["employee_id"] == 2

    def test_preferred_range_ranked_higher_than_overqualified(self):
        candidates = [
            {"employee_id": 1, "employee_name": "A", "skill_score": 42},
            {"employee_id": 2, "employee_name": "B", "skill_score": 90},
        ]
        result = rank_candidates_by_skill(candidates, THRESHOLD)
        assert result[0]["employee_id"] == 1  # 42 preferred over 90

    def test_ties_broken_by_employee_id(self):
        """Two candidates with identical skill_score should break tie by employee_id."""
        candidates = [
            {"employee_id": 5, "employee_name": "E", "skill_score": 42},
            {"employee_id": 2, "employee_name": "B", "skill_score": 42},
        ]
        result = rank_candidates_by_skill(candidates, THRESHOLD)
        assert result[0]["employee_id"] == 2  # lower id wins tie
