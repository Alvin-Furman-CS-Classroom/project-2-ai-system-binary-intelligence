"""
Unit tests for module2_plan_generator.states.

Tests state creation, goal testing, successor generation, path recovery,
and hashing/equality for use in OPEN/CLOSED sets.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from module2_plan_generator.states import TrainingState


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _start_state(**overrides):
    defaults = dict(
        total_weeks=16,
        current_weekly_miles=15.0,
        days_per_week=4,
        experience="beginner",
        available_terrain=["road", "trail"],
    )
    defaults.update(overrides)
    return TrainingState.create_start(**defaults)


def _sample_workouts():
    return (
        {"day": "Tuesday", "type": "easy run", "distance": 4, "terrain": "road"},
        {"day": "Thursday", "type": "easy run", "distance": 3, "terrain": "trail"},
        {"day": "Saturday", "type": "long run", "distance": 8, "terrain": "road"},
    )


# ===================================================================
# State Creation
# ===================================================================

class TestCreateStart:

    def test_start_week_is_zero(self):
        state = _start_state()
        assert state.week_number == 0

    def test_start_has_no_plan(self):
        state = _start_state()
        assert state.plan_weeks == ()
        assert state.weekly_miles_history == ()

    def test_start_g_cost_is_zero(self):
        state = _start_state()
        assert state.g_cost == 0.0

    def test_start_has_no_parent(self):
        state = _start_state()
        assert state.parent is None

    def test_terrain_stored_as_tuple(self):
        state = _start_state(available_terrain=["road", "Trail", "TRACK"])
        assert state.available_terrain == ("road", "trail", "track")

    def test_experience_preserved(self):
        state = _start_state(experience="intermediate")
        assert state.experience == "intermediate"

    def test_total_weeks_preserved(self):
        state = _start_state(total_weeks=20)
        assert state.total_weeks == 20


# ===================================================================
# Goal Test
# ===================================================================

class TestGoalTest:

    def test_start_is_not_goal(self):
        state = _start_state(total_weeks=16)
        assert state.is_goal() is False

    def test_complete_plan_is_goal(self):
        """After adding total_weeks weeks, the state should be a goal."""
        state = _start_state(total_weeks=3)
        workouts = tuple([_sample_workouts()])
        for i in range(3):
            state = state.add_week(workouts=_sample_workouts(), week_miles=15.0, week_penalty=0)
        assert state.is_goal() is True

    def test_partial_plan_is_not_goal(self):
        state = _start_state(total_weeks=3)
        state = state.add_week(workouts=_sample_workouts(), week_miles=15.0, week_penalty=0)
        assert state.is_goal() is False

    def test_one_week_plan(self):
        state = _start_state(total_weeks=1)
        assert state.is_goal() is False
        state = state.add_week(workouts=_sample_workouts(), week_miles=15.0, week_penalty=0)
        assert state.is_goal() is True


# ===================================================================
# Adding Weeks (Successor Generation)
# ===================================================================

class TestAddWeek:

    def test_week_number_increments(self):
        state = _start_state()
        next_state = state.add_week(_sample_workouts(), 16.0, 5)
        assert next_state.week_number == 1

    def test_mileage_updated(self):
        state = _start_state()
        next_state = state.add_week(_sample_workouts(), 16.0, 5)
        assert next_state.current_weekly_miles == 16.0

    def test_history_appended(self):
        state = _start_state()
        s1 = state.add_week(_sample_workouts(), 16.0, 0)
        s2 = s1.add_week(_sample_workouts(), 17.0, 0)
        assert s2.weekly_miles_history == (16.0, 17.0)

    def test_plan_weeks_appended(self):
        state = _start_state()
        w = _sample_workouts()
        s1 = state.add_week(w, 15.0, 0)
        assert len(s1.plan_weeks) == 1
        assert s1.plan_weeks[0] == w

    def test_g_cost_accumulates(self):
        state = _start_state()
        s1 = state.add_week(_sample_workouts(), 16.0, 5)
        s2 = s1.add_week(_sample_workouts(), 17.0, 10)
        assert s2.g_cost == 15.0

    def test_parent_pointer(self):
        state = _start_state()
        s1 = state.add_week(_sample_workouts(), 16.0, 0)
        assert s1.parent is state

    def test_original_state_unchanged(self):
        """States are immutable (frozen dataclass)."""
        state = _start_state()
        state.add_week(_sample_workouts(), 16.0, 5)
        assert state.week_number == 0
        assert state.g_cost == 0.0
        assert state.weekly_miles_history == ()

    def test_constant_fields_preserved(self):
        state = _start_state(experience="intermediate", days_per_week=5)
        next_state = state.add_week(_sample_workouts(), 16.0, 0)
        assert next_state.experience == "intermediate"
        assert next_state.days_per_week == 5
        assert next_state.total_weeks == state.total_weeks
        assert next_state.available_terrain == state.available_terrain


# ===================================================================
# Path Recovery
# ===================================================================

class TestRecoverPlan:

    def test_recover_three_week_plan(self):
        state = _start_state(total_weeks=3)
        s1 = state.add_week(_sample_workouts(), 15.0, 0)
        s2 = s1.add_week(_sample_workouts(), 16.0, 5)
        s3 = s2.add_week(_sample_workouts(), 17.0, 3)

        plan = s3.recover_plan()
        assert len(plan) == 3
        assert plan[0]["week"] == 1
        assert plan[1]["week"] == 2
        assert plan[2]["week"] == 3

    def test_plan_contains_mileage(self):
        state = _start_state(total_weeks=2)
        s1 = state.add_week(_sample_workouts(), 15.0, 0)
        s2 = s1.add_week(_sample_workouts(), 16.5, 0)
        plan = s2.recover_plan()
        assert plan[0]["total_miles"] == 15.0
        assert plan[1]["total_miles"] == 16.5

    def test_plan_contains_workouts(self):
        state = _start_state(total_weeks=1)
        w = _sample_workouts()
        s1 = state.add_week(w, 15.0, 0)
        plan = s1.recover_plan()
        assert len(plan[0]["workouts"]) == len(w)

    def test_start_state_empty_plan(self):
        state = _start_state()
        plan = state.recover_plan()
        assert plan == []


# ===================================================================
# Hashing and Equality (needed for OPEN/CLOSED sets)
# ===================================================================

class TestHashingEquality:

    def test_same_state_equal(self):
        s1 = _start_state()
        s2 = _start_state()
        assert s1 == s2

    def test_same_hash(self):
        s1 = _start_state()
        s2 = _start_state()
        assert hash(s1) == hash(s2)

    def test_different_weeks_not_equal(self):
        s1 = _start_state()
        s2 = s1.add_week(_sample_workouts(), 16.0, 0)
        assert s1 != s2

    def test_can_be_in_set(self):
        s1 = _start_state()
        s2 = s1.add_week(_sample_workouts(), 16.0, 0)
        states = {s1, s2}
        assert len(states) == 2
        assert s1 in states
        assert s2 in states

    def test_can_be_dict_key(self):
        s1 = _start_state()
        d = {s1: 42}
        assert d[s1] == 42

    def test_states_with_different_mileage_history_not_equal(self):
        state = _start_state()
        s1 = state.add_week(_sample_workouts(), 15.0, 0)
        s2 = state.add_week(_sample_workouts(), 16.0, 0)
        assert s1 != s2

    def test_frozen_immutable(self):
        state = _start_state()
        with pytest.raises(AttributeError):
            state.week_number = 5
