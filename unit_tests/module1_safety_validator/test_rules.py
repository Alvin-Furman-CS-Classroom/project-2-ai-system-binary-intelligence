"""
Unit tests for rules.py - Safety rules knowledge base.

Tests the structure and integrity of the 31 safety rules, rule categories,
and helper functions for accessing the rule base.
"""

import pytest
from src.module1_safety_validator.rules import (
    SafetyRule,
    SAFETY_RULES,
    ABSOLUTE_SAFETY_RULES,
    INJURY_TERRAIN_RULES,
    TRAINING_LOAD_RULES,
    RECOVERY_FATIGUE_RULES,
    ENVIRONMENT_PREPARATION_RULES,
    get_rules_by_category,
    get_rule_by_name
)


class TestSafetyRuleStructure:
    """Test the SafetyRule dataclass structure."""
    
    def test_safety_rule_creation(self):
        """Test creating a SafetyRule instance."""
        rule = SafetyRule(
            name="test_rule",
            conditions=["condition1", "condition2"],
            conclusion="unsafe_high",
            severity="high",
            explanation="Test explanation",
            can_suggest_alternative=True
        )
        
        assert rule.name == "test_rule"
        assert rule.conditions == ["condition1", "condition2"]
        assert rule.conclusion == "unsafe_high"
        assert rule.severity == "high"
        assert rule.explanation == "Test explanation"
        assert rule.can_suggest_alternative is True
    
    def test_safety_rule_has_all_required_fields(self):
        """Test that each rule in SAFETY_RULES has all required fields."""
        for rule in SAFETY_RULES:
            assert hasattr(rule, "name")
            assert hasattr(rule, "conditions")
            assert hasattr(rule, "conclusion")
            assert hasattr(rule, "severity")
            assert hasattr(rule, "explanation")
            assert hasattr(rule, "can_suggest_alternative")
            
            # Verify types
            assert isinstance(rule.name, str)
            assert isinstance(rule.conditions, list)
            assert isinstance(rule.conclusion, str)
            assert isinstance(rule.severity, str)
            assert isinstance(rule.explanation, str)
            assert isinstance(rule.can_suggest_alternative, bool)


class TestRuleCounts:
    """Test that we have the correct number of rules in each category."""
    
    def test_total_rule_count(self):
        """Test that we have exactly 31 rules total."""
        assert len(SAFETY_RULES) == 31
    
    def test_absolute_safety_rules_count(self):
        """Test that we have 4 absolute safety rules."""
        assert len(ABSOLUTE_SAFETY_RULES) == 4
    
    def test_injury_terrain_rules_count(self):
        """Test that we have 17 injury-terrain rules."""
        assert len(INJURY_TERRAIN_RULES) == 17
    
    def test_training_load_rules_count(self):
        """Test that we have 4 training load rules."""
        assert len(TRAINING_LOAD_RULES) == 4
    
    def test_recovery_fatigue_rules_count(self):
        """Test that we have 3 recovery/fatigue rules."""
        assert len(RECOVERY_FATIGUE_RULES) == 3
    
    def test_environment_preparation_rules_count(self):
        """Test that we have 3 environment/preparation rules."""
        assert len(ENVIRONMENT_PREPARATION_RULES) == 3
    
    def test_category_sum_equals_total(self):
        """Test that sum of category counts equals total."""
        category_sum = (
            len(ABSOLUTE_SAFETY_RULES) +
            len(INJURY_TERRAIN_RULES) +
            len(TRAINING_LOAD_RULES) +
            len(RECOVERY_FATIGUE_RULES) +
            len(ENVIRONMENT_PREPARATION_RULES)
        )
        assert category_sum == len(SAFETY_RULES)


