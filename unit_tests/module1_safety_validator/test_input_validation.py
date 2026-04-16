"""
Unit tests for input_validation.py - Input validation for runner profiles.

Tests validation of input data to prevent garbage in/garbage out scenarios.
"""

import pytest
from src.module1_safety_validator.input_validation import (
    validate_runner_profile,
    validate_workout_structure,
    validate_workout_data,
    validate_injury_data,
    get_validation_summary
)


class TestValidateRunnerProfile:
    """Test runner profile validation."""
    
    def test_valid_profile_returns_none(self):
        """Test that valid profile returns no error."""
        profile = {
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "days_trained_this_week": 3,
            "rest_days_this_week": 2,
            "available_terrain": ["road", "track"]
        }
        error = validate_runner_profile(profile)
        assert error is None
    
    def test_negative_weekly_mileage(self):
        """Test that negative weekly mileage is caught."""
        profile = {"weekly_mileage": -10}
        error = validate_runner_profile(profile)
        assert error is not None
        assert "negative" in error.lower()
    
    def test_excessive_weekly_mileage(self):
        """Test that unrealistic weekly mileage is caught."""
        profile = {"weekly_mileage": 2000, "experience_level": "beginner"}
        error = validate_runner_profile(profile)
        assert error is not None
        assert "250" in error or "200" in error
    
    def test_experience_level_mileage_mismatch(self):
        """Test that experience level inconsistent with mileage is caught."""
        profile = {"weekly_mileage": 100, "experience_level": "beginner"}
        error = validate_runner_profile(profile)
        assert error is not None
        assert "beginner" in error.lower()
    
    def test_negative_days_trained(self):
        """Test that negative days trained is caught."""
        profile = {"days_trained_this_week": -1}
        error = validate_runner_profile(profile)
        assert error is not None
        assert "negative" in error.lower()
    
    def test_excessive_days_trained(self):
        """Test that more than 7 days trained is caught."""
        profile = {"days_trained_this_week": 10}
        error = validate_runner_profile(profile)
        assert error is not None
        assert "7" in error
    
    def test_negative_rest_days(self):
        """Test that negative rest days is caught."""
        profile = {"rest_days_this_week": -2}
        error = validate_runner_profile(profile)
        assert error is not None
    
    def test_days_plus_rest_exceeds_week(self):
        """Test that days trained + rest days > 7 is caught."""
        profile = {
            "days_trained_this_week": 5,
            "rest_days_this_week": 4
        }
        error = validate_runner_profile(profile)
        assert error is not None
        assert "7" in error
    
    def test_injuries_without_terrain_options(self):
        """Test that injuries without available_terrain is caught."""
        profile = {
            "injuries": ["shin splints"],
            "weekly_mileage": 20
        }
        error = validate_runner_profile(profile)
        assert error is not None
        assert "available_terrain" in error
    
    def test_invalid_terrain_options(self):
        """Test that invalid terrain options are caught."""
        profile = {
            "available_terrain": ["road", "invalid_terrain", "track"]
        }
        error = validate_runner_profile(profile)
        assert error is not None
        assert "invalid_terrain" in error


class TestValidateWorkoutStructure:
    """Test workout structure validation."""
    
    def test_valid_workout_returns_empty(self):
        """Test that valid workout returns no errors."""
        workout = {"type": "easy run", "distance": 5, "terrain": "road"}
        errors = validate_workout_structure(workout)
        assert len(errors) == 0
    
    def test_negative_distance(self):
        """Test that negative distance is caught."""
        workout = {"distance": -5}
        errors = validate_workout_structure(workout)
        assert len(errors) > 0
        assert any("negative" in e.lower() for e in errors)
    
    def test_excessive_distance(self):
        """Test that unrealistic distance is caught."""
        workout = {"distance": 100}
        errors = validate_workout_structure(workout)
        assert len(errors) > 0
        assert any("extremely high" in e.lower() or "26.2" in e for e in errors)
    
    def test_invalid_terrain(self):
        """Test that invalid terrain is caught."""
        workout = {"terrain": "invalid_terrain"}
        errors = validate_workout_structure(workout)
        assert len(errors) > 0
        assert any("invalid" in e.lower() for e in errors)
    
    def test_valid_terrains_accepted(self):
        """Test that all valid terrains are accepted."""
        valid_terrains = ["road", "track", "trail", "treadmill"]
        for terrain in valid_terrains:
            workout = {"distance": 5, "terrain": terrain}
            errors = validate_workout_structure(workout)
            assert len(errors) == 0


class TestValidateWorkoutData:
    """Test comprehensive workout validation."""
    
    def test_valid_workout_for_experience(self):
        """Test valid workout for experience level."""
        workout = {"type": "easy run", "distance": 5, "terrain": "road"}
        profile = {"experience_level": "beginner"}
        errors = validate_workout_data(workout, profile)
        assert len(errors) == 0
    
    def test_beginner_tempo_invalid(self):
        """Test that beginner doing tempo is caught."""
        workout = {"type": "tempo", "distance": 5, "terrain": "road"}
        profile = {"experience_level": "beginner"}
        errors = validate_workout_data(workout, profile)
        assert len(errors) > 0
        assert any("beginner" in e.lower() for e in errors)
    
    def test_intermediate_tempo_valid(self):
        """Test that intermediate can do tempo."""
        workout = {"type": "tempo", "distance": 5, "terrain": "road"}
        profile = {"experience_level": "intermediate"}
        errors = validate_workout_data(workout, profile)
        # Should only have errors from structure validation, not experience
        assert not any("beginner" in e.lower() for e in errors)


class TestValidateInjuryData:
    """Test injury data validation."""
    
    def test_known_injuries_no_warning(self):
        """Test that known injuries return no warning."""
        injuries = ["shin splints", "knee pain"]
        warning = validate_injury_data(injuries)
        assert warning is None
    
    def test_unrecognized_injury_returns_warning(self):
        """Test that unrecognized injury returns warning."""
        injuries = ["some weird injury xyz"]
        warning = validate_injury_data(injuries)
        assert warning is not None
        assert "weird injury xyz" in warning
    
    def test_empty_injuries_no_warning(self):
        """Test that empty injuries return no warning."""
        warning = validate_injury_data([])
        assert warning is None
    
    def test_partial_match_recognized(self):
        """Test that partial matches are recognized."""
        injuries = ["runner's knee pain"]
        warning = validate_injury_data(injuries)
        assert warning is None  # "knee" is recognized


class TestGetValidationSummary:
    """Test comprehensive validation summary."""
    
    def test_valid_profile_summary(self):
        """Test summary for valid profile."""
        profile = {
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "injuries": ["shin splints"],
            "available_terrain": ["road"]
        }
        summary = get_validation_summary(profile)
        assert summary["valid"] is True
        assert len(summary["errors"]) == 0
    
    def test_invalid_profile_summary(self):
        """Test summary for invalid profile."""
        profile = {"weekly_mileage": -10}
        summary = get_validation_summary(profile)
        assert summary["valid"] is False
        assert len(summary["errors"]) > 0
    
    def test_warnings_in_summary(self):
        """Test that warnings appear in summary."""
        profile = {
            "weekly_mileage": 20,
            "injuries": ["unknown injury xyz"]
        }
        summary = get_validation_summary(profile)
        assert len(summary["warnings"]) > 0