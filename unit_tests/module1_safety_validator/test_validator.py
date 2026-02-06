"""
Unit tests for validator.py - Main workout safety validation interface.

Tests the complete validation workflow including fact extraction, inference,
and alternative generation working together.
"""

import pytest
from datetime import datetime, timedelta
from src.module1_safety_validator.validator import (
    validate_workout,
    validate_workout_detailed,
    quick_validate,
    batch_validate
)


class TestValidateWorkoutBasic:
    """Test basic validate_workout functionality."""
    
    def test_validate_workout_returns_dict(self):
        """Test that validate_workout returns a dictionary."""
        profile = {
            "injuries": [],
            "symptoms": [],
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["road"]
        }
        workout = {"type": "easy run", "distance": 5, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        assert isinstance(result, dict)
        assert "safe" in result
        assert "reason" in result
        assert "alternative" in result
    
    def test_validate_workout_with_embedded_workout(self):
        """Test validate_workout with workout embedded in profile."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "proposed_workout": {
                "type": "easy run",
                "distance": 5,
                "terrain": "road"
            }
        }
        
        result = validate_workout(profile)
        
        assert isinstance(result, dict)
        assert "safe" in result
    
    def test_validate_workout_no_workout_returns_error(self):
        """Test that missing workout returns error."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20
        }
        
        result = validate_workout(profile)
        
        assert result["safe"] is False
        assert "No proposed workout" in result["reason"]
        assert result["alternative"] is None