class TestAbsoluteSafetyRules:
    """Test absolute safety rules that always block training."""
    
    def test_all_absolute_rules_are_critical(self):
        """Test that all absolute safety rules have critical severity."""
        for rule in ABSOLUTE_SAFETY_RULES:
            assert rule.severity == "critical"
    
    def test_all_absolute_rules_prevent_alternatives(self):
        """Test that absolute safety rules cannot suggest alternatives."""
        for rule in ABSOLUTE_SAFETY_RULES:
            assert rule.can_suggest_alternative is False
    
    def test_chest_pain_rule_exists(self):
        """Test that chest pain blocking rule exists."""
        rule = get_rule_by_name("chest_pain_block")
        assert rule.name == "chest_pain_block"
        assert "chest_pain" in rule.conditions
        assert rule.conclusion == "unsafe_critical"
    
    def test_dizziness_rule_exists(self):
        """Test that dizziness blocking rule exists."""
        rule = get_rule_by_name("dizziness_block")
        assert rule.name == "dizziness_block"
        assert "dizziness" in rule.conditions
        assert rule.conclusion == "unsafe_critical"
    
    def test_severe_pain_rule_exists(self):
        """Test that severe pain blocking rule exists."""
        rule = get_rule_by_name("severe_pain_block")
        assert rule.name == "severe_pain_block"
        assert "severe_pain" in rule.conditions
        assert rule.conclusion == "unsafe_critical"
    
    def test_uncleared_injury_rule_exists(self):
        """Test that uncleared injury blocking rule exists."""
        rule = get_rule_by_name("uncleared_injury_block")
        assert rule.name == "uncleared_injury_block"
        assert "active_injury" in rule.conditions
        assert "not_cleared_by_doctor" in rule.conditions


class TestInjuryTerrainRules:
    """Test injury-terrain contraindication rules."""
    
    def test_all_injury_rules_allow_alternatives(self):
        """Test that injury-terrain rules can suggest alternatives."""
        # All except stress_fracture_running
        for rule in INJURY_TERRAIN_RULES:
            if rule.name != "stress_fracture_running":
                assert rule.can_suggest_alternative is True
    
    def test_shin_splints_track_rule(self):
        """Test shin splints + track contraindication."""
        rule = get_rule_by_name("shin_splints_track")
        assert "shin_splints" in rule.conditions
        assert "track_terrain" in rule.conditions
        assert rule.conclusion == "high_injury_risk"
        assert rule.severity == "high"
    
    def test_shin_splints_road_rule(self):
        """Test shin splints + road contraindication."""
        rule = get_rule_by_name("shin_splints_road")
        assert "shin_splints" in rule.conditions
        assert "road_terrain" in rule.conditions
        assert rule.conclusion == "medium_injury_risk"
        assert rule.severity == "medium"
    
    def test_knee_injury_trail_rule(self):
        """Test knee injury + trail contraindication."""
        rule = get_rule_by_name("knee_injury_trail")
        assert "knee_injury" in rule.conditions
        assert "trail_terrain" in rule.conditions
        assert rule.conclusion == "high_injury_risk"
    
    def test_knee_injury_road_rule(self):
        """Test knee injury + road contraindication."""
        rule = get_rule_by_name("knee_injury_road")
        assert "knee_injury" in rule.conditions
        assert "road_terrain" in rule.conditions
        assert rule.conclusion == "medium_injury_risk"
    
    def test_plantar_fasciitis_hard_surface_rule(self):
        """Test plantar fasciitis + hard surface contraindication."""
        rule = get_rule_by_name("plantar_fasciitis_hard_surface")
        assert "plantar_fasciitis" in rule.conditions
        assert "hard_surface" in rule.conditions
        assert rule.conclusion == "high_injury_risk"
    
    def test_stress_fracture_running_rule(self):
        """Test stress fracture blocks all running."""
        rule = get_rule_by_name("stress_fracture_running")
        assert "stress_fracture" in rule.conditions
        assert rule.conclusion == "unsafe_critical"
        assert rule.can_suggest_alternative is False
    
    def test_hamstring_trail_rule(self):
        """Test hamstring + trail contraindication."""
        rule = get_rule_by_name("hamstring_trail")
        assert "hamstring_injury" in rule.conditions
        assert "trail_terrain" in rule.conditions
        assert rule.conclusion == "high_injury_risk"
    
    def test_calf_trail_rule(self):
        """Test calf + trail contraindication."""
        rule = get_rule_by_name("calf_trail")
        assert "calf_injury" in rule.conditions
        assert "trail_terrain" in rule.conditions
        assert rule.conclusion == "high_injury_risk"
    
    def test_calf_hard_surface_rule(self):
        """Test calf + hard surface contraindication."""
        rule = get_rule_by_name("calf_hard_surface")
        assert "calf_injury" in rule.conditions
        assert "hard_surface" in rule.conditions
        assert rule.conclusion == "medium_injury_risk"
    
    def test_ankle_trail_rule(self):
        """Test ankle + trail contraindication."""
        rule = get_rule_by_name("ankle_trail")
        assert "ankle_injury" in rule.conditions
        assert "trail_terrain" in rule.conditions
        assert rule.conclusion == "high_injury_risk"
    
    def test_back_injury_trail_rule(self):
        """Test back injury + trail contraindication."""
        rule = get_rule_by_name("back_injury_trail")
        assert "back_injury" in rule.conditions
        assert "trail_terrain" in rule.conditions
        assert rule.conclusion == "high_injury_risk"
    
    def test_back_injury_hard_surface_rule(self):
        """Test back injury + hard surface contraindication."""
        rule = get_rule_by_name("back_injury_hard_surface")
        assert "back_injury" in rule.conditions
        assert "hard_surface" in rule.conditions
        assert rule.conclusion == "medium_injury_risk"


