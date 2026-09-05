"""
test_chemistry.py — Tests for pair chemistry calculation and normalization.
These tests use mock database functions to avoid needing real data.
"""
import pytest
from unittest.mock import patch
from chemistry_calculator import (
    calculate_pair_chemistry,
    normalize_chemistry,
    calculate_candidate_team_chemistry,
    calculate_final_team_chemistry,
)
from config import PAIR_CHEMISTRY_MIN, PAIR_CHEMISTRY_MAX


class TestPairChemistry:
    def test_one_shared_project_no_report(self):
        with patch("chemistry_calculator.get_common_projects", return_value=1), \
             patch("chemistry_calculator.get_confirmed_report", return_value=False):
            assert calculate_pair_chemistry(1, 2) == 2.0

    def test_two_shared_projects_no_report(self):
        with patch("chemistry_calculator.get_common_projects", return_value=2), \
             patch("chemistry_calculator.get_confirmed_report", return_value=False):
            assert calculate_pair_chemistry(1, 2) == 4.0

    def test_three_shared_projects_no_report(self):
        with patch("chemistry_calculator.get_common_projects", return_value=3), \
             patch("chemistry_calculator.get_confirmed_report", return_value=False):
            assert calculate_pair_chemistry(1, 2) == 6.0

    def test_confirmed_report_penalty(self):
        with patch("chemistry_calculator.get_common_projects", return_value=0), \
             patch("chemistry_calculator.get_confirmed_report", return_value=True):
            assert calculate_pair_chemistry(1, 2) == -2.0

    def test_confirmed_report_with_shared_projects(self):
        with patch("chemistry_calculator.get_common_projects", return_value=2), \
             patch("chemistry_calculator.get_confirmed_report", return_value=True):
            # (2×2) + (-2) = 2
            assert calculate_pair_chemistry(1, 2) == 2.0

    def test_pending_report_no_effect(self):
        # pending → confirmed_report returns False → no penalty
        with patch("chemistry_calculator.get_common_projects", return_value=0), \
             patch("chemistry_calculator.get_confirmed_report", return_value=False):
            assert calculate_pair_chemistry(1, 2) == 0.0

    def test_dismissed_report_no_effect(self):
        with patch("chemistry_calculator.get_common_projects", return_value=0), \
             patch("chemistry_calculator.get_confirmed_report", return_value=False):
            assert calculate_pair_chemistry(1, 2) == 0.0

    def test_capped_at_max(self):
        """7 shared projects = 14 → must cap at +10."""
        with patch("chemistry_calculator.get_common_projects", return_value=7), \
             patch("chemistry_calculator.get_confirmed_report", return_value=False):
            assert calculate_pair_chemistry(1, 2) == PAIR_CHEMISTRY_MAX

    def test_cannot_go_below_min(self):
        """Even with -2 penalty and 0 projects, should equal -2."""
        with patch("chemistry_calculator.get_common_projects", return_value=0), \
             patch("chemistry_calculator.get_confirmed_report", return_value=True):
            result = calculate_pair_chemistry(1, 2)
            assert result == PAIR_CHEMISTRY_MIN
            assert result >= PAIR_CHEMISTRY_MIN


class TestNormalization:
    def test_min_normalizes_to_zero(self):
        assert normalize_chemistry(-2.0) == 0.0

    def test_max_normalizes_to_100(self):
        assert normalize_chemistry(10.0) == 100.0

    def test_zero_normalizes_correctly(self):
        # ((0 + 2) / 12) * 100 = 16.666...
        result = normalize_chemistry(0.0)
        assert abs(result - 16.6667) < 0.01

    def test_four_normalizes_to_50(self):
        # ((4 + 2) / 12) * 100 = 50.0
        assert normalize_chemistry(4.0) == 50.0


class TestCandidateTeamChemistry:
    def test_empty_team_returns_zero(self):
        result = calculate_candidate_team_chemistry(99, [])
        assert result == 0.0

    def test_single_team_member_equals_pair_chemistry(self):
        with patch("chemistry_calculator.get_common_projects", return_value=2), \
             patch("chemistry_calculator.get_confirmed_report", return_value=False):
            result = calculate_candidate_team_chemistry(1, [2])
            assert result == 4.0

    def test_average_across_multiple_members(self):
        # pair(candidate, A) = 2, pair(candidate, B) = 4 → avg = 3
        call_results = {(1, 2): 1, (1, 3): 2}  # common_projects
        def mock_common(a, b):
            return call_results.get((min(a,b), max(a,b)), 0)

        with patch("chemistry_calculator.get_common_projects", side_effect=mock_common), \
             patch("chemistry_calculator.get_confirmed_report", return_value=False):
            result = calculate_candidate_team_chemistry(1, [2, 3])
            assert result == 3.0  # (2 + 4) / 2


class TestFinalTeamChemistry:
    def test_single_member_returns_zero(self):
        result = calculate_final_team_chemistry([1])
        assert result["raw"] == 0.0

    def test_three_member_team(self):
        # A-B = 2, A-C = 4, B-C = 0 → avg = 2
        def mock_common(a, b):
            pairs = {(1, 2): 1, (1, 3): 2, (2, 3): 0}
            return pairs.get((min(a,b), max(a,b)), 0)

        with patch("chemistry_calculator.get_common_projects", side_effect=mock_common), \
             patch("chemistry_calculator.get_confirmed_report", return_value=False):
            result = calculate_final_team_chemistry([1, 2, 3])
            assert result["raw"] == 2.0
