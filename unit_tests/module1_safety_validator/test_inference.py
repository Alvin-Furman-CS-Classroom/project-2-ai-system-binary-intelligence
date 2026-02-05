"""
Unit tests for inference.py - Forward chaining inference engine.

Tests the propositional logic inference algorithm, safety determination,
and helper functions for explaining inference chains.
"""

import pytest
from src.module1_safety_validator.inference import (
    forward_chain,
    determine_safety,
    explain_inference,
    get_critical_rules,
    get_alternative_blocking_rules,
    validate_rule_consistency,
    check_facts_coverage
)
from src.module1_safety_validator.rules import (
    SafetyRule,
    SAFETY_RULES,
    get_rule_by_name
)


class TestForwardChaining:
    """Test the forward chaining inference algorithm."""
    
    def test_forward_chain_returns_tuple(self):
        """Test that forward_chain returns a tuple of (facts, rules)."""
        facts = {"chest_pain"}
        result = forward_chain(facts)
        assert isinstance(result, tuple)
        assert len(result) == 2
        all_facts, fired_rules = result
        assert isinstance(all_facts, set)
        assert isinstance(fired_rules, list)
    
    def test_forward_chain_preserves_initial_facts(self):
        """Test that forward chaining preserves initial facts."""
        initial_facts = {"chest_pain", "beginner_runner"}
        all_facts, _ = forward_chain(initial_facts)
        assert "chest_pain" in all_facts
        assert "beginner_runner" in all_facts
    
    def test_forward_chain_chest_pain_fires_rule(self):
        """Test that chest pain triggers the chest_pain_block rule."""
        facts = {"chest_pain"}
        all_facts, fired_rules = forward_chain(facts)
        
        assert "unsafe_critical" in all_facts
        assert len(fired_rules) > 0
        assert any(rule.name == "chest_pain_block" for rule in fired_rules)
    
    def test_forward_chain_shin_splints_track(self):
        """Test that shin splints + track triggers injury risk rule."""
        facts = {"shin_splints", "track_terrain"}
        all_facts, fired_rules = forward_chain(facts)
        
        assert "high_injury_risk" in all_facts
        assert any(rule.name == "shin_splints_track" for rule in fired_rules)
    
    def test_forward_chain_no_matching_rules(self):
        """Test that no rules fire when conditions aren't met."""
        facts = {"beginner_runner", "easy_run"}
        all_facts, fired_rules = forward_chain(facts)
        
        assert len(fired_rules) == 0
        assert all_facts == facts
    
    def test_forward_chain_multiple_rules_fire(self):
        """Test that multiple rules can fire in one inference."""
        facts = {
            "shin_splints",
            "track_terrain",
            "excessive_distance"
        }
        all_facts, fired_rules = forward_chain(facts)
        
        # Should fire both shin_splints_track and excessive_distance rules
        assert len(fired_rules) >= 2
        rule_names = [rule.name for rule in fired_rules]
        assert "shin_splints_track" in rule_names
        assert "excessive_distance" in rule_names
    
    def test_forward_chain_convergence(self):
        """Test that forward chaining terminates (reaches fixed point)."""
        # Create facts that could potentially loop
        facts = {
            "chest_pain",
            "dizziness",
            "severe_pain",
            "shin_splints",
            "track_terrain"
        }
        all_facts, fired_rules = forward_chain(facts)
        
        # Should terminate without infinite loop
        assert len(fired_rules) <= len(SAFETY_RULES)
    
    def test_forward_chain_with_custom_rules(self):
        """Test forward chaining with custom rule set."""
        custom_rules = [
            SafetyRule(
                name="test_rule",
                conditions=["condition_a", "condition_b"],
                conclusion="conclusion_c",
                severity="high",
                explanation="Test rule",
                can_suggest_alternative=True
            )
        ]
        facts = {"condition_a", "condition_b"}
        all_facts, fired_rules = forward_chain(facts, custom_rules)
        
        assert "conclusion_c" in all_facts
        assert len(fired_rules) == 1
        assert fired_rules[0].name == "test_rule"
    
    def test_forward_chain_partial_conditions_dont_fire(self):
        """Test that rules don't fire with partial conditions."""
        # Rule needs both shin_splints AND track_terrain
        facts = {"shin_splints"}  # Only one condition
        all_facts, fired_rules = forward_chain(facts)
        
        # shin_splints_track rule should NOT fire
        rule_names = [rule.name for rule in fired_rules]
        assert "shin_splints_track" not in rule_names
    
    def test_forward_chain_rule_fires_only_once(self):
        """Test that each rule fires at most once."""
        facts = {"chest_pain"}
        all_facts, fired_rules = forward_chain(facts)
        
        # Count occurrences of each rule
        rule_names = [rule.name for rule in fired_rules]
        for name in set(rule_names):
            assert rule_names.count(name) == 1


