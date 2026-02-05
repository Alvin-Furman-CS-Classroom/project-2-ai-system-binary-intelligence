"""
Unit tests for facts.py - Fact extraction from runner profiles.

Tests the conversion of structured input data into propositional facts
for use in the inference engine.
"""

import pytest
from datetime import datetime, timedelta
from src.module1_safety_validator.facts import (
    extract_facts,
    profile_to_facts,
    get_fact_explanation,
    _extract_health_facts,
    _extract_injury_facts,
    _extract_recovery_facts,
    _extract_training_facts,
    _extract_environment_facts,
    _extract_workout_facts,
    _compute_derived_facts
)


class TestBasicFactExtraction:
    """Test basic fact extraction functionality."""
    
    def test_extract_facts_returns_set(self):
        """Test that extract_facts returns a set."""
        profile = {"proposed_workout": {"type": "easy run", "distance": 5, "terrain": "road"}}
        facts = extract_facts(profile)
        assert isinstance(facts, set)
    
    def test_empty_profile_returns_facts(self):
        """Test that even empty profile returns some facts."""
        profile = {"proposed_workout": {}}
        facts = extract_facts(profile)
        assert isinstance(facts, set)
    
    def test_profile_to_facts_alias(self):
        """Test that profile_to_facts is an alias for extract_facts."""
        profile = {"injuries": ["shin splints"], "proposed_workout": {"type": "easy run"}}
        facts1 = extract_facts(profile)
        facts2 = profile_to_facts(profile)
        assert facts1 == facts2


class TestHealthFactExtraction:
    """Test extraction of health and symptom facts."""
    
    def test_chest_pain_symptom(self):
        """Test chest pain symptom extraction."""
        profile = {"symptoms": ["chest_pain"], "proposed_workout": {}}
        facts = _extract_health_facts(profile)
        assert "chest_pain" in facts
    
    def test_chest_pain_with_space(self):
        """Test chest pain with space in name."""
        profile = {"symptoms": ["chest pain"], "proposed_workout": {}}
        facts = _extract_health_facts(profile)
        assert "chest_pain" in facts
    
    def test_dizziness_symptom(self):
        """Test dizziness symptom extraction."""
        profile = {"symptoms": ["dizziness"], "proposed_workout": {}}
        facts = _extract_health_facts(profile)
        assert "dizziness" in facts
    
    def test_severe_pain_level(self):
        """Test severe pain level extraction."""
        profile = {"pain_level": "severe", "proposed_workout": {}}
        facts = _extract_health_facts(profile)
        assert "severe_pain" in facts
    
    def test_no_severe_pain_for_mild(self):
        """Test that mild pain doesn't create severe_pain fact."""
        profile = {"pain_level": "mild", "proposed_workout": {}}
        facts = _extract_health_facts(profile)
        assert "severe_pain" not in facts
    
    def test_no_symptoms_returns_empty(self):
        """Test that no symptoms returns empty set."""
        profile = {"proposed_workout": {}}
        facts = _extract_health_facts(profile)
        assert len(facts) == 0


class TestInjuryFactExtraction:
    """Test extraction of injury-related facts."""
    
    def test_shin_splints_injury(self):
        """Test shin splints injury extraction."""
        profile = {"injuries": ["shin splints"], "proposed_workout": {}}
        facts = _extract_injury_facts(profile)
        assert "shin_splints" in facts
        assert "active_injury" in facts
    
    def test_knee_injury(self):
        """Test knee injury extraction."""
        profile = {"injuries": ["knee pain"], "proposed_workout": {}}
        facts = _extract_injury_facts(profile)
        assert "knee_injury" in facts
        assert "active_injury" in facts
    
    def test_plantar_fasciitis_injury(self):
        """Test plantar fasciitis extraction."""
        profile = {"injuries": ["plantar fasciitis"], "proposed_workout": {}}
        facts = _extract_injury_facts(profile)
        assert "plantar_fasciitis" in facts
        assert "active_injury" in facts
    
    def test_plantar_short_form(self):
        """Test plantar extraction with short form."""
        profile = {"injuries": ["plantar"], "proposed_workout": {}}
        facts = _extract_injury_facts(profile)
        assert "plantar_fasciitis" in facts
    
    def test_injury_not_cleared_by_doctor(self):
        """Test injury without doctor clearance."""
        profile = {"injuries": ["shin splints"], "cleared_by_doctor": False, "proposed_workout": {}}
        facts = _extract_injury_facts(profile)
        assert "not_cleared_by_doctor" in facts
    
    def test_injury_cleared_by_doctor(self):
        """Test injury with doctor clearance doesn't add not_cleared fact."""
        profile = {"injuries": ["shin splints"], "cleared_by_doctor": True, "proposed_workout": {}}
        facts = _extract_injury_facts(profile)
        assert "not_cleared_by_doctor" not in facts
    
    def test_no_injuries_returns_empty(self):
        """Test that no injuries returns empty set."""
        profile = {"proposed_workout": {}}
        facts = _extract_injury_facts(profile)
        assert len(facts) == 0


