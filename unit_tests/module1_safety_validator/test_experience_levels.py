"""
Unit tests for experience_levels.py - Runner experience level definitions.

Tests experience level criteria, validation, and helper functions.
"""

import pytest
from src.module1_safety_validator.experience_levels import (
    ExperienceLevelCriteria,
    BEGINNER,
    INTERMEDIATE,
    ADVANCED,
    EXPERIENCE_LEVELS,
    get_experience_criteria,
    validate_experience_level_consistency,
    get_appropriate_level,
    validate_workout_for_experience
)


class TestExperienceLevelCriteria:
    """Test ExperienceLevelCriteria dataclass."""
    
    def test_beginner_criteria_exists(self):
        """Test that BEGINNER criteria is defined."""
        assert BEGINNER.name == "beginner"
        assert BEGINNER.min_weekly_mileage == 0
        assert BEGINNER.max_weekly_mileage == 30
        assert BEGINNER.max_long_run == 13
        assert BEGINNER.can_do_high_intensity is False
    
    def test_intermediate_criteria_exists(self):
        """Test that INTERMEDIATE criteria is defined."""
        assert INTERMEDIATE.name == "intermediate"
        assert INTERMEDIATE.min_weekly_mileage == 20
        assert INTERMEDIATE.max_weekly_mileage == 50
        assert INTERMEDIATE.max_long_run == 18
        assert INTERMEDIATE.can_do_high_intensity is True
    
    def test_advanced_criteria_exists(self):
        """Test that ADVANCED criteria is defined."""
        assert ADVANCED.name == "advanced"
        assert ADVANCED.min_weekly_mileage == 40
        assert ADVANCED.max_weekly_mileage == 200
        assert ADVANCED.max_long_run == 26
        assert ADVANCED.can_do_high_intensity is True
    
    def test_all_criteria_have_descriptions(self):
        """Test that all levels have descriptions."""
        for level in [BEGINNER, INTERMEDIATE, ADVANCED]:
            assert len(level.description) > 0


class TestExperienceLevelsDict:
    """Test EXPERIENCE_LEVELS dictionary."""
    
    def test_experience_levels_has_all_levels(self):
        """Test that dictionary has all three levels."""
        assert len(EXPERIENCE_LEVELS) == 3
        assert "beginner" in EXPERIENCE_LEVELS
        assert "intermediate" in EXPERIENCE_LEVELS
        assert "advanced" in EXPERIENCE_LEVELS
    
    def test_experience_levels_values_correct(self):
        """Test that dictionary values are correct."""
        assert EXPERIENCE_LEVELS["beginner"] == BEGINNER
        assert EXPERIENCE_LEVELS["intermediate"] == INTERMEDIATE
        assert EXPERIENCE_LEVELS["advanced"] == ADVANCED


class TestGetExperienceCriteria:
    """Test get_experience_criteria function."""
    
    def test_get_beginner_criteria(self):
        """Test getting beginner criteria."""
        criteria = get_experience_criteria("beginner")
        assert criteria == BEGINNER
    
    def test_get_intermediate_criteria(self):
        """Test getting intermediate criteria."""
        criteria = get_experience_criteria("intermediate")
        assert criteria == INTERMEDIATE
    
    def test_get_advanced_criteria(self):
        """Test getting advanced criteria."""
        criteria = get_experience_criteria("advanced")
        assert criteria == ADVANCED
    
    def test_get_criteria_case_insensitive(self):
        """Test that function is case-insensitive."""
        criteria = get_experience_criteria("BEGINNER")
        assert criteria == BEGINNER
    
    def test_get_criteria_invalid_returns_none(self):
        """Test that invalid level returns None."""
        criteria = get_experience_criteria("invalid")
        assert criteria is None