class TestTrainingLoadRules:
    """Test training load and progression rules."""
    
    def test_excessive_distance_rule(self):
        """Test excessive distance rule."""
        rule = get_rule_by_name("excessive_distance")
        assert "excessive_distance" in rule.conditions
        assert rule.conclusion == "unsafe_high"
        assert rule.can_suggest_alternative is True
    
    def test_beginner_high_intensity_rule(self):
        """Test beginner + high intensity restriction."""
        rule = get_rule_by_name("beginner_high_intensity")
        assert "beginner_runner" in rule.conditions
        assert "high_intensity_workout" in rule.conditions
        assert rule.severity == "high"
    
    def test_consecutive_hard_workouts_rule(self):
        """Test consecutive hard workouts rule."""
        rule = get_rule_by_name("consecutive_hard_workouts")
        assert "hard_workout_yesterday" in rule.conditions
        assert "hard_workout_today" in rule.conditions
        assert "no_rest_yesterday" in rule.conditions
        assert rule.conclusion == "overtraining_risk"
    
    def test_race_week_long_run_rule(self):
        """Test race week long run restriction."""
        rule = get_rule_by_name("race_week_long_run")
        assert "race_within_7_days" in rule.conditions
        assert "long_run" in rule.conditions


class TestRecoveryFatigueRules:
    """Test recovery and fatigue rules."""
    
    def test_insufficient_recovery_rule(self):
        """Test insufficient recovery + high intensity rule."""
        rule = get_rule_by_name("insufficient_recovery_high_intensity")
        assert "not_fully_recovered" in rule.conditions
        assert "high_intensity_workout" in rule.conditions
        assert rule.conclusion == "unsafe_medium"
    
    def test_poor_sleep_rule(self):
        """Test poor sleep + high intensity rule."""
        rule = get_rule_by_name("poor_sleep_high_intensity")
        assert "poor_sleep" in rule.conditions
        assert "high_intensity_workout" in rule.conditions
    
    def test_no_rest_days_rule(self):
        """Test no rest days rule."""
        rule = get_rule_by_name("no_rest_days")
        assert "zero_rest_days_this_week" in rule.conditions
        assert "six_plus_training_days" in rule.conditions
        assert rule.conclusion == "overtraining_risk"


class TestEnvironmentPreparationRules:
    """Test environment and preparation rules."""
    
    def test_extreme_weather_rule(self):
        """Test extreme weather rule."""
        rule = get_rule_by_name("extreme_weather")
        assert "extreme_weather" in rule.conditions
        assert rule.conclusion == "unsafe_medium"
        assert rule.can_suggest_alternative is False
    
    def test_not_hydrated_rule(self):
        """Test dehydration rule."""
        rule = get_rule_by_name("not_hydrated")
        assert "not_hydrated" in rule.conditions
        assert rule.conclusion == "unsafe_medium"
    
    def test_improper_footwear_rule(self):
        """Test improper footwear rule."""
        rule = get_rule_by_name("improper_footwear")
        assert "no_proper_footwear" in rule.conditions
        assert rule.conclusion == "unsafe_medium"