class TestDetermineSafety:
    """Test safety determination from derived facts."""
    
    def test_determine_safety_safe_workout(self):
        """Test that safe facts return True."""
        facts = {"beginner_runner", "easy_run", "road_terrain"}
        is_safe, severity = determine_safety(facts)
        
        assert is_safe is True
        assert severity == "none"
    
    def test_determine_safety_critical_unsafe(self):
        """Test that critical unsafe facts return False with critical severity."""
        facts = {"unsafe_critical", "chest_pain"}
        is_safe, severity = determine_safety(facts)
        
        assert is_safe is False
        assert severity == "critical"
    
    def test_determine_safety_high_injury_risk(self):
        """Test that high injury risk returns False with high severity."""
        facts = {"high_injury_risk", "shin_splints", "track_terrain"}
        is_safe, severity = determine_safety(facts)
        
        assert is_safe is False
        assert severity == "high"
    
    def test_determine_safety_unsafe_high(self):
        """Test that unsafe_high returns False with high severity."""
        facts = {"unsafe_high", "excessive_distance"}
        is_safe, severity = determine_safety(facts)
        
        assert is_safe is False
        assert severity == "high"
    
    def test_determine_safety_medium_injury_risk(self):
        """Test that medium injury risk returns False with medium severity."""
        facts = {"medium_injury_risk"}
        is_safe, severity = determine_safety(facts)
        
        assert is_safe is False
        assert severity == "medium"
    
    def test_determine_safety_unsafe_medium(self):
        """Test that unsafe_medium returns False with medium severity."""
        facts = {"unsafe_medium", "not_hydrated"}
        is_safe, severity = determine_safety(facts)
        
        assert is_safe is False
        assert severity == "medium"
    
    def test_determine_safety_overtraining_risk(self):
        """Test that overtraining risk returns False with medium severity."""
        facts = {"overtraining_risk"}
        is_safe, severity = determine_safety(facts)
        
        assert is_safe is False
        assert severity == "medium"
    
    def test_determine_safety_priority_critical_over_high(self):
        """Test that critical severity takes priority over high."""
        facts = {"unsafe_critical", "high_injury_risk"}
        is_safe, severity = determine_safety(facts)
        
        assert severity == "critical"
    
    def test_determine_safety_priority_high_over_medium(self):
        """Test that high severity takes priority over medium."""
        facts = {"unsafe_high", "unsafe_medium"}
        is_safe, severity = determine_safety(facts)
        
        assert severity == "high"


