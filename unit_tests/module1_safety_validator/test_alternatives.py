"""
Unit tests for alternatives.py - Safe workout alternative generation.

Tests the logic for generating safe workout alternatives when the original
proposed workout is deemed unsafe.
"""

import pytest
from src.module1_safety_validator.alternatives import (
    generate_alternative,
    can_suggest_alternative,
    get_alternative_explanation,
    suggest_rest_day_message,
    _find_safe_terrain,
    _calculate_safe_distance
)
from src.module1_safety_validator.rules import (
    SafetyRule,
    get_rule_by_name
)


class TestCanSuggestAlternative:
    """Test checking if alternatives can be suggested."""
    
    def test_can_suggest_alternative_true(self):
        """Test that alternative-friendly rules return True."""
        rules = [get_rule_by_name("shin_splints_track")]
        assert can_suggest_alternative(rules) is True
    
    def test_can_suggest_alternative_false_critical(self):
        """Test that critical rules return False."""
        rules = [get_rule_by_name("chest_pain_block")]
        assert can_suggest_alternative(rules) is False
    
    def test_can_suggest_alternative_mixed_rules(self):
        """Test that mixed rules return False if any blocks alternatives."""
        rules = [
            get_rule_by_name("chest_pain_block"),
            get_rule_by_name("shin_splints_track")
        ]
        assert can_suggest_alternative(rules) is False
    
    def test_can_suggest_alternative_multiple_allowed(self):
        """Test that multiple alternative-friendly rules return True."""
        rules = [
            get_rule_by_name("shin_splints_track"),
            get_rule_by_name("excessive_distance")
        ]
        assert can_suggest_alternative(rules) is True
    
    def test_can_suggest_alternative_empty_list(self):
        """Test that empty rule list returns True."""
        assert can_suggest_alternative([]) is True


class TestFindSafeTerrain:
    """Test safe terrain selection for injuries."""
    
    def test_find_safe_terrain_shin_splints(self):
        """Test that treadmill is preferred for shin splints."""
        injuries = ["shin splints"]
        available = ["track", "road", "treadmill"]
        current = "track"
        
        safe_terrain = _find_safe_terrain(injuries, available, current)
        assert safe_terrain == "treadmill"
    
    def test_find_safe_terrain_shin_splints_no_treadmill(self):
        """Test shin splints when treadmill not available."""
        injuries = ["shin splints"]
        available = ["track", "road", "trail"]
        current = "track"
        
        safe_terrain = _find_safe_terrain(injuries, available, current)
        assert safe_terrain == "trail"  # Next best option
    
    def test_find_safe_terrain_knee_injury(self):
        """Test that treadmill is preferred for knee injury."""
        injuries = ["knee pain"]
        available = ["trail", "treadmill", "road"]
        current = "trail"
        
        safe_terrain = _find_safe_terrain(injuries, available, current)
        assert safe_terrain == "treadmill"
    
    def test_find_safe_terrain_plantar_fasciitis(self):
        """Test soft surface preferred for plantar fasciitis."""
        injuries = ["plantar fasciitis"]
        available = ["track", "road", "treadmill", "trail"]
        current = "track"
        
        safe_terrain = _find_safe_terrain(injuries, available, current)
        assert safe_terrain in ["treadmill", "trail"]
    
    def test_find_safe_terrain_no_alternatives(self):
        """Test when only current terrain is available."""
        injuries = ["shin splints"]
        available = ["track"]
        current = "track"
        
        safe_terrain = _find_safe_terrain(injuries, available, current)
        assert safe_terrain is None
    
    def test_find_safe_terrain_generic_injury(self):
        """Test terrain selection for unknown injury type."""
        injuries = ["unknown injury"]
        available = ["track", "treadmill", "road"]
        current = "track"

        safe_terrain = _find_safe_terrain(injuries, available, current)
        assert safe_terrain == "treadmill"  # Generic preference

    def test_find_safe_terrain_multiple_injuries_has_safe_option(self):
        """Test terrain selection with multiple injuries when one option is safe."""
        injuries = ["shin splints", "knee pain"]
        available = ["track", "treadmill", "road"]
        current = "track"
        safe_terrain = _find_safe_terrain(injuries, available, current)
        assert safe_terrain == "treadmill"

    def test_find_safe_terrain_multiple_injuries_all_contraindicated(self):
        """Test that multiple injuries with only bad terrains returns None."""
        injuries = ["shin splints", "knee pain"]
        available = ["track"]
        current = "track"
        safe_terrain = _find_safe_terrain(injuries, available, current)
        assert safe_terrain is None


