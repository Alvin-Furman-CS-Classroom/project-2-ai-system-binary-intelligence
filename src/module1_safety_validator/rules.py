"""
Safety rules for workout validation using propositional logic.

This module defines the knowledge base of 20 safety rules organized into
five categories: absolute safety, injury-terrain contraindications, training
load, recovery/fatigue, and environment/preparation.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class SafetyRule:
    """
    Represents a propositional logic safety rule.
    
    A rule has the form: IF all conditions are true THEN conclusion is true.
    
    Attributes:
        name: Unique identifier for the rule
        conditions: List of propositional facts that must all be true (AND logic)
        conclusion: Propositional fact to derive if conditions are met
        severity: Risk level ("critical", "high", "medium")
        explanation: Human-readable explanation of why this rule exists
        can_suggest_alternative: Whether a safe alternative can be suggested
    """
    name: str
    conditions: List[str]
    conclusion: str
    severity: str
    explanation: str
    can_suggest_alternative: bool


# ============================================================================
# CATEGORY 1: ABSOLUTE SAFETY RULES (4 rules)
# These always block training with no alternatives
# ============================================================================

ABSOLUTE_SAFETY_RULES = [
    SafetyRule(
        name="chest_pain_block",
        conditions=["chest_pain"],
        conclusion="unsafe_critical",
        severity="critical",
        explanation="Chest pain requires immediate medical attention",
        can_suggest_alternative=False
    ),
    SafetyRule(
        name="dizziness_block",
        conditions=["dizziness"],
        conclusion="unsafe_critical",
        severity="critical",
        explanation="Dizziness during exercise can indicate serious medical issues",
        can_suggest_alternative=False
    ),
    SafetyRule(
        name="severe_pain_block",
        conditions=["severe_pain"],
        conclusion="unsafe_critical",
        severity="critical",
        explanation="Severe pain indicates potential injury requiring rest",
        can_suggest_alternative=False
    ),
    SafetyRule(
        name="uncleared_injury_block",
        conditions=["active_injury", "not_cleared_by_doctor"],
        conclusion="unsafe_critical",
        severity="critical",
        explanation="Active injuries require medical clearance before training",
        can_suggest_alternative=False
    ),
]


# ============================================================================
# CATEGORY 2: INJURY-TERRAIN CONTRAINDICATIONS (5 rules)
# These suggest terrain alternatives when violated
# ============================================================================

INJURY_TERRAIN_RULES = [
    SafetyRule(
        name="shin_splints_track",
        conditions=["shin_splints", "track_terrain"],
        conclusion="high_injury_risk",
        severity="high",
        explanation="Track running aggravates shin splints due to repetitive turns",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="shin_splints_road",
        conditions=["shin_splints", "road_terrain"],
        conclusion="medium_injury_risk",
        severity="medium",
        explanation="Road running can aggravate shin splints on hard surfaces",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="knee_injury_trail",
        conditions=["knee_injury", "trail_terrain"],
        conclusion="high_injury_risk",
        severity="high",
        explanation="Trail running stresses knees with uneven surfaces and elevation changes",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="knee_injury_road",
        conditions=["knee_injury", "road_terrain"],
        conclusion="medium_injury_risk",
        severity="medium",
        explanation="Road running can stress knees on hard surfaces",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="plantar_fasciitis_hard_surface",
        conditions=["plantar_fasciitis", "hard_surface"],
        conclusion="high_injury_risk",
        severity="high",
        explanation="Hard surfaces aggravate plantar fasciitis",
        can_suggest_alternative=True
    ),
]


# ============================================================================
# CATEGORY 3: TRAINING LOAD & PROGRESSION (5 rules)
# These enforce safe training progression
# ============================================================================

TRAINING_LOAD_RULES = [
    SafetyRule(
        name="excessive_distance",
        conditions=["excessive_distance"],
        conclusion="unsafe_high",
        severity="high",
        explanation="Long run distance exceeds safe limit (1.5x weekly mileage)",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="excessive_progression",
        conditions=["excessive_progression"],
        conclusion="unsafe_medium",
        severity="medium",
        explanation="Weekly mileage increase exceeds 10% rule",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="beginner_high_intensity",
        conditions=["beginner_runner", "high_intensity_workout"],
        conclusion="unsafe_high",
        severity="high",
        explanation="Beginners should not perform high-intensity workouts without proper base",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="consecutive_hard_workouts",
        conditions=["hard_workout_yesterday", "hard_workout_today", "no_rest_yesterday"],
        conclusion="overtraining_risk",
        severity="medium",
        explanation="Back-to-back hard workouts without rest increases injury risk",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="race_week_long_run",
        conditions=["race_within_7_days", "long_run"],
        conclusion="unsafe_medium",
        severity="medium",
        explanation="Long runs within 7 days of race prevent proper taper",
        can_suggest_alternative=True
    ),
]


# ============================================================================
# CATEGORY 4: RECOVERY & FATIGUE (3 rules)
# These ensure adequate recovery between workouts
# ============================================================================

RECOVERY_FATIGUE_RULES = [
    SafetyRule(
        name="insufficient_recovery_high_intensity",
        conditions=["not_fully_recovered", "high_intensity_workout"],
        conclusion="unsafe_medium",
        severity="medium",
        explanation="High-intensity workouts require full recovery from previous training",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="poor_sleep_high_intensity",
        conditions=["poor_sleep", "high_intensity_workout"],
        conclusion="unsafe_medium",
        severity="medium",
        explanation="Poor sleep impairs performance and increases injury risk during intense workouts",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="no_rest_days",
        conditions=["zero_rest_days_this_week", "six_plus_training_days"],
        conclusion="overtraining_risk",
        severity="medium",
        explanation="Training 6+ days without rest increases overtraining and injury risk",
        can_suggest_alternative=True
    ),
]


# ============================================================================
# CATEGORY 5: ENVIRONMENT & PREPARATION (3 rules)
# These ensure safe training conditions
# ============================================================================

ENVIRONMENT_PREPARATION_RULES = [
    SafetyRule(
        name="extreme_weather",
        conditions=["extreme_weather"],
        conclusion="unsafe_medium",
        severity="medium",
        explanation="Extreme heat or cold increases risk of heat illness or hypothermia",
        can_suggest_alternative=False
    ),
    SafetyRule(
        name="not_hydrated",
        conditions=["not_hydrated"],
        conclusion="unsafe_medium",
        severity="medium",
        explanation="Dehydration impairs performance and increases health risks",
        can_suggest_alternative=False
    ),
    SafetyRule(
        name="improper_footwear",
        conditions=["no_proper_footwear"],
        conclusion="unsafe_medium",
        severity="medium",
        explanation="Improper footwear significantly increases injury risk",
        can_suggest_alternative=False
    ),
]


# ============================================================================
# COMBINED RULE SET
# All 20 rules in a single list for the inference engine
# ============================================================================

SAFETY_RULES: List[SafetyRule] = (
    ABSOLUTE_SAFETY_RULES +
    INJURY_TERRAIN_RULES +
    TRAINING_LOAD_RULES +
    RECOVERY_FATIGUE_RULES +
    ENVIRONMENT_PREPARATION_RULES
)


def get_rules_by_category(category: str) -> List[SafetyRule]:
    """
    Get all rules belonging to a specific category.
    
    Args:
        category: Category name ("absolute", "injury", "training", "recovery", "environment")
        
    Returns:
        List of SafetyRule objects in that category
        
    Example:
        >>> injury_rules = get_rules_by_category("injury")
        >>> len(injury_rules)
        5
    """
    category_map = {
        "absolute": ABSOLUTE_SAFETY_RULES,
        "injury": INJURY_TERRAIN_RULES,
        "training": TRAINING_LOAD_RULES,
        "recovery": RECOVERY_FATIGUE_RULES,
        "environment": ENVIRONMENT_PREPARATION_RULES,
    }
    return category_map.get(category, [])


def get_rule_by_name(rule_name: str) -> SafetyRule:
    """
    Get a specific rule by its name.
    
    Args:
        rule_name: Name of the rule to retrieve
        
    Returns:
        SafetyRule object with matching name
        
    Raises:
        ValueError: If rule name not found
        
    Example:
        >>> rule = get_rule_by_name("chest_pain_block")
        >>> rule.severity
        'critical'
    """
    for rule in SAFETY_RULES:
        if rule.name == rule_name:
            return rule
    raise ValueError(f"Rule '{rule_name}' not found in knowledge base")