class TestRecoveryFactExtraction:
    """Test extraction of recovery and fatigue facts."""
    
    def test_not_fully_recovered(self):
        """Test not fully recovered extraction."""
        profile = {"fully_recovered": False, "proposed_workout": {}}
        facts = _extract_recovery_facts(profile)
        assert "not_fully_recovered" in facts
    
    def test_fully_recovered_no_fact(self):
        """Test that fully recovered doesn't add negative fact."""
        profile = {"fully_recovered": True, "proposed_workout": {}}
        facts = _extract_recovery_facts(profile)
        assert "not_fully_recovered" not in facts
    
    def test_poor_sleep(self):
        """Test poor sleep extraction."""
        profile = {"sleep_quality": "poor", "proposed_workout": {}}
        facts = _extract_recovery_facts(profile)
        assert "poor_sleep" in facts
    
    def test_good_sleep_no_fact(self):
        """Test that good sleep doesn't add poor_sleep fact."""
        profile = {"sleep_quality": "good", "proposed_workout": {}}
        facts = _extract_recovery_facts(profile)
        assert "poor_sleep" not in facts
    
    def test_zero_rest_days(self):
        """Test zero rest days extraction."""
        profile = {"rest_days_this_week": 0, "proposed_workout": {}}
        facts = _extract_recovery_facts(profile)
        assert "zero_rest_days_this_week" in facts
    
    def test_nonzero_rest_days(self):
        """Test that non-zero rest days doesn't add fact."""
        profile = {"rest_days_this_week": 2, "proposed_workout": {}}
        facts = _extract_recovery_facts(profile)
        assert "zero_rest_days_this_week" not in facts
    
    def test_six_plus_training_days(self):
        """Test six or more training days extraction."""
        profile = {"days_trained_this_week": 6, "proposed_workout": {}}
        facts = _extract_recovery_facts(profile)
        assert "six_plus_training_days" in facts
    
    def test_five_training_days_no_fact(self):
        """Test that 5 training days doesn't trigger six_plus fact."""
        profile = {"days_trained_this_week": 5, "proposed_workout": {}}
        facts = _extract_recovery_facts(profile)
        assert "six_plus_training_days" not in facts
    
    def test_hard_workout_yesterday(self):
        """Test hard workout yesterday extraction."""
        profile = {"hard_workout_yesterday": True, "proposed_workout": {}}
        facts = _extract_recovery_facts(profile)
        assert "hard_workout_yesterday" in facts
    
    def test_no_rest_yesterday(self):
        """Test no rest yesterday extraction."""
        profile = {"rest_day_yesterday": False, "proposed_workout": {}}
        facts = _extract_recovery_facts(profile)
        assert "no_rest_yesterday" in facts