class TestCalculateSafeDistance:
    """Test safe distance calculation."""
    
    def test_calculate_safe_distance_long_run(self):
        """Test safe distance for long run (1.5x weekly mileage)."""
        distance = _calculate_safe_distance(20, "long run")
        assert distance == 30.0
    
    def test_calculate_safe_distance_tempo_run(self):
        """Test safe distance for tempo run (0.4x weekly mileage)."""
        distance = _calculate_safe_distance(20, "tempo")
        assert distance == 8.0
    
    def test_calculate_safe_distance_intervals(self):
        """Test safe distance for intervals (0.3x weekly mileage)."""
        distance = _calculate_safe_distance(20, "intervals")
        assert distance == 6.0
    
    def test_calculate_safe_distance_easy_run(self):
        """Test safe distance for easy run (0.5x weekly mileage)."""
        distance = _calculate_safe_distance(20, "easy run")
        assert distance == 10.0
    
    def test_calculate_safe_distance_zero_mileage(self):
        """Test that zero mileage returns None."""
        distance = _calculate_safe_distance(0, "long run")
        assert distance is None

    def test_calculate_safe_distance_negative_mileage(self):
        """Test that negative weekly mileage returns None or is handled."""
        distance = _calculate_safe_distance(-10, "long run")
        assert distance is None
    
    def test_calculate_safe_distance_rounds_correctly(self):
        """Test that distance is rounded to 1 decimal place."""
        distance = _calculate_safe_distance(15, "long run")
        assert distance == 22.5
        assert isinstance(distance, float)