class TestExplainInference:
    """Test inference explanation generation."""
    
    def test_explain_inference_returns_string(self):
        """Test that explain_inference returns a string."""
        initial = {"chest_pain"}
        derived = {"chest_pain", "unsafe_critical"}
        fired = [get_rule_by_name("chest_pain_block")]
        
        explanation = explain_inference(initial, derived, fired)
        assert isinstance(explanation, str)
        assert len(explanation) > 0
    
    def test_explain_inference_contains_initial_facts(self):
        """Test that explanation includes initial facts."""
        initial = {"chest_pain", "beginner_runner"}
        derived = initial.copy()
        fired = []
        
        explanation = explain_inference(initial, derived, fired)
        assert "chest_pain" in explanation
        assert "beginner_runner" in explanation
    
    def test_explain_inference_shows_fired_rules(self):
        """Test that explanation shows which rules fired."""
        initial = {"chest_pain"}
        rule = get_rule_by_name("chest_pain_block")
        derived = {"chest_pain", "unsafe_critical"}
        fired = [rule]
        
        explanation = explain_inference(initial, derived, fired)
        assert "chest_pain_block" in explanation
        assert rule.explanation in explanation
    
    def test_explain_inference_shows_conclusion(self):
        """Test that explanation shows final safety conclusion."""
        initial = {"chest_pain"}
        derived = {"chest_pain", "unsafe_critical"}
        fired = [get_rule_by_name("chest_pain_block")]
        
        explanation = explain_inference(initial, derived, fired)
        assert "UNSAFE" in explanation
        assert "critical" in explanation
    
    def test_explain_inference_safe_conclusion(self):
        """Test explanation for safe workout."""
        initial = {"easy_run", "road_terrain"}
        derived = initial.copy()
        fired = []
        
        explanation = explain_inference(initial, derived, fired)
        assert "SAFE" in explanation


class TestCriticalRules:
    """Test critical rule filtering."""
    
    def test_get_critical_rules_filters_correctly(self):
        """Test that get_critical_rules returns only critical rules."""
        all_fired = [
            get_rule_by_name("chest_pain_block"),
            get_rule_by_name("shin_splints_track")
        ]
        critical = get_critical_rules(all_fired)
        
        assert len(critical) == 1
        assert critical[0].name == "chest_pain_block"
        assert critical[0].severity == "critical"
    
    def test_get_critical_rules_empty_when_none(self):
        """Test that get_critical_rules returns empty list when no critical rules."""
        all_fired = [get_rule_by_name("shin_splints_track")]
        critical = get_critical_rules(all_fired)
        
        assert len(critical) == 0
    
    def test_get_critical_rules_multiple_critical(self):
        """Test filtering multiple critical rules."""
        all_fired = [
            get_rule_by_name("chest_pain_block"),
            get_rule_by_name("dizziness_block"),
            get_rule_by_name("shin_splints_track")
        ]
        critical = get_critical_rules(all_fired)
        
        assert len(critical) == 2
        assert all(rule.severity == "critical" for rule in critical)


class TestAlternativeBlockingRules:
    """Test alternative blocking rule filtering."""
    
    def test_get_alternative_blocking_rules(self):
        """Test getting rules that block alternatives."""
        all_fired = [
            get_rule_by_name("chest_pain_block"),
            get_rule_by_name("shin_splints_track")
        ]
        blocking = get_alternative_blocking_rules(all_fired)
        
        assert len(blocking) == 1
        assert blocking[0].name == "chest_pain_block"
        assert blocking[0].can_suggest_alternative is False
    
    def test_get_alternative_blocking_rules_none(self):
        """Test when no rules block alternatives."""
        all_fired = [get_rule_by_name("shin_splints_track")]
        blocking = get_alternative_blocking_rules(all_fired)
        
        assert len(blocking) == 0


class TestRuleConsistency:
    """Test rule base consistency validation."""
    
    def test_validate_rule_consistency_no_warnings(self):
        """Test that SAFETY_RULES has no consistency issues."""
        warnings = validate_rule_consistency(SAFETY_RULES)
        assert len(warnings) == 0
    
    def test_validate_rule_consistency_duplicate_names(self):
        """Test detection of duplicate rule names."""
        rules = [
            SafetyRule("test", ["a"], "b", "high", "Test", True),
            SafetyRule("test", ["c"], "d", "high", "Test", True)
        ]
        warnings = validate_rule_consistency(rules)
        
        assert len(warnings) > 0
        assert any("Duplicate" in w for w in warnings)
    
    def test_validate_rule_consistency_no_conditions(self):
        """Test detection of rules with no conditions."""
        rules = [
            SafetyRule("test", [], "conclusion", "high", "Test", True)
        ]
        warnings = validate_rule_consistency(rules)
        
        assert len(warnings) > 0
        assert any("no conditions" in w for w in warnings)
    
    def test_validate_rule_consistency_no_conclusion(self):
        """Test detection of rules with no conclusion."""
        rules = [
            SafetyRule("test", ["a"], "", "high", "Test", True)
        ]
        warnings = validate_rule_consistency(rules)
        
        assert len(warnings) > 0
        assert any("no conclusion" in w for w in warnings)