class TestTrainingFactExtraction:
    """Test extraction of training context facts."""
    
    def test_beginner_runner(self):
        """Test beginner experience level extraction."""
        profile = {"experience_level": "beginner", "proposed_workout": {}}
        facts = _extract_training_facts(profile)
        assert "beginner_runner" in facts
    
    def test_intermediate_runner(self):
        """Test intermediate experience level extraction."""
        profile = {"experience_level": "intermediate", "proposed_workout": {}}
        facts = _extract_training_facts(profile)
        assert "intermediate_runner" in facts
    
    def test_advanced_runner(self):
        """Test advanced experience level extraction."""
        profile = {"experience_level": "advanced", "proposed_workout": {}}
        facts = _extract_training_facts(profile)
        assert "advanced_runner" in facts
    
    def test_race_within_7_days(self):
        """Test race within 7 days extraction."""
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
        profile = {"race_date": tomorrow, "proposed_workout": {}}
        facts = _extract_training_facts(profile)
        assert "race_within_7_days" in facts
    
    def test_race_in_14_days_no_fact(self):
        """Test that race in 14 days doesn't trigger fact."""
        future = (datetime.now() + timedelta(days=14)).isoformat()
        profile = {"race_date": future, "proposed_workout": {}}
        facts = _extract_training_facts(profile)
        assert "race_within_7_days" not in facts
    
    def test_invalid_race_date_handled(self):
        """Test that invalid race date doesn't crash."""
        profile = {"race_date": "invalid-date", "proposed_workout": {}}
        facts = _extract_training_facts(profile)
        assert "race_within_7_days" not in facts


class TestEnvironmentFactExtraction:
    """Test extraction of environment and preparation facts."""
    
    def test_extreme_heat(self):
        """Test extreme heat extraction."""
        profile = {"weather": "extreme_heat", "proposed_workout": {}}
        facts = _extract_environment_facts(profile)
        assert "extreme_weather" in facts
    
    def test_extreme_cold(self):
        """Test extreme cold extraction."""
        profile = {"weather": "extreme_cold", "proposed_workout": {}}
        facts = _extract_environment_facts(profile)
        assert "extreme_weather" in facts
    
    def test_normal_weather_no_fact(self):
        """Test that normal weather doesn't add extreme fact."""
        profile = {"weather": "normal", "proposed_workout": {}}
        facts = _extract_environment_facts(profile)
        assert "extreme_weather" not in facts
    
    def test_not_hydrated(self):
        """Test not hydrated extraction."""
        profile = {"hydrated": False, "proposed_workout": {}}
        facts = _extract_environment_facts(profile)
        assert "not_hydrated" in facts
    
    def test_hydrated_no_fact(self):
        """Test that hydrated doesn't add negative fact."""
        profile = {"hydrated": True, "proposed_workout": {}}
        facts = _extract_environment_facts(profile)
        assert "not_hydrated" not in facts
    
    def test_no_proper_footwear(self):
        """Test improper footwear extraction."""
        profile = {"proper_footwear": False, "proposed_workout": {}}
        facts = _extract_environment_facts(profile)
        assert "no_proper_footwear" in facts


class TestWorkoutFactExtraction:
    """Test extraction of proposed workout facts."""
    
    def test_long_run_type(self):
        """Test long run workout type extraction."""
        profile = {"proposed_workout": {"type": "long run"}}
        facts = _extract_workout_facts(profile)
        assert "long_run" in facts
    
    def test_tempo_run_type(self):
        """Test tempo run workout type extraction."""
        profile = {"proposed_workout": {"type": "tempo"}}
        facts = _extract_workout_facts(profile)
        assert "tempo_run" in facts
        assert "high_intensity_workout" in facts
        assert "hard_workout_today" in facts
    
    def test_intervals_type(self):
        """Test intervals workout type extraction."""
        profile = {"proposed_workout": {"type": "intervals"}}
        facts = _extract_workout_facts(profile)
        assert "intervals" in facts
        assert "high_intensity_workout" in facts
        assert "hard_workout_today" in facts
    
    def test_easy_run_type(self):
        """Test easy run workout type extraction."""
        profile = {"proposed_workout": {"type": "easy run"}}
        facts = _extract_workout_facts(profile)
        assert "easy_run" in facts
        assert "high_intensity_workout" not in facts
    
    def test_track_terrain(self):
        """Test track terrain extraction."""
        profile = {"proposed_workout": {"terrain": "track"}}
        facts = _extract_workout_facts(profile)
        assert "track_terrain" in facts
        assert "hard_surface" in facts
    
    def test_road_terrain(self):
        """Test road terrain extraction."""
        profile = {"proposed_workout": {"terrain": "road"}}
        facts = _extract_workout_facts(profile)
        assert "road_terrain" in facts
        assert "hard_surface" in facts
    
    def test_trail_terrain(self):
        """Test trail terrain extraction."""
        profile = {"proposed_workout": {"terrain": "trail"}}
        facts = _extract_workout_facts(profile)
        assert "trail_terrain" in facts
        assert "hard_surface" not in facts
    
    def test_treadmill_terrain(self):
        """Test treadmill terrain extraction."""
        profile = {"proposed_workout": {"terrain": "treadmill"}}
        facts = _extract_workout_facts(profile)
        assert "treadmill_terrain" in facts
        assert "hard_surface" not in facts