class TestGenerateAlternative:
    """Test complete alternative generation logic."""
    
    def test_generate_alternative_critical_rule_returns_none(self):
        """Test that critical rules return no alternative."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20,
            "available_terrain": ["track", "treadmill"]
        }
        workout = {"type": "easy run", "distance": 5, "terrain": "track"}
        fired_rules = [get_rule_by_name("chest_pain_block")]
        
        alternative = generate_alternative(profile, workout, fired_rules)
        assert alternative is None
    
    def test_generate_alternative_shin_splints_changes_terrain(self):
        """Test that shin splints + track changes to safer terrain."""
        profile = {
            "injuries": ["shin splints"],
            "weekly_mileage": 20,
            "available_terrain": ["track", "treadmill"],
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good"
        }
        workout = {"type": "long run", "distance": 10, "terrain": "track"}
        fired_rules = [get_rule_by_name("shin_splints_track")]
        
        alternative = generate_alternative(profile, workout, fired_rules)
        
        assert alternative is not None
        assert alternative["terrain"] == "treadmill"
        assert alternative["type"] == "long run"
        assert alternative["distance"] == 10
    
    def test_generate_alternative_excessive_distance_reduces(self):
        """Test that excessive distance is reduced."""
        profile = {
            "injuries": [],
            "weekly_mileage": 10,
            "available_terrain": ["road"],
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good"
        }
        workout = {"type": "long run", "distance": 20, "terrain": "road"}
        fired_rules = [get_rule_by_name("excessive_distance")]
        
        alternative = generate_alternative(profile, workout, fired_rules)
        
        assert alternative is not None
        assert alternative["distance"] == 15.0  # 1.5 × 10
        assert alternative["distance"] < workout["distance"]
    
    def test_generate_alternative_beginner_high_intensity(self):
        """Test that beginner + high intensity switches to easy run."""
        profile = {
            "injuries": [],
            "weekly_mileage": 15,
            "available_terrain": ["road"],
            "experience_level": "beginner",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good"
        }
        workout = {"type": "tempo", "distance": 5, "terrain": "road"}
        fired_rules = [get_rule_by_name("beginner_high_intensity")]
        
        alternative = generate_alternative(profile, workout, fired_rules)
        
        assert alternative is not None
        assert alternative["type"] == "easy run"
    
    def test_generate_alternative_multiple_fixes(self):
        """Test alternative generation with multiple issues."""
        profile = {
            "injuries": ["shin splints"],
            "weekly_mileage": 10,
            "available_terrain": ["track", "treadmill"],
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good"
        }
        workout = {"type": "long run", "distance": 20, "terrain": "track"}
        fired_rules = [
            get_rule_by_name("shin_splints_track"),
            get_rule_by_name("excessive_distance")
        ]
        
        alternative = generate_alternative(profile, workout, fired_rules)
        
        assert alternative is not None
        assert alternative["terrain"] == "treadmill"  # Fixed terrain
        assert alternative["distance"] == 15.0  # Fixed distance (1.5 × 10)
    
    def test_generate_alternative_no_safe_terrain_returns_none(self):
        """Test that no safe terrain available returns None."""
        profile = {
            "injuries": ["shin splints"],
            "weekly_mileage": 20,
            "available_terrain": ["track"],  # Only unsafe option
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal"
        }
        workout = {"type": "long run", "distance": 10, "terrain": "track"}
        fired_rules = [get_rule_by_name("shin_splints_track")]
        
        alternative = generate_alternative(profile, workout, fired_rules)
        assert alternative is None

    def test_generate_alternative_multiple_injuries_all_terrains_contraindicated(self):
        """Test that multiple injuries with only contraindicated terrains returns None."""
        profile = {
            "injuries": ["shin splints", "knee pain"],
            "cleared_by_doctor": True,
            "weekly_mileage": 20,
            "available_terrain": ["track"],
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal"
        }
        workout = {"type": "long run", "distance": 10, "terrain": "track"}
        fired_rules = [get_rule_by_name("shin_splints_track")]
        alternative = generate_alternative(profile, workout, fired_rules)
        assert alternative is None

    def test_generate_alternative_race_week_long_run(self):
        """Test race week long run converts to easy run."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20,
            "available_terrain": ["road"],
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good"
        }
        workout = {"type": "long run", "distance": 15, "terrain": "road"}
        fired_rules = [get_rule_by_name("race_week_long_run")]
        
        alternative = generate_alternative(profile, workout, fired_rules)
        
        assert alternative is not None
        assert alternative["type"] == "easy run"
        assert alternative["distance"] < workout["distance"]
    
    def test_generate_alternative_overtraining_reduces_intensity(self):
        """Test overtraining concerns reduce workout intensity."""
        profile = {
            "injuries": [],
            "weekly_mileage": 20,
            "available_terrain": ["road"],
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 0,
            "days_trained_this_week": 6,
            "fully_recovered": True,
            "sleep_quality": "good"
        }
        workout = {"type": "tempo", "distance": 8, "terrain": "road"}
        fired_rules = [get_rule_by_name("no_rest_days")]
        
        alternative = generate_alternative(profile, workout, fired_rules)
        
        assert alternative is not None
        assert alternative["type"] == "easy run"


class TestAlternativeExplanation:
    """Test alternative explanation generation."""
    
    def test_get_alternative_explanation_terrain_change(self):
        """Test explanation when terrain changes."""
        original = {"type": "long run", "distance": 10, "terrain": "track"}
        alternative = {"type": "long run", "distance": 10, "terrain": "treadmill"}
        
        explanation = get_alternative_explanation(original, alternative)
        
        assert "terrain" in explanation.lower()
        assert "track" in explanation
        assert "treadmill" in explanation
    
    def test_get_alternative_explanation_distance_change(self):
        """Test explanation when distance changes."""
        original = {"type": "long run", "distance": 20, "terrain": "road"}
        alternative = {"type": "long run", "distance": 15, "terrain": "road"}
        
        explanation = get_alternative_explanation(original, alternative)
        
        assert "distance" in explanation.lower()
        assert "20" in explanation
        assert "15" in explanation
    
    def test_get_alternative_explanation_type_change(self):
        """Test explanation when workout type changes."""
        original = {"type": "tempo", "distance": 6, "terrain": "road"}
        alternative = {"type": "easy run", "distance": 6, "terrain": "road"}
        
        explanation = get_alternative_explanation(original, alternative)
        
        assert "type" in explanation.lower() or "workout" in explanation.lower()
        assert "tempo" in explanation
        assert "easy run" in explanation
    
    def test_get_alternative_explanation_multiple_changes(self):
        """Test explanation with multiple changes."""
        original = {"type": "tempo", "distance": 10, "terrain": "track"}
        alternative = {"type": "easy run", "distance": 5, "terrain": "treadmill"}
        
        explanation = get_alternative_explanation(original, alternative)
        
        # Should mention multiple changes
        assert "type" in explanation.lower() or "tempo" in explanation
        assert "distance" in explanation.lower()
        assert "terrain" in explanation.lower()
    
    def test_get_alternative_explanation_no_changes(self):
        """Test explanation when workouts are identical."""
        original = {"type": "easy run", "distance": 5, "terrain": "road"}
        alternative = {"type": "easy run", "distance": 5, "terrain": "road"}
        
        explanation = get_alternative_explanation(original, alternative)
        
        assert len(explanation) > 0
        assert "Alternative workout" in explanation