class TestFactsCoverage:
    """Test facts coverage checking."""
    
    def test_check_facts_coverage_can_fire(self):
        """Test when facts can fire at least one rule."""
        facts = {"chest_pain"}
        can_fire, missing = check_facts_coverage(facts, SAFETY_RULES)
        
        assert can_fire is True
    
    def test_check_facts_coverage_cannot_fire(self):
        """Test when facts cannot fire any rules."""
        facts = {"random_fact_xyz"}
        can_fire, missing = check_facts_coverage(facts, SAFETY_RULES)
        
        assert can_fire is False
        assert len(missing) > 0
    
    def test_check_facts_coverage_partial_conditions(self):
        """Test when facts partially match rule conditions."""
        facts = {"shin_splints"}  # Missing track_terrain
        can_fire, missing = check_facts_coverage(facts, SAFETY_RULES)
        
        # Some rules might fire (uncleared_injury if active_injury fact present)
        # But shin_splints_track won't fire
        assert "track_terrain" in missing or "road_terrain" in missing


class TestInferenceWithRealScenarios:
    """Test inference with realistic safety scenarios."""
    
    def test_inference_beginner_high_intensity(self):
        """Test that beginner + high intensity triggers safety rule."""
        facts = {"beginner_runner", "high_intensity_workout"}
        all_facts, fired_rules = forward_chain(facts)
        
        assert "unsafe_high" in all_facts
        rule_names = [rule.name for rule in fired_rules]
        assert "beginner_high_intensity" in rule_names
    
    def test_inference_consecutive_hard_workouts(self):
        """Test consecutive hard workouts detection."""
        facts = {
            "hard_workout_yesterday",
            "hard_workout_today",
            "no_rest_yesterday"
        }
        all_facts, fired_rules = forward_chain(facts)
        
        assert "overtraining_risk" in all_facts
        rule_names = [rule.name for rule in fired_rules]
        assert "consecutive_hard_workouts" in rule_names
    
    def test_inference_race_week_long_run(self):
        """Test race week long run restriction."""
        facts = {"race_within_7_days", "long_run"}
        all_facts, fired_rules = forward_chain(facts)
        
        assert "unsafe_medium" in all_facts
        rule_names = [rule.name for rule in fired_rules]
        assert "race_week_long_run" in rule_names
    
    def test_inference_no_rest_days_overtraining(self):
        """Test no rest days with heavy training."""
        facts = {"zero_rest_days_this_week", "six_plus_training_days"}
        all_facts, fired_rules = forward_chain(facts)
        
        assert "overtraining_risk" in all_facts
    
    def test_inference_poor_sleep_high_intensity(self):
        """Test poor sleep + high intensity combination."""
        facts = {"poor_sleep", "high_intensity_workout"}
        all_facts, fired_rules = forward_chain(facts)
        
        assert "unsafe_medium" in all_facts
        rule_names = [rule.name for rule in fired_rules]
        assert "poor_sleep_high_intensity" in rule_names
    
    def test_inference_multiple_safety_issues(self):
        """Test multiple safety issues detected simultaneously."""
        facts = {
            "chest_pain",
            "shin_splints",
            "track_terrain",
            "excessive_distance"
        }
        all_facts, fired_rules = forward_chain(facts)
        
        # Should detect multiple issues
        assert len(fired_rules) >= 3
        assert "unsafe_critical" in all_facts  # From chest pain
        
        # Verify safety determination prioritizes critical
        is_safe, severity = determine_safety(all_facts)
        assert is_safe is False
        assert severity == "critical"