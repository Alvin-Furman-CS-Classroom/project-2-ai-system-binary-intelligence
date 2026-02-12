"""
Unit tests for module2_plan_generator.input_validation.

Tests every validation rule, valid inputs, boundary cases, and cross-field
consistency checks.
"""

import sys
import os
import pytest
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from module2_plan_generator.input_validation import (
    validate_planner_input,
    VALID_GOALS,
    VALID_EXPERIENCE_LEVELS,
    VALID_TERRAIN_TYPES,
    _parse_date,
)


# ---------------------------------------------------------------------------
# Helper: build a valid config (all tests can override specific fields)
# ---------------------------------------------------------------------------

def _valid_config(**overrides):
    """Return a valid planner config dict, with optional overrides."""
    future = date.today() + timedelta(weeks=16)
    cfg = {
        "goal": "complete marathon",
        "race_date": future.isoformat(),
        "days_per_week": 4,
        "current_weekly_miles": 15,
        "experience": "beginner",
        "available_terrain": ["road", "trail"],
    }
    cfg.update(overrides)
    return cfg


# ===================================================================
# Tests for fully valid input
# ===================================================================

class TestValidInput:
    """A valid config should produce zero errors."""

    def test_minimal_valid(self):
        errors = validate_planner_input(_valid_config())
        assert errors == []

    def test_all_experience_levels(self):
        for level in VALID_EXPERIENCE_LEVELS:
            miles = {"beginner": 15, "intermediate": 30, "advanced": 40}[level]
            errors = validate_planner_input(
                _valid_config(experience=level, current_weekly_miles=miles)
            )
            assert errors == [], f"Failed for {level}: {errors}"

    def test_all_terrain_types(self):
        for terrain in VALID_TERRAIN_TYPES:
            errors = validate_planner_input(
                _valid_config(available_terrain=[terrain])
            )
            assert errors == []

    def test_multiple_terrains(self):
        errors = validate_planner_input(
            _valid_config(available_terrain=["road", "trail", "track", "treadmill"])
        )
        assert errors == []

    def test_days_per_week_boundaries(self):
        for d in [3, 4, 5, 6]:
            errors = validate_planner_input(_valid_config(days_per_week=d))
            assert errors == [], f"Failed for {d} days: {errors}"

    def test_half_marathon_goal(self):
        errors = validate_planner_input(_valid_config(goal="complete half marathon"))
        assert errors == []

    def test_case_insensitive_goal(self):
        errors = validate_planner_input(_valid_config(goal="Complete Marathon"))
        assert errors == []

    def test_zero_miles(self):
        """A complete beginner with 0 miles should be accepted."""
        errors = validate_planner_input(_valid_config(current_weekly_miles=0))
        assert errors == []

    def test_race_date_as_date_object(self):
        future = date.today() + timedelta(weeks=16)
        errors = validate_planner_input(_valid_config(race_date=future))
        assert errors == []


# ===================================================================
# Tests for missing required fields
# ===================================================================

class TestMissingFields:
    """Each required field must be present."""

    @pytest.mark.parametrize("missing_key", [
        "goal", "race_date", "days_per_week",
        "current_weekly_miles", "experience", "available_terrain",
    ])
    def test_missing_field(self, missing_key):
        cfg = _valid_config()
        del cfg[missing_key]
        errors = validate_planner_input(cfg)
        assert any(missing_key in e for e in errors)

    def test_multiple_missing_fields(self):
        errors = validate_planner_input({})
        assert len(errors) >= 6  # All required fields missing

    def test_empty_dict(self):
        errors = validate_planner_input({})
        assert len(errors) > 0


# ===================================================================
# Tests for goal validation
# ===================================================================

class TestGoalValidation:

    def test_invalid_goal_string(self):
        errors = validate_planner_input(_valid_config(goal="win olympic gold"))
        assert any("goal" in e.lower() for e in errors)

    def test_empty_goal(self):
        errors = validate_planner_input(_valid_config(goal=""))
        assert any("goal" in e.lower() for e in errors)

    def test_goal_not_string(self):
        errors = validate_planner_input(_valid_config(goal=42))
        assert any("goal" in e.lower() for e in errors)


# ===================================================================
# Tests for race_date validation
# ===================================================================

class TestRaceDateValidation:

    def test_past_date(self):
        past = (date.today() - timedelta(days=30)).isoformat()
        errors = validate_planner_input(_valid_config(race_date=past))
        assert any("future" in e.lower() for e in errors)

    def test_today_date(self):
        errors = validate_planner_input(_valid_config(race_date=date.today().isoformat()))
        assert any("future" in e.lower() for e in errors)

    def test_too_close_race(self):
        close = (date.today() + timedelta(weeks=2)).isoformat()
        errors = validate_planner_input(_valid_config(race_date=close))
        assert any("week" in e.lower() for e in errors)

    def test_too_far_race(self):
        far = (date.today() + timedelta(weeks=35)).isoformat()
        errors = validate_planner_input(_valid_config(race_date=far))
        assert any("30 weeks" in e.lower() or "maximum" in e.lower() for e in errors)

    def test_invalid_date_format(self):
        errors = validate_planner_input(_valid_config(race_date="June 15 2026"))
        assert any("iso" in e.lower() or "format" in e.lower() for e in errors)

    def test_nonsense_date(self):
        errors = validate_planner_input(_valid_config(race_date="not-a-date"))
        assert len(errors) > 0

    def test_boundary_4_weeks(self):
        """Exactly 4 weeks out should be valid."""
        boundary = (date.today() + timedelta(weeks=4, days=1)).isoformat()
        errors = validate_planner_input(_valid_config(race_date=boundary))
        assert errors == []

    def test_boundary_30_weeks(self):
        """Exactly 30 weeks out should be valid."""
        boundary = (date.today() + timedelta(weeks=30)).isoformat()
        errors = validate_planner_input(_valid_config(race_date=boundary))
        assert errors == []


# ===================================================================
# Tests for days_per_week validation
# ===================================================================

class TestDaysPerWeekValidation:

    def test_too_few_days(self):
        errors = validate_planner_input(_valid_config(days_per_week=2))
        assert any("days_per_week" in e for e in errors)

    def test_too_many_days(self):
        errors = validate_planner_input(_valid_config(days_per_week=7))
        assert any("days_per_week" in e for e in errors)

    def test_float_days(self):
        errors = validate_planner_input(_valid_config(days_per_week=4.5))
        assert any("days_per_week" in e for e in errors)

    def test_zero_days(self):
        errors = validate_planner_input(_valid_config(days_per_week=0))
        assert any("days_per_week" in e for e in errors)

    def test_negative_days(self):
        errors = validate_planner_input(_valid_config(days_per_week=-1))
        assert any("days_per_week" in e for e in errors)

    def test_string_days(self):
        errors = validate_planner_input(_valid_config(days_per_week="four"))
        assert len(errors) > 0


# ===================================================================
# Tests for current_weekly_miles validation
# ===================================================================

class TestWeeklyMilesValidation:

    def test_negative_miles(self):
        errors = validate_planner_input(_valid_config(current_weekly_miles=-5))
        assert any("miles" in e.lower() for e in errors)

    def test_too_high_miles(self):
        errors = validate_planner_input(_valid_config(current_weekly_miles=150))
        assert any("100" in e or "high" in e.lower() for e in errors)

    def test_string_miles(self):
        errors = validate_planner_input(_valid_config(current_weekly_miles="twenty"))
        assert len(errors) > 0

    def test_float_miles_ok(self):
        errors = validate_planner_input(_valid_config(current_weekly_miles=15.5))
        assert errors == []

    def test_boundary_100_miles(self):
        errors = validate_planner_input(
            _valid_config(current_weekly_miles=100, experience="advanced")
        )
        assert errors == []


# ===================================================================
# Tests for experience validation
# ===================================================================

class TestExperienceValidation:

    def test_invalid_experience(self):
        errors = validate_planner_input(_valid_config(experience="elite"))
        assert any("experience" in e.lower() for e in errors)

    def test_empty_experience(self):
        errors = validate_planner_input(_valid_config(experience=""))
        assert any("experience" in e.lower() for e in errors)

    def test_numeric_experience(self):
        errors = validate_planner_input(_valid_config(experience=3))
        assert len(errors) > 0


# ===================================================================
# Tests for available_terrain validation
# ===================================================================

class TestTerrainValidation:

    def test_empty_list(self):
        errors = validate_planner_input(_valid_config(available_terrain=[]))
        assert any("terrain" in e.lower() for e in errors)

    def test_invalid_terrain_type(self):
        errors = validate_planner_input(_valid_config(available_terrain=["moon"]))
        assert any("terrain" in e.lower() for e in errors)

    def test_mixed_valid_invalid(self):
        errors = validate_planner_input(
            _valid_config(available_terrain=["road", "swamp"])
        )
        assert any("swamp" in e for e in errors)

    def test_not_a_list(self):
        errors = validate_planner_input(_valid_config(available_terrain="road"))
        assert any("terrain" in e.lower() for e in errors)


# ===================================================================
# Tests for cross-field consistency
# ===================================================================

class TestCrossFieldValidation:

    def test_beginner_too_many_miles(self):
        errors = validate_planner_input(
            _valid_config(experience="beginner", current_weekly_miles=40)
        )
        assert any("beginner" in e.lower() for e in errors)

    def test_advanced_too_few_miles(self):
        errors = validate_planner_input(
            _valid_config(experience="advanced", current_weekly_miles=10)
        )
        assert any("advanced" in e.lower() for e in errors)

    def test_intermediate_any_miles(self):
        """Intermediate has no special mileage constraints."""
        errors = validate_planner_input(
            _valid_config(experience="intermediate", current_weekly_miles=25)
        )
        assert errors == []


# ===================================================================
# Tests for _parse_date helper
# ===================================================================

class TestParseDate:

    def test_valid_iso_string(self):
        assert _parse_date("2026-06-15") == date(2026, 6, 15)

    def test_date_object(self):
        d = date(2026, 6, 15)
        assert _parse_date(d) == d

    def test_invalid_string(self):
        assert _parse_date("not-a-date") is None

    def test_none_input(self):
        assert _parse_date(None) is None

    def test_integer_input(self):
        assert _parse_date(12345) is None

    def test_empty_string(self):
        assert _parse_date("") is None