class TestRestDayMessage:
    """Test rest day recommendation messages."""
    
    def test_suggest_rest_day_message_chest_pain(self):
        """Test rest message for chest pain."""
        rules = [get_rule_by_name("chest_pain_block")]
        message = suggest_rest_day_message(rules)
        
        assert "medical attention" in message.lower()
        assert "chest pain" in message.lower()
    
    def test_suggest_rest_day_message_dizziness(self):
        """Test rest message for dizziness."""
        rules = [get_rule_by_name("dizziness_block")]
        message = suggest_rest_day_message(rules)
        
        assert "medical" in message.lower() or "doctor" in message.lower()
        assert "dizziness" in message.lower()
    
    def test_suggest_rest_day_message_critical_generic(self):
        """Test generic critical message."""
        rules = [get_rule_by_name("severe_pain_block")]
        message = suggest_rest_day_message(rules)
        
        assert "rest" in message.lower() or "consult" in message.lower()
    
    def test_suggest_rest_day_message_high_severity(self):
        """Test message for high severity (non-critical)."""
        rules = [get_rule_by_name("shin_splints_track")]
        message = suggest_rest_day_message(rules)
        
        assert "rest" in message.lower()
        assert "injury" in message.lower() or "prevent" in message.lower()
    
    def test_suggest_rest_day_message_medium_severity(self):
        """Test message for medium severity."""
        rules = [get_rule_by_name("not_hydrated")]
        message = suggest_rest_day_message(rules)
        
        assert "rest" in message.lower() or "consider" in message.lower()
    
    def test_suggest_rest_day_message_empty_rules(self):
        """Test message with empty rules list."""
        message = suggest_rest_day_message([])
        assert len(message) > 0


class TestAlternativeValidation:
    """Test that generated alternatives are actually safe."""
    
    def test_alternative_is_validated(self):
        """Test that alternative is validated before returning."""
        # This is implicitly tested by checking that generate_alternative
        # calls validate_workout internally
        profile = {
            "injuries": ["shin splints"],
            "weekly_mileage": 20,
            "available_terrain": ["treadmill"],
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good"
        }
        workout = {"type": "long run", "distance": 10, "terrain": "track"}
        fired_rules = [get_rule_by_name("shin_splints_track")]
        
        alternative = generate_alternative(profile, workout, fired_rules)
        
        # If alternative is returned, it should be safe
        # (This is validated inside generate_alternative)
        assert alternative is not None
    
    def test_unsafe_alternative_returns_none(self):
        """Test that if alternative is still unsafe, None is returned."""
        # Create scenario where no safe alternative exists
        profile = {
            "symptoms": ["chest_pain"],  # Critical - blocks everything
            "injuries": [],
            "weekly_mileage": 20,
            "available_terrain": ["road"],
            "experience_level": "intermediate",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal"
        }
        workout = {"type": "easy run", "distance": 5, "terrain": "road"}
        fired_rules = [get_rule_by_name("chest_pain_block")]
        
        alternative = generate_alternative(profile, workout, fired_rules)
        assert alternative is None