class TestValidateExperienceLevelConsistency:
    """Test experience level consistency validation."""
    
    def test_beginner_20_miles_valid(self):
        """Test that beginner with 20 miles is valid."""
        is_valid, error = validate_experience_level_consistency("beginner", 20)
        assert is_valid is True
        assert error is None
    
    def test_beginner_50_miles_invalid(self):
        """Test that beginner with 50 miles is invalid."""
        is_valid, error = validate_experience_level_consistency("beginner", 50)
        assert is_valid is False
        assert error is not None
        assert "30" in error
    
    def test_intermediate_40_miles_valid(self):
        """Test that intermediate with 40 miles is valid."""
        is_valid, error = validate_experience_level_consistency("intermediate", 40)
        assert is_valid is True
    
    def test_intermediate_100_miles_invalid(self):
        """Test that intermediate with 100 miles is invalid."""
        is_valid, error = validate_experience_level_consistency("intermediate", 100)
        assert is_valid is False
        assert "50" in error
    
    def test_advanced_100_miles_valid(self):
        """Test that advanced with 100 miles is valid."""
        is_valid, error = validate_experience_level_consistency("advanced", 100)
        assert is_valid is True
    
    def test_advanced_10_miles_invalid(self):
        """Test that advanced with very low mileage is invalid."""
        is_valid, error = validate_experience_level_consistency("advanced", 10)
        assert is_valid is False
        assert "20" in error
    
    def test_invalid_level_name(self):
        """Test that invalid level name is caught."""
        is_valid, error = validate_experience_level_consistency("invalid", 20)
        assert is_valid is False
        assert "invalid" in error.lower()


class TestGetAppropriateLevel:
    """Test get_appropriate_level function."""
    
    def test_low_mileage_suggests_beginner(self):
        """Test that low mileage suggests beginner."""
        level = get_appropriate_level(15)
        assert level == "beginner"
    
    def test_medium_mileage_suggests_intermediate(self):
        """Test that medium mileage suggests intermediate."""
        level = get_appropriate_level(40)
        assert level == "intermediate"
    
    def test_high_mileage_suggests_advanced(self):
        """Test that high mileage suggests advanced."""
        level = get_appropriate_level(100)
        assert level == "advanced"
    
    def test_boundary_beginner_intermediate(self):
        """Test boundary between beginner and intermediate."""
        assert get_appropriate_level(30) == "beginner"
        assert get_appropriate_level(31) == "intermediate"
    
    def test_boundary_intermediate_advanced(self):
        """Test boundary between intermediate and advanced."""
        assert get_appropriate_level(50) == "intermediate"
        assert get_appropriate_level(51) == "advanced"


class TestValidateWorkoutForExperience:
    """Test workout appropriateness for experience level."""
    
    def test_beginner_easy_run_valid(self):
        """Test that beginner can do easy run."""
        is_valid, error = validate_workout_for_experience("beginner", "easy run")
        assert is_valid is True
        assert error is None
    
    def test_beginner_tempo_invalid(self):
        """Test that beginner cannot do tempo."""
        is_valid, error = validate_workout_for_experience("beginner", "tempo")
        assert is_valid is False
        assert error is not None
        assert "beginner" in error.lower()
    
    def test_beginner_intervals_invalid(self):
        """Test that beginner cannot do intervals."""
        is_valid, error = validate_workout_for_experience("beginner", "intervals")
        assert is_valid is False
        assert "beginner" in error.lower()
    
    def test_intermediate_tempo_valid(self):
        """Test that intermediate can do tempo."""
        is_valid, error = validate_workout_for_experience("intermediate", "tempo")
        assert is_valid is True
    
    def test_intermediate_intervals_valid(self):
        """Test that intermediate can do intervals."""
        is_valid, error = validate_workout_for_experience("intermediate", "intervals")
        assert is_valid is True
    
    def test_advanced_all_workouts_valid(self):
        """Test that advanced can do all workouts."""
        workouts = ["easy run", "tempo", "intervals", "hill repeats", "fartlek"]
        for workout in workouts:
            is_valid, error = validate_workout_for_experience("advanced", workout)
            assert is_valid is True
    
    def test_invalid_experience_level_returns_true(self):
        """Test that unknown level returns True (no validation)."""
        is_valid, error = validate_workout_for_experience("invalid", "tempo")
        assert is_valid is True
        assert error is None