class TestDerivedFactComputation:
    """Test computation of derived facts from numerical data."""
    
    def test_excessive_distance_long_run(self):
        """Test excessive distance detection for long runs."""
        profile = {
            "weekly_mileage": 10,
            "proposed_workout": {"type": "long run", "distance": 20}
        }
        facts = extract_facts(profile)
        assert "excessive_distance" in facts
    
    def test_safe_distance_long_run(self):
        """Test that safe long run distance doesn't trigger fact."""
        profile = {
            "weekly_mileage": 20,
            "proposed_workout": {"type": "long run", "distance": 15}
        }
        facts = extract_facts(profile)
        assert "excessive_distance" not in facts
    
    def test_excessive_distance_boundary(self):
        """Test excessive distance at exactly 1.5x boundary."""
        profile = {
            "weekly_mileage": 10,
            "proposed_workout": {"type": "long run", "distance": 15}
        }
        facts = extract_facts(profile)
        assert "excessive_distance" not in facts
    
    def test_excessive_progression(self):
        """Test excessive weekly mileage progression detection."""
        profile = {
            "weekly_mileage": 20,
            "proposed_weekly_mileage": 25
        }
        facts = _compute_derived_facts(set(), profile)
        assert "excessive_progression" in facts
    
    def test_safe_progression(self):
        """Test that 10% progression doesn't trigger fact."""
        profile = {
            "weekly_mileage": 20,
            "proposed_weekly_mileage": 22
        }
        facts = _compute_derived_facts(set(), profile)
        assert "excessive_progression" not in facts


class TestCompleteFactExtraction:
    """Test complete fact extraction with realistic profiles."""
    
    def test_healthy_beginner_easy_run(self):
        """Test fact extraction for healthy beginner doing easy run."""
        profile = {
            "symptoms": [],
            "injuries": [],
            "weekly_mileage": 15,
            "experience_level": "beginner",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "proposed_workout": {
                "type": "easy run",
                "distance": 5,
                "terrain": "road"
            }
        }
        facts = extract_facts(profile)
        
        assert "beginner_runner" in facts
        assert "easy_run" in facts
        assert "road_terrain" in facts
        assert "chest_pain" not in facts
        assert "not_hydrated" not in facts
    
    def test_injured_runner_unsafe_terrain(self):
        """Test fact extraction for injured runner on contraindicated terrain."""
        profile = {
            "injuries": ["shin splints"],
            "cleared_by_doctor": False,
            "weekly_mileage": 20,
            "proposed_workout": {
                "type": "long run",
                "distance": 12,
                "terrain": "track"
            }
        }
        facts = extract_facts(profile)
        
        assert "shin_splints" in facts
        assert "active_injury" in facts
        assert "not_cleared_by_doctor" in facts
        assert "track_terrain" in facts
        assert "long_run" in facts
        assert "hard_surface" in facts


class TestFactExplanations:
    """Test fact explanation helper function."""
    
    def test_get_fact_explanation_known_fact(self):
        """Test getting explanation for known fact."""
        explanation = get_fact_explanation("chest_pain")
        assert "chest pain" in explanation.lower()
        assert len(explanation) > 0
    
    def test_get_fact_explanation_shin_splints(self):
        """Test explanation for shin splints."""
        explanation = get_fact_explanation("shin_splints")
        assert "shin splints" in explanation.lower()
    
    def test_get_fact_explanation_unknown_fact(self):
        """Test explanation for unknown fact returns default message."""
        explanation = get_fact_explanation("unknown_fact_xyz")
        assert "Unknown fact" in explanation
        assert "unknown_fact_xyz" in explanation
    
    def test_all_common_facts_have_explanations(self):
        """Test that common facts have explanations."""
        common_facts = [
            "chest_pain", "shin_splints", "knee_injury", "beginner_runner",
            "track_terrain", "long_run", "excessive_distance"
        ]
        for fact in common_facts:
            explanation = get_fact_explanation(fact)
            assert "Unknown fact" not in explanation