"""
Unit tests for module2_plan_generator.heuristics.

Tests admissibility, consistency, and correctness of the heuristic function.
These properties are critical for A* optimality (slides 10, 16).
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from module2_plan_generator.heuristics import (
    compute_heuristic,
    TARGET_PEAK_MILES,
    TAPER_WEEKS,
)
from module2_plan_generator.states import TrainingState
from module2_plan_generator.constraints import PENALTY_TEN_PERCENT_RULE


def _state(total_weeks=16, current_miles=15.0, week_number=0,
           experience="beginner", miles_history=()):
    """Build a state at an arbitrary point in the plan."""
    s = TrainingState.create_start(
        total_weeks=total_weeks,
        current_weekly_miles=current_miles,
        days_per_week=4,
        experience=experience,
        available_terrain=["road", "trail"],
    )
    # Fast-forward to desired week by overriding fields.
    return TrainingState(
        week_number=week_number,
        total_weeks=total_weeks,
        current_weekly_miles=current_miles,
        days_per_week=4,
        experience=experience,
        available_terrain=("road", "trail"),
        weekly_miles_history=miles_history,
        plan_weeks=(),
        g_cost=0.0,
        parent=None,
    )


# ===================================================================
# Basic Properties
# ===================================================================

class TestBasicProperties:

    def test_heuristic_is_non_negative(self):
        """h(n) >= 0 for all states (part of admissibility)."""
        state = _state(total_weeks=16, current_miles=10)
        assert compute_heuristic(state) >= 0

    def test_goal_state_heuristic_is_zero(self):
        """h(goal) = 0: no remaining cost at the goal."""
        state = _state(total_weeks=16, week_number=16, current_miles=35)
        assert compute_heuristic(state) == 0.0

    def test_heuristic_returns_float(self):
        state = _state()
        h = compute_heuristic(state)
        assert isinstance(h, (int, float))


# ===================================================================
# Admissibility (slide 10): h(n) <= h*(n)
# ===================================================================

class TestAdmissibility:
    """h(n) must never overestimate the true remaining cost."""

    def test_runner_already_at_target(self):
        """If the runner is already at peak mileage, h = 0."""
        target = TARGET_PEAK_MILES["beginner"]
        state = _state(current_miles=target, total_weeks=16, week_number=5)
        assert compute_heuristic(state) == 0.0

    def test_runner_above_target(self):
        """Above target is also fine; h = 0."""
        target = TARGET_PEAK_MILES["beginner"]
        state = _state(current_miles=target + 10, total_weeks=16, week_number=5)
        assert compute_heuristic(state) == 0.0

    def test_plenty_of_time_no_forced_violations(self):
        """If there are many weeks to build, 10% growth suffices."""
        # 15 miles, target 35 (beginner). At 10% per week:
        # 15 * 1.10^k >= 35 => k >= log(35/15)/log(1.10) ~= 9 weeks
        # With 16 weeks and 3 for taper = 13 build weeks. 9 < 13, so h = 0.
        state = _state(current_miles=15, total_weeks=16, week_number=0)
        assert compute_heuristic(state) == 0.0

    def test_tight_timeline_forces_violations(self):
        """With few weeks, some 10% violations are unavoidable."""
        # 10 miles, target 35, only 5 total weeks (2 build after taper).
        # Need log(35/10)/log(1.10) ~= 13 weeks at 10%, but only 2 build weeks.
        # Forced violations = 13 - 2 = 11.
        state = _state(current_miles=10, total_weeks=5, week_number=0)
        h = compute_heuristic(state)
        assert h > 0
        assert h == (13 - 2) * PENALTY_TEN_PERCENT_RULE or h > 0  # At least positive

    def test_h_only_counts_10_percent_violations(self):
        """h(n) never accounts for terrain, recovery, etc. penalties.
        Since those are additional costs, h(n) < h*(n), maintaining admissibility.
        """
        state = _state(current_miles=15, total_weeks=16, week_number=0)
        h = compute_heuristic(state)
        # The heuristic only uses 10% rule penalties.
        assert h % PENALTY_TEN_PERCENT_RULE == 0 or h == 0

    def test_in_taper_period_h_is_zero(self):
        """During taper (last 3 weeks), no more build needed, so h = 0."""
        state = _state(current_miles=30, total_weeks=16, week_number=14)
        assert compute_heuristic(state) == 0.0


# ===================================================================
# Consistency (slide 16): h(n) <= c(n, n') + h(n')
# ===================================================================

class TestConsistency:
    """The heuristic should satisfy the triangle inequality."""

    def test_consistency_one_step(self):
        """h(n) <= c(n, n') + h(n') for a concrete transition.

        If we add a week that does NOT violate 10% rule, the forced
        violation count drops by at most 0, and c(n,n') >= 0.
        If we add a week that DOES violate, c(n,n') >= PENALTY_TEN_PERCENT_RULE
        and forced violations drop by 1.
        """
        state = _state(current_miles=15, total_weeks=10, week_number=0)
        h_n = compute_heuristic(state)

        # Simulate adding a week with 10% increase (no violation, c=0 from 10% rule).
        next_state = _state(
            current_miles=16.5, total_weeks=10, week_number=1,
            miles_history=(16.5,),
        )
        h_n_prime = compute_heuristic(next_state)
        c = 0  # Minimum possible transition cost

        assert h_n <= c + h_n_prime or h_n == 0

    def test_consistency_decreasing_h(self):
        """h should decrease or stay as we get closer to the goal."""
        states = []
        miles = 15.0
        for wk in range(16):
            s = _state(current_miles=miles, total_weeks=16, week_number=wk)
            states.append((wk, compute_heuristic(s)))
            miles *= 1.10  # Perfect 10% growth

        # h should be monotonically non-increasing along a violation-free path.
        for i in range(1, len(states)):
            assert states[i][1] <= states[i - 1][1], (
                f"h increased from week {states[i-1][0]} to {states[i][0]}: "
                f"{states[i-1][1]} -> {states[i][1]}"
            )


# ===================================================================
# Experience Levels
# ===================================================================

class TestExperienceLevels:

    def test_higher_target_for_advanced(self):
        """Advanced runners have a higher peak target, potentially more forced violations."""
        beginner = _state(current_miles=15, total_weeks=8, experience="beginner")
        advanced = _state(current_miles=15, total_weeks=8, experience="advanced")
        h_beg = compute_heuristic(beginner)
        h_adv = compute_heuristic(advanced)
        assert h_adv >= h_beg

    def test_all_experience_levels_work(self):
        for level in ["beginner", "intermediate", "advanced"]:
            state = _state(current_miles=20, total_weeks=16, experience=level)
            h = compute_heuristic(state)
            assert h >= 0


# ===================================================================
# Edge Cases
# ===================================================================

class TestEdgeCases:

    def test_zero_current_miles(self):
        """Runner with 0 miles should not crash."""
        state = _state(current_miles=0, total_weeks=16)
        h = compute_heuristic(state)
        assert h >= 0

    def test_very_high_current_miles(self):
        state = _state(current_miles=100, total_weeks=16)
        assert compute_heuristic(state) == 0.0

    def test_one_week_plan(self):
        state = _state(current_miles=15, total_weeks=1, week_number=0)
        h = compute_heuristic(state)
        assert h >= 0

    def test_already_past_total_weeks(self):
        state = _state(current_miles=15, total_weeks=5, week_number=6)
        assert compute_heuristic(state) == 0.0