class TestRuleConditions:
    """Test rule condition integrity."""
    
    def test_all_rules_have_conditions(self):
        """Test that every rule has at least one condition."""
        for rule in SAFETY_RULES:
            assert len(rule.conditions) > 0, f"Rule {rule.name} has no conditions"
    
    def test_all_rules_have_conclusions(self):
        """Test that every rule has a conclusion."""
        for rule in SAFETY_RULES:
            assert rule.conclusion, f"Rule {rule.name} has empty conclusion"
    
    def test_all_rules_have_explanations(self):
        """Test that every rule has an explanation."""
        for rule in SAFETY_RULES:
            assert rule.explanation, f"Rule {rule.name} has empty explanation"
            assert len(rule.explanation) > 10, f"Rule {rule.name} explanation too short"
    
    def test_all_rule_names_are_unique(self):
        """Test that all rule names are unique."""
        names = [rule.name for rule in SAFETY_RULES]
        assert len(names) == len(set(names)), "Duplicate rule names found"


class TestHelperFunctions:
    """Test helper functions for accessing rules."""
    
    def test_get_rules_by_category_absolute(self):
        """Test getting absolute safety rules by category."""
        rules = get_rules_by_category("absolute")
        assert len(rules) == 4
        assert all(rule.severity == "critical" for rule in rules)
    
    def test_get_rules_by_category_injury(self):
        """Test getting injury-terrain rules by category."""
        rules = get_rules_by_category("injury")
        assert len(rules) == 17
    
    def test_get_rules_by_category_training(self):
        """Test getting training load rules by category."""
        rules = get_rules_by_category("training")
        assert len(rules) == 4
    
    def test_get_rules_by_category_recovery(self):
        """Test getting recovery rules by category."""
        rules = get_rules_by_category("recovery")
        assert len(rules) == 3
    
    def test_get_rules_by_category_environment(self):
        """Test getting environment rules by category."""
        rules = get_rules_by_category("environment")
        assert len(rules) == 3
    
    def test_get_rules_by_category_invalid(self):
        """Test getting rules with invalid category returns empty list."""
        rules = get_rules_by_category("invalid_category")
        assert rules == []
    
    def test_get_rule_by_name_valid(self):
        """Test getting a rule by valid name."""
        rule = get_rule_by_name("chest_pain_block")
        assert rule.name == "chest_pain_block"
        assert isinstance(rule, SafetyRule)
    
    def test_get_rule_by_name_invalid(self):
        """Test getting a rule by invalid name raises ValueError."""
        with pytest.raises(ValueError, match="Rule 'nonexistent_rule' not found"):
            get_rule_by_name("nonexistent_rule")


class TestRuleSeverityLevels:
    """Test rule severity level distribution."""
    
    def test_critical_severity_rules(self):
        """Test that critical rules are only in absolute safety category."""
        critical_rules = [rule for rule in SAFETY_RULES if rule.severity == "critical"]
        # 4 from absolute + 1 from stress fracture
        assert len(critical_rules) == 5
    
    def test_high_severity_exists(self):
        """Test that high severity rules exist."""
        high_rules = [rule for rule in SAFETY_RULES if rule.severity == "high"]
        assert len(high_rules) > 0
    
    def test_medium_severity_exists(self):
        """Test that medium severity rules exist."""
        medium_rules = [rule for rule in SAFETY_RULES if rule.severity == "medium"]
        assert len(medium_rules) > 0
    
    def test_valid_severity_values(self):
        """Test that all rules have valid severity values."""
        valid_severities = {"critical", "high", "medium"}
        for rule in SAFETY_RULES:
            assert rule.severity in valid_severities, f"Rule {rule.name} has invalid severity: {rule.severity}"