"""
Unit tests for module2_plan_generator.constraints.

Tests every constraint function individually with normal cases, boundary
cases, and edge cases, then tests the composite compute_week_penalty.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from module2_plan_generator.constraints import (
    check_ten_percent_rule,
    check_long_run_present,
    check_excessive_long_run,
    check_recovery_pattern,
    check_terrain_variety,
    check_rest_days,
    check_taper,
    check_dropback_week,
    compute_week_penalty,
    PENALTY_TEN_PERCENT_RULE,
    PENALTY_MISSING_LONG_RUN,
    PENALTY_EXCESSIVE_LONG_RUN,
    PENALTY_POOR_RECOVERY,
    PENALTY_TERRAIN_MONOTONY,
    PENALTY_INSUFFICIENT_REST,
    PENALTY_TAPER_VIOLATION,
    PENALTY_NO_DROPBACK,
    HARD_WORKOUT_TYPES,
    EASY_WORKOUT_TYPES,
)


# ===================================================================
# 10% Rule
# ===================================================================

class TestTenPercentRule:

    def test_exactly_10_percent_ok(self):
        """10% increase is the limit, should pass."""
        assert check_ten_percent_rule(20, 22) == 0

    def test_under_10_percent_ok(self):
        assert check_ten_percent_rule(20, 21) == 0

    def test_over_10_percent_violation(self):
        assert check_ten_percent_rule(20, 23) == PENALTY_TEN_PERCENT_RULE

    def test_25_percent_increase_violation(self):
        assert check_ten_percent_rule(20, 25) == PENALTY_TEN_PERCENT_RULE

    def test_decrease_ok(self):
        """Decreasing mileage should never violate the 10% rule."""
        assert check_ten_percent_rule(20, 15) == 0

    def test_same_mileage_ok(self):
        assert check_ten_percent_rule(20, 20) == 0

    def test_zero_previous_ok(self):
        """Cannot compute percentage from 0, should be safe."""
        assert check_ten_percent_rule(0, 10) == 0

    def test_negative_previous_ok(self):
        assert check_ten_percent_rule(-5, 10) == 0

    def test_small_numbers(self):
        """5 to 5.6 is 12%, should violate."""
        assert check_ten_percent_rule(5, 5.6) == PENALTY_TEN_PERCENT_RULE

    def test_large_numbers(self):
        """100 to 110 is exactly 10%, ok."""
        assert check_ten_percent_rule(100, 110) == 0


# ===================================================================
# Long Run Present
# ===================================================================

class TestLongRunPresent:

    def test_long_run_present_adequate(self):
        workouts = [
            {"type": "easy run", "distance": 4},
            {"type": "long run", "distance": 8},
        ]
        assert check_long_run_present(workouts, 12) == 0

    def test_no_long_run(self):
        workouts = [
            {"type": "easy run", "distance": 4},
            {"type": "easy run", "distance": 4},
        ]
        assert check_long_run_present(workouts, 8) == PENALTY_MISSING_LONG_RUN

    def test_long_run_too_short(self):
        """Long run is only 10% of weekly mileage (below 20% threshold)."""
        workouts = [
            {"type": "easy run", "distance": 9},
            {"type": "long run", "distance": 1},
        ]
        assert check_long_run_present(workouts, 10) == PENALTY_MISSING_LONG_RUN

    def test_long_run_exactly_20_percent(self):
        workouts = [
            {"type": "easy run", "distance": 8},
            {"type": "long run", "distance": 2},
        ]
        assert check_long_run_present(workouts, 10) == 0

    def test_multiple_long_runs(self):
        """Should check the longest one."""
        workouts = [
            {"type": "long run", "distance": 3},
            {"type": "long run", "distance": 6},
        ]
        assert check_long_run_present(workouts, 20) == 0

    def test_empty_workouts(self):
        assert check_long_run_present([], 0) == PENALTY_MISSING_LONG_RUN

    def test_zero_weekly_miles(self):
        workouts = [{"type": "long run", "distance": 0}]
        assert check_long_run_present(workouts, 0) == 0  # Can't divide by 0


# ===================================================================
# Excessive Long Run
# ===================================================================

class TestExcessiveLongRun:

    def test_long_run_35_percent_ok(self):
        workouts = [
            {"type": "easy run", "distance": 6.5},
            {"type": "long run", "distance": 3.5},
        ]
        assert check_excessive_long_run(workouts, 10) == 0

    def test_long_run_over_35_percent(self):
        workouts = [
            {"type": "easy run", "distance": 5},
            {"type": "long run", "distance": 5},
        ]
        # 50% of weekly mileage
        assert check_excessive_long_run(workouts, 10) == PENALTY_EXCESSIVE_LONG_RUN

    def test_no_long_run(self):
        workouts = [{"type": "easy run", "distance": 5}]
        assert check_excessive_long_run(workouts, 5) == 0

    def test_zero_weekly_miles(self):
        workouts = [{"type": "long run", "distance": 0}]
        assert check_excessive_long_run(workouts, 0) == 0


# ===================================================================
# Recovery Pattern
# ===================================================================

class TestRecoveryPattern:

    def test_alternating_hard_easy(self):
        workouts = [
            {"type": "tempo"},
            {"type": "easy run"},
            {"type": "long run"},
        ]
        assert check_recovery_pattern(workouts) == 0

    def test_back_to_back_hard(self):
        workouts = [
            {"type": "tempo"},
            {"type": "long run"},
        ]
        assert check_recovery_pattern(workouts) == PENALTY_POOR_RECOVERY

    def test_all_easy(self):
        workouts = [
            {"type": "easy run"},
            {"type": "easy run"},
            {"type": "recovery run"},
        ]
        assert check_recovery_pattern(workouts) == 0

    def test_all_hard(self):
        workouts = [
            {"type": "intervals"},
            {"type": "tempo"},
        ]
        assert check_recovery_pattern(workouts) == PENALTY_POOR_RECOVERY

    def test_single_workout(self):
        workouts = [{"type": "long run"}]
        assert check_recovery_pattern(workouts) == 0

    def test_empty_workouts(self):
        assert check_recovery_pattern([]) == 0

    def test_hard_easy_hard_ok(self):
        workouts = [
            {"type": "intervals"},
            {"type": "easy run"},
            {"type": "long run"},
        ]
        assert check_recovery_pattern(workouts) == 0

    def test_race_pace_is_hard(self):
        assert "race pace" in HARD_WORKOUT_TYPES
        workouts = [
            {"type": "race pace"},
            {"type": "tempo"},
        ]
        assert check_recovery_pattern(workouts) == PENALTY_POOR_RECOVERY

    def test_recovery_run_is_easy(self):
        assert "recovery run" in EASY_WORKOUT_TYPES


# ===================================================================
# Terrain Variety
# ===================================================================

class TestTerrainVariety:

    def test_multiple_terrains_used(self):
        workouts = [
            {"terrain": "road"},
            {"terrain": "trail"},
        ]
        assert check_terrain_variety(workouts, ["road", "trail"]) == 0

    def test_single_terrain_used_violation(self):
        workouts = [
            {"terrain": "road"},
            {"terrain": "road"},
        ]
        assert check_terrain_variety(workouts, ["road", "trail"]) == PENALTY_TERRAIN_MONOTONY

    def test_only_one_terrain_available(self):
        """No penalty when runner only has one option."""
        workouts = [
            {"terrain": "road"},
            {"terrain": "road"},
        ]
        assert check_terrain_variety(workouts, ["road"]) == 0

    def test_three_terrains_used(self):
        workouts = [
            {"terrain": "road"},
            {"terrain": "trail"},
            {"terrain": "track"},
        ]
        assert check_terrain_variety(workouts, ["road", "trail", "track"]) == 0


# ===================================================================
# Rest Days
# ===================================================================

class TestRestDays:

    def test_adequate_rest(self):
        assert check_rest_days(7, 4) == 0  # 3 rest days

    def test_minimum_rest(self):
        assert check_rest_days(7, 6) == 0  # 1 rest day

    def test_no_rest_violation(self):
        assert check_rest_days(7, 7) == PENALTY_INSUFFICIENT_REST

    def test_more_than_seven(self):
        assert check_rest_days(7, 8) == PENALTY_INSUFFICIENT_REST


# ===================================================================
# Taper
# ===================================================================

class TestTaper:

    def test_not_in_taper_period(self):
        """Weeks far from race don't trigger taper check."""
        assert check_taper(5, 16, 30, 25) == 0

    def test_taper_mileage_decreasing_ok(self):
        assert check_taper(14, 16, 20, 25) == 0  # 2 weeks remaining

    def test_taper_mileage_increasing_violation(self):
        assert check_taper(14, 16, 30, 25) == PENALTY_TAPER_VIOLATION

    def test_taper_same_mileage_ok(self):
        """Same mileage during taper is acceptable (not increasing)."""
        assert check_taper(14, 16, 25, 25) == 0

    def test_final_week_taper(self):
        """Last week (1 week remaining) should still check taper."""
        assert check_taper(15, 16, 20, 25) == 0  # Decreasing, ok
        assert check_taper(15, 16, 30, 25) == PENALTY_TAPER_VIOLATION  # Increasing, bad

    def test_week_4_remaining_no_taper(self):
        """4 weeks remaining is NOT in taper zone (only last 3)."""
        assert check_taper(12, 16, 30, 25) == 0

    def test_week_3_remaining_in_taper(self):
        """3 weeks remaining IS in taper zone."""
        assert check_taper(13, 16, 30, 25) == PENALTY_TAPER_VIOLATION