class TestSafeWorkouts:
    """Test validation of safe workouts."""
    
    def test_safe_easy_run(self):
        """Test that safe easy run passes validation."""
        profile = {
            "symptoms": [],
            "injuries": [],
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["road"]
        }
        workout = {"type": "easy run", "distance": 5, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is True
        assert result["alternative"] is None
        assert "safe" in result["reason"].lower()
    
    def test_safe_long_run_within_limits(self):
        """Test that long run within safe limits passes."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["road"]
        }
        workout = {"type": "long run", "distance": 15, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is True


class TestUnsafeWorkoutsCritical:
    """Test validation of critical safety violations."""
    
    def test_chest_pain_blocks_workout(self):
        """Test that chest pain blocks all workouts."""
        profile = {
            "symptoms": ["chest_pain"],
            "injuries": [],
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "available_terrain": ["road"]
        }
        workout = {"type": "easy run", "distance": 3, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert "chest pain" in result["reason"].lower()
        assert result["alternative"] is None
        assert result["recommendation"] == "rest"
    
    def test_dizziness_blocks_workout(self):
        """Test that dizziness blocks all workouts."""
        profile = {
            "symptoms": ["dizziness"],
            "injuries": [],
            "weekly_mileage": 20,
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "available_terrain": ["road"]
        }
        workout = {"type": "easy run", "distance": 3, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert "dizziness" in result["reason"].lower()
        assert result["alternative"] is None
    
    def test_severe_pain_blocks_workout(self):
        """Test that severe pain blocks workouts."""
        profile = {
            "pain_level": "severe",
            "injuries": [],
            "weekly_mileage": 20,
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "available_terrain": ["road"]
        }
        workout = {"type": "easy run", "distance": 3, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert result["alternative"] is None
    
    def test_uncleared_injury_blocks_workout(self):
        """Test that uncleared injury blocks workouts."""
        profile = {
            "injuries": ["shin splints"],
            "cleared_by_doctor": False,
            "weekly_mileage": 20,
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "available_terrain": ["treadmill"]
        }
        workout = {"type": "easy run", "distance": 3, "terrain": "treadmill"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert result["alternative"] is None


class TestUnsafeWorkoutsWithAlternatives:
    """Test validation of unsafe workouts that can have alternatives."""
    
    def test_shin_splints_track_suggests_treadmill(self):
        """Test shin splints + track suggests treadmill alternative."""
        profile = {
            "injuries": ["shin splints"],
            "cleared_by_doctor": True,
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["track", "treadmill"]
        }
        workout = {"type": "long run", "distance": 10, "terrain": "track"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert "shin splints" in result["reason"].lower()
        assert result["alternative"] is not None
        assert result["alternative"]["terrain"] == "treadmill"
        assert result["alternative"]["type"] == "long run"
        assert result["alternative"]["distance"] == 10
    
    def test_excessive_distance_reduces_distance(self):
        """Test excessive distance suggests reduced distance."""
        profile = {
            "injuries": [],
            "weekly_mileage": 10,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["road"]
        }
        workout = {"type": "long run", "distance": 20, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert "distance" in result["reason"].lower()
        assert result["alternative"] is not None
        assert result["alternative"]["distance"] == 15.0  # 1.5 × 10
    
    def test_beginner_high_intensity_suggests_easy_run(self):
        """Test beginner + high intensity suggests easy run."""
        profile = {
            "injuries": [],
            "weekly_mileage": 15,
            "experience_level": "beginner",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["road"]
        }
        workout = {"type": "tempo", "distance": 5, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert "beginner" in result["reason"].lower()
        assert result["alternative"] is not None
        assert result["alternative"]["type"] == "easy run"
    
    def test_multiple_issues_multiple_fixes(self):
        """Test multiple safety issues get multiple fixes."""
        profile = {
            "injuries": ["shin splints"],
            "cleared_by_doctor": True,
            "weekly_mileage": 10,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["track", "treadmill"]
        }
        workout = {"type": "long run", "distance": 20, "terrain": "track"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert result["alternative"] is not None
        assert result["alternative"]["terrain"] == "treadmill"
        assert result["alternative"]["distance"] == 15.0


class TestEnvironmentSafety:
    """Test environment-related safety checks."""
    
    def test_extreme_heat_blocks_workout(self):
        """Test extreme heat blocks workout."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20,
            "hydrated": True,
            "proper_footwear": True,
            "weather": "extreme_heat",
            "available_terrain": ["road"]
        }
        workout = {"type": "easy run", "distance": 5, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert "extreme" in result["reason"].lower() or "heat" in result["reason"].lower()
    
    def test_not_hydrated_blocks_workout(self):
        """Test dehydration blocks workout."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20,
            "hydrated": False,
            "proper_footwear": True,
            "weather": "normal",
            "available_terrain": ["road"]
        }
        workout = {"type": "easy run", "distance": 5, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert "hydrat" in result["reason"].lower()
    
    def test_no_proper_footwear_blocks_workout(self):
        """Test improper footwear blocks workout."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20,
            "hydrated": True,
            "proper_footwear": False,
            "weather": "normal",
            "available_terrain": ["road"]
        }
        workout = {"type": "easy run", "distance": 5, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert "footwear" in result["reason"].lower()


class TestDetailedValidation:
    """Test validate_workout_detailed with debug info."""
    
    def test_detailed_validation_includes_debug_info(self):
        """Test that detailed validation includes debug information."""
        profile = {
            "injuries": ["shin splints"],
            "cleared_by_doctor": True,
            "weekly_mileage": 20,
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "available_terrain": ["track", "treadmill"]
        }
        workout = {"type": "long run", "distance": 10, "terrain": "track"}
        
        result = validate_workout_detailed(profile, workout, debug=True)
        
        assert "_debug_info" in result
        assert "initial_facts" in result["_debug_info"]
        assert "derived_facts" in result["_debug_info"]
        assert "fired_rules" in result["_debug_info"]
        assert "severity" in result["_debug_info"]
        assert "inference_chain" in result["_debug_info"]
    
    def test_detailed_validation_without_debug(self):
        """Test that detailed validation without debug flag doesn't include debug info."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20,
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "available_terrain": ["road"]
        }
        workout = {"type": "easy run", "distance": 5, "terrain": "road"}
        
        result = validate_workout_detailed(profile, workout, debug=False)
        
        assert "_debug_info" not in result
    
    def test_detailed_validation_shows_initial_facts(self):
        """Test that debug info includes initial facts."""
        profile = {
            "injuries": ["shin splints"],
            "cleared_by_doctor": True,
            "weekly_mileage": 20,
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "available_terrain": ["track"]
        }
        workout = {"type": "long run", "distance": 10, "terrain": "track"}
        
        result = validate_workout_detailed(profile, workout, debug=True)
        
        initial_facts = result["_debug_info"]["initial_facts"]
        assert "shin_splints" in initial_facts
        assert "track_terrain" in initial_facts


class TestQuickValidate:
    """Test quick_validate simplified interface."""
    
    def test_quick_validate_safe_returns_true(self):
        """Test quick validate returns True for safe workout."""
        result = quick_validate(
            injuries=[],
            workout_type="easy run",
            distance=5,
            terrain="road",
            weekly_mileage=20
        )
        
        assert result is True
    
    def test_quick_validate_unsafe_returns_false(self):
        """Test quick validate returns False for unsafe workout."""
        result = quick_validate(
            injuries=["shin splints"],
            workout_type="long run",
            distance=12,
            terrain="track",
            weekly_mileage=15
        )
        
        assert result is False
    
    def test_quick_validate_excessive_distance(self):
        """Test quick validate detects excessive distance."""
        result = quick_validate(
            injuries=[],
            workout_type="long run",
            distance=25,
            terrain="road",
            weekly_mileage=10
        )
        
        assert result is False


class TestBatchValidate:
    """Test batch_validate for multiple workouts."""
    
    def test_batch_validate_multiple_workouts(self):
        """Test batch validation of multiple workouts."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["road", "track"]
        }
        
        workouts = [
            {"type": "easy run", "distance": 5, "terrain": "road"},
            {"type": "long run", "distance": 15, "terrain": "road"},
            {"type": "tempo", "distance": 6, "terrain": "track"}
        ]
        
        results = batch_validate(profile, workouts)
        
        assert len(results) == 3
        assert all(isinstance(r, dict) for r in results)
        assert all("safe" in r for r in results)
    
    def test_batch_validate_mixed_results(self):
        """Test batch validation with safe and unsafe workouts."""
        profile = {
            "injuries": ["shin splints"],
            "cleared_by_doctor": True,
            "weekly_mileage": 10,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["road", "track", "treadmill"]
        }
        
        workouts = [
            {"type": "easy run", "distance": 3, "terrain": "treadmill"},  # Safe
            {"type": "long run", "distance": 20, "terrain": "track"}      # Unsafe (2 issues)
        ]
        
        results = batch_validate(profile, workouts)
        
        assert len(results) == 2
        assert results[0]["safe"] is True
        assert results[1]["safe"] is False


class TestRealWorldScenarios:
    """Test realistic complete scenarios."""
    
    def test_healthy_runner_weekly_plan(self):
        """Test validation of healthy runner's weekly plan."""
        profile = {
            "symptoms": [],
            "injuries": [],
            "weekly_mileage": 25,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 1,
            "days_trained_this_week": 4,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["road", "trail"]
        }
        
        workouts = [
            {"type": "easy run", "distance": 6, "terrain": "road"},
            {"type": "tempo", "distance": 8, "terrain": "road"},
            {"type": "long run", "distance": 12, "terrain": "trail"}
        ]
        
        results = batch_validate(profile, workouts)
        
        # All should be safe
        assert all(r["safe"] for r in results)
    
    def test_recovering_runner_plan(self):
        """Test validation for runner recovering from injury."""
        profile = {
            "injuries": ["shin splints"],
            "cleared_by_doctor": True,
            "weekly_mileage": 15,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["track", "treadmill", "trail"]
        }
        
        workout = {"type": "easy run", "distance": 5, "terrain": "treadmill"}
        
        result = validate_workout(profile, workout)
        
        # Should be safe on treadmill
        assert result["safe"] is True
    
    def test_beginner_first_long_run(self):
        """Test validation for beginner's first long run attempt."""
        profile = {
            "injuries": [],
            "weekly_mileage": 12,
            "experience_level": "beginner",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["road"]
        }
        
        workout = {"type": "long run", "distance": 8, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        # Should be safe (within 1.5x weekly mileage and not high intensity)
        assert result["safe"] is True


class TestInvalidInputs:
    """Test validation with invalid or edge-case inputs."""

    def test_negative_distance_caught_by_input_validation(self):
        """Test that negative distance is caught by input validation."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["road"]
        }
        workout = {"type": "easy run", "distance": -5, "terrain": "road"}
        result = validate_workout(profile, workout)
        assert result["safe"] is False
        assert "Invalid input" in result["reason"]

    def test_negative_weekly_mileage_caught_by_input_validation(self):
        """Test that negative weekly mileage is caught by input validation."""
        profile = {
            "injuries": [],
            "weekly_mileage": -10,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["road"]
        }
        workout = {"type": "long run", "distance": 5, "terrain": "road"}
        result = validate_workout(profile, workout)
        assert result["safe"] is False
        assert "Invalid input" in result["reason"]

    def test_empty_string_workout_type_does_not_crash(self):
        """Test that empty string workout type is handled without crashing."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20,
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "available_terrain": ["road"]
        }
        workout = {"type": "", "distance": 5, "terrain": "road"}
        result = validate_workout(profile, workout)
        assert isinstance(result, dict)
        assert "safe" in result

    def test_empty_string_terrain_caught_by_input_validation(self):
        """Test that empty string terrain is caught by input validation."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20,
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "available_terrain": ["road"]
        }
        workout = {"type": "easy run", "distance": 5, "terrain": ""}
        result = validate_workout(profile, workout)
        # Empty terrain won't match any valid terrain, so won't add terrain facts
        # Workout should still be processed
        assert isinstance(result, dict)
        assert "safe" in result


class TestMultipleInjuries:
    """Test validation when runner has multiple injuries."""

    def test_multiple_injuries_unsafe_terrain_gets_alternative(self):
        """Test that multiple injuries with one safe option still get alternative."""
        profile = {
            "injuries": ["shin splints", "knee pain"],
            "cleared_by_doctor": True,
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["track", "treadmill"]
        }
        workout = {"type": "long run", "distance": 10, "terrain": "track"}
        result = validate_workout(profile, workout)
        assert result["safe"] is False
        assert result["alternative"] is not None
        assert result["alternative"]["terrain"] == "treadmill"

    def test_multiple_injuries_all_terrains_contraindicated_returns_rest(self):
        """Test that when all available terrains are bad for injuries, recommendation is rest."""
        profile = {
            "injuries": ["shin splints"],
            "cleared_by_doctor": True,
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["track"]
        }
        workout = {"type": "long run", "distance": 10, "terrain": "track"}
        result = validate_workout(profile, workout)
        assert result["safe"] is False
        assert result["alternative"] is None
        assert result.get("recommendation") == "rest"


class TestNewInjuryRules:
    """Test validation with newly added injury types."""
    
    def test_back_injury_trail_contraindication(self):
        """Test back injury + trail triggers safety rule."""
        profile = {
            "injuries": ["back pain"],
            "cleared_by_doctor": True,
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["trail", "treadmill"]
        }
        workout = {"type": "long run", "distance": 10, "terrain": "trail"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert result["alternative"] is not None
        assert result["alternative"]["terrain"] == "treadmill"
    
    def test_hamstring_injury_trail_contraindication(self):
        """Test hamstring injury + trail triggers safety rule."""
        profile = {
            "injuries": ["hamstring strain"],
            "cleared_by_doctor": True,
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["trail", "treadmill"]
        }
        workout = {"type": "easy run", "distance": 5, "terrain": "trail"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert result["alternative"] is not None
    
    def test_calf_injury_hard_surface_contraindication(self):
        """Test calf injury + hard surface triggers safety rule."""
        profile = {
            "injuries": ["calf strain"],
            "cleared_by_doctor": True,
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["road", "treadmill"]
        }
        workout = {"type": "easy run", "distance": 5, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert result["alternative"] is not None
        assert result["alternative"]["terrain"] == "treadmill"
    
    def test_ankle_injury_trail_contraindication(self):
        """Test ankle injury + trail triggers safety rule."""
        profile = {
            "injuries": ["ankle sprain"],
            "cleared_by_doctor": True,
            "weekly_mileage": 20,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["trail", "road"]
        }
        workout = {"type": "easy run", "distance": 5, "terrain": "trail"}
        
        result = validate_workout(profile, workout)
        
        assert result["safe"] is False
        assert result["alternative"] is not None
        assert result["alternative"]["terrain"] == "road"


class TestLongRunAsHardWorkout:
    """Test that long runs are treated as hard workouts."""
    
    def test_long_run_yesterday_triggers_consecutive_hard_workouts(self):
        """Test that long run + long run triggers consecutive hard workouts rule."""
        profile = {
            "injuries": [],
            "weekly_mileage": 30,
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 1,
            "days_trained_this_week": 4,
            "fully_recovered": True,
            "sleep_quality": "good",
            "hard_workout_yesterday": True,
            "rest_day_yesterday": False,
            "available_terrain": ["road"]
        }
        workout = {"type": "long run", "distance": 12, "terrain": "road"}
        
        result = validate_workout(profile, workout)
        
        # Should trigger overtraining risk from consecutive hard workouts
        assert result["safe"] is False
        assert "overtraining" in result["reason"].lower() or "back-to-back" in result["reason"].lower()