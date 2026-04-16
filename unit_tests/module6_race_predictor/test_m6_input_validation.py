"""Tests for runner snapshot validation (happy paths + error conditions)."""

import pytest

from src.module6_race_predictor.constants import HALF_MARATHON_KM, MARATHON_KM
from src.module6_race_predictor.input_validation import ValidationError, validate_runner_snapshot


def _valid_goal(**overrides):
    base = {
        "age": 30,
        "goal_race": {
            "distance": "marathon",
            "target_time": "4:00:00",
            "terrain": "road",
        },
    }
    base.update(overrides)
    if "goal_race" in overrides and isinstance(overrides["goal_race"], dict):
        g = {
            "distance": "marathon",
            "target_time": "4:00:00",
            "terrain": "road",
        }
        g.update(overrides["goal_race"])
        base["goal_race"] = g
    return base


def test_minimal_valid_snapshot():
    out = validate_runner_snapshot(
        {
            "age": 30,
            "goal_race": {
                "distance": "marathon",
                "target_time": "4:00:00",
                "terrain": "road",
            },
        }
    )
    assert out["age"] == 30.0
    assert out["goal_time_minutes"] == 240.0


def test_missing_age_raises():
    with pytest.raises(ValidationError, match="age"):
        validate_runner_snapshot({"goal_race": {"distance": "marathon"}})


def test_unknown_goal_distance_raises():
    with pytest.raises(ValidationError, match="Unknown goal distance"):
        validate_runner_snapshot(
            {
                "age": 30,
                "goal_race": {"distance": "ultra 100mi", "target_time": "4:00:00"},
            }
        )


def test_input_must_be_dict():
    with pytest.raises(ValidationError, match="Input must be a dict"):
        validate_runner_snapshot("not a dict")  # type: ignore[arg-type]


def test_history_must_be_list():
    with pytest.raises(ValidationError, match="history must be a list"):
        validate_runner_snapshot(_valid_goal(history="bad"))  # type: ignore[dict-item]


def test_history_row_must_be_dict():
    with pytest.raises(ValidationError, match="history\\[0\\] must be a dict"):
        validate_runner_snapshot(_valid_goal(history=[1, 2]))


def test_age_lower_boundary_valid():
    out = validate_runner_snapshot(_valid_goal(age=16))
    assert out["age"] == 16.0


def test_age_upper_boundary_valid():
    out = validate_runner_snapshot(_valid_goal(age=80))
    assert out["age"] == 80.0


def test_age_too_young_raises():
    with pytest.raises(ValidationError, match="between 16 and 80"):
        validate_runner_snapshot(_valid_goal(age=15))


def test_age_too_old_raises():
    with pytest.raises(ValidationError, match="between 16 and 80"):
        validate_runner_snapshot(_valid_goal(age=81))


def test_invalid_experience_level_raises():
    with pytest.raises(ValidationError, match="experience_level must be one of"):
        validate_runner_snapshot(_valid_goal(experience_level="elite"))


def test_goal_race_must_be_dict():
    with pytest.raises(ValidationError, match="goal_race must be a dict"):
        validate_runner_snapshot(_valid_goal(goal_race="marathon"))  # type: ignore[dict-item]


def test_invalid_target_time_raises():
    with pytest.raises(ValidationError, match="target_time"):
        validate_runner_snapshot(
            _valid_goal(goal_race={"distance": "marathon", "target_time": "not-a-time"})
        )


def test_target_time_two_part_parses():
    out = validate_runner_snapshot(
        _valid_goal(goal_race={"distance": "marathon", "target_time": "4:30"})
    )
    assert out["goal_time_minutes"] == 270.0


def test_default_goal_minutes_when_target_time_missing():
    # Omit target_time entirely (partial-merge helpers would still inject 4:00).
    out = validate_runner_snapshot(
        {"age": 30, "goal_race": {"distance": "marathon"}},
    )
    assert out["goal_time_minutes"] == 270.0


def test_half_marathon_distance():
    out = validate_runner_snapshot(
        _valid_goal(goal_race={"distance": "half marathon", "target_time": "2:00:00"})
    )
    assert out["goal_distance_km"] == HALF_MARATHON_KM


def test_marathon_42k_alias():
    out = validate_runner_snapshot(
        _valid_goal(goal_race={"distance": "42k", "target_time": "4:00:00"})
    )
    assert out["goal_distance_km"] == MARATHON_KM


def test_numeric_goal_distance_km():
    out = validate_runner_snapshot(
        _valid_goal(goal_race={"distance": 10.0, "target_time": "1:00:00"})
    )
    assert out["goal_distance_km"] == 10.0


def test_goal_distance_km_string_pattern():
    out = validate_runner_snapshot(
        _valid_goal(goal_race={"distance": "21.1 km", "target_time": "2:00:00"})
    )
    assert abs(out["goal_distance_km"] - 21.1) < 0.001


def test_days_to_race_boundaries():
    assert validate_runner_snapshot(_valid_goal(days_to_race=1))["days_to_race"] == 1.0
    assert validate_runner_snapshot(_valid_goal(days_to_race=400))["days_to_race"] == 400.0


def test_days_to_race_out_of_range_raises():
    with pytest.raises(ValidationError, match="days_to_race must be between"):
        validate_runner_snapshot(_valid_goal(days_to_race=0))
    with pytest.raises(ValidationError, match="days_to_race must be between"):
        validate_runner_snapshot(_valid_goal(days_to_race=401))


def test_days_to_race_not_numeric_raises():
    with pytest.raises(ValidationError, match="days_to_race must be a number"):
        validate_runner_snapshot(_valid_goal(days_to_race="soon"))


def test_adherence_not_numeric_raises():
    with pytest.raises(ValidationError, match="adherence_percent must be a number"):
        validate_runner_snapshot(_valid_goal(adherence_percent="high"))


def test_adherence_clamped_to_0_100():
    assert validate_runner_snapshot(_valid_goal(adherence_percent=150))["adherence_percent"] == 100.0
    assert validate_runner_snapshot(_valid_goal(adherence_percent=-5))["adherence_percent"] == 0.0


def test_history_defaults_to_empty_list():
    out = validate_runner_snapshot(_valid_goal())
    assert out["history"] == []