# ===================================================================
# Drop-back Week
# ===================================================================

class TestDropbackWeek:

    def test_too_early_no_check(self):
        assert check_dropback_week(2, [15, 16]) == 0

    def test_dropback_present(self):
        """Week 4 had lower mileage than the peak of the window."""
        history = [15, 16, 17, 14]  # 14 is below 85% of 17
        assert check_dropback_week(5, history) == 0

    def test_no_dropback_violation(self):
        """Steady increase with no drop in last 4 weeks."""
        # 85% of 18 = 15.3, so 15 IS below threshold, meaning dropback detected.
        # Use values where none are below 85% of the max.
        history = [16, 17, 17.5, 18]  # 85% of 18 = 15.3, all above
        assert check_dropback_week(5, history) == PENALTY_NO_DROPBACK

    def test_dropback_exactly_at_threshold(self):
        """A value exactly at 85% of peak should count as a dropback."""
        # 85% of 20 = 17.0
        history = [17.0, 18, 19, 20]
        assert check_dropback_week(5, history) == 0  # 17.0 <= 20*0.85

    def test_short_history(self):
        """Fewer than 4 weeks of history should skip check."""
        assert check_dropback_week(5, [15, 16, 17]) == 0

    def test_long_history_uses_last_four(self):
        """Only the last 4 weeks matter."""
        history = [10, 12, 14, 20, 21, 22, 23]  # Last 4: 20,21,22,23
        assert check_dropback_week(8, history) == PENALTY_NO_DROPBACK


# ===================================================================
# Composite: compute_week_penalty
# ===================================================================

class TestComputeWeekPenalty:

    def test_perfect_week_zero_penalty(self):
        """A well-constructed week should have zero penalty."""
        workouts = [
            {"type": "easy run", "distance": 4, "terrain": "road"},
            {"type": "easy run", "distance": 3, "terrain": "trail"},
            {"type": "easy run", "distance": 3, "terrain": "road"},
            {"type": "long run", "distance": 5, "terrain": "trail"},
        ]
        penalty, violations = compute_week_penalty(
            workouts=workouts,
            weekly_miles=15,
            previous_miles=14,
            week_number=2,
            total_weeks=16,
            days_per_week=4,
            available_terrain=["road", "trail"],
            weekly_miles_history=[14],
        )
        assert penalty == 0
        assert violations == []

    def test_multiple_violations_stack(self):
        """A bad week can accumulate penalties from multiple constraints."""
        workouts = [
            {"type": "tempo", "distance": 5, "terrain": "road"},
            {"type": "long run", "distance": 5, "terrain": "road"},
            {"type": "intervals", "distance": 5, "terrain": "road"},
            {"type": "tempo", "distance": 5, "terrain": "road"},
            {"type": "intervals", "distance": 5, "terrain": "road"},
            {"type": "long run", "distance": 5, "terrain": "road"},
            {"type": "tempo", "distance": 5, "terrain": "road"},
        ]
        penalty, violations = compute_week_penalty(
            workouts=workouts,
            weekly_miles=35,
            previous_miles=20,
            week_number=2,
            total_weeks=16,
            days_per_week=4,
            available_terrain=["road", "trail"],
            weekly_miles_history=[20],
        )
        assert penalty > 0
        assert len(violations) > 1

    def test_violations_list_is_descriptive(self):
        """Violation strings should describe the problem."""
        workouts = [
            {"type": "easy run", "distance": 10, "terrain": "road"},
        ]
        penalty, violations = compute_week_penalty(
            workouts=workouts,
            weekly_miles=30,
            previous_miles=20,
            week_number=2,
            total_weeks=16,
            days_per_week=4,
            available_terrain=["road", "trail"],
            weekly_miles_history=[20],
        )
        # Should include 10% rule violation and missing long run
        violation_text = " ".join(violations).lower()
        assert "10%" in violation_text or "long run" in violation_text

    def test_taper_week_penalty(self):
        """Increasing mileage during taper should add penalty."""
        workouts = [
            {"type": "easy run", "distance": 8, "terrain": "road"},
            {"type": "easy run", "distance": 7, "terrain": "trail"},
            {"type": "long run", "distance": 10, "terrain": "road"},
        ]
        penalty, violations = compute_week_penalty(
            workouts=workouts,
            weekly_miles=25,
            previous_miles=20,
            week_number=14,
            total_weeks=16,
            days_per_week=3,
            available_terrain=["road", "trail"],
            weekly_miles_history=[15, 16, 17, 18, 19, 20, 21, 20, 21, 22, 23, 24, 20],
        )
        assert any("taper" in v.lower() for v in violations)

    def test_return_types(self):
        workouts = [
            {"type": "easy run", "distance": 4, "terrain": "road"},
            {"type": "long run", "distance": 6, "terrain": "trail"},
        ]
        penalty, violations = compute_week_penalty(
            workouts=workouts, weekly_miles=10, previous_miles=9,
            week_number=1, total_weeks=16, days_per_week=3,
            available_terrain=["road", "trail"], weekly_miles_history=[],
        )
        assert isinstance(penalty, int)
        assert isinstance(violations, list)
        for v in violations:
            assert isinstance(v, str)
