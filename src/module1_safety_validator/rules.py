"""
Safety rules for workout validation using propositional logic.

This module defines the knowledge base of safety rules organized into
five categories: absolute safety, injury-terrain contraindications, training
load, recovery/fatigue, and environment/preparation.
See README.md References section for sources.

RULE STRUCTURE:
===============
Each rule follows the form: IF (conditions) THEN (conclusion)

- conditions: List of facts that must ALL be true (AND logic)
- conclusion: Fact derived when conditions are met
- severity: "critical", "high", or "medium"
- can_suggest_alternative: Whether a safe alternative workout can be suggested

EXPERIENCE LEVEL DEFINITIONS:
==============================
See experience_levels.py for detailed criteria.

Beginner (0-1 year):
  - Weekly mileage: 0-30 miles
  - Long run max: 13 miles
  - Cannot do high-intensity workouts

Intermediate (1-3 years):
  - Weekly mileage: 20-50 miles
  - Long run max: 18 miles
  - Can do tempo runs and moderate intervals

Advanced (3+ years):
  - Weekly mileage: 40-200 miles
  - Long run max: 26 miles
  - Can handle all workout types
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


# Severity levels (use constants to avoid typos and magic strings)
SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_NONE = "none"


# ============================================================================
# CATEGORY 1: ABSOLUTE SAFETY RULES (4 rules)
# These always block training with no alternatives
# ============================================================================

ABSOLUTE_SAFETY_RULES = [
    SafetyRule(
        name="chest_pain_block",
        conditions=["chest_pain"],
        conclusion="unsafe_critical",
        severity=SEVERITY_CRITICAL,
        explanation="Chest pain requires immediate medical attention",
        can_suggest_alternative=False
    ),
    SafetyRule(
        name="dizziness_block",
        conditions=["dizziness"],
        conclusion="unsafe_critical",
        severity=SEVERITY_CRITICAL,
        explanation="Dizziness during exercise can indicate serious medical issues",
        can_suggest_alternative=False
    ),
    SafetyRule(
        name="severe_pain_block",
        conditions=["severe_pain"],
        conclusion="unsafe_critical",
        severity=SEVERITY_CRITICAL,
        explanation="Severe pain indicates potential injury requiring rest",
        can_suggest_alternative=False
    ),
    SafetyRule(
        name="uncleared_injury_block",
        conditions=["active_injury", "not_cleared_by_doctor"],
        conclusion="unsafe_critical",
        severity=SEVERITY_CRITICAL,
        explanation="Active injuries require medical clearance before training",
        can_suggest_alternative=False
    ),
]


# ============================================================================
# CATEGORY 2: INJURY-TERRAIN CONTRAINDICATIONS (17 rules)
# These suggest terrain alternatives when violated
# Based on: VCU Health, HSS, Therapeutic Associates
# ============================================================================

INJURY_TERRAIN_RULES = [
    # Shin splints rules
    SafetyRule(
        name="shin_splints_track",
        conditions=["shin_splints", "track_terrain"],
        conclusion="high_injury_risk",
        severity=SEVERITY_HIGH,
        explanation="Track running aggravates shin splints due to repetitive turns",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="shin_splints_road",
        conditions=["shin_splints", "road_terrain"],
        conclusion="medium_injury_risk",
        severity=SEVERITY_MEDIUM,
        explanation="Road running can aggravate shin splints on hard surfaces",
        can_suggest_alternative=True
    ),
    
    # Knee injury rules  
    SafetyRule(
        name="knee_injury_trail",
        conditions=["knee_injury", "trail_terrain"],
        conclusion="high_injury_risk",
        severity=SEVERITY_HIGH,
        explanation="Trail running stresses knees with uneven surfaces and elevation changes",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="knee_injury_road",
        conditions=["knee_injury", "road_terrain"],
        conclusion="medium_injury_risk",
        severity=SEVERITY_MEDIUM,
        explanation="Road running can stress knees on hard surfaces",
        can_suggest_alternative=True
    ),
    
    # Plantar fasciitis rules
    SafetyRule(
        name="plantar_fasciitis_hard_surface",
        conditions=["plantar_fasciitis", "hard_surface"],
        conclusion="high_injury_risk",
        severity=SEVERITY_HIGH,
        explanation="Hard surfaces aggravate plantar fasciitis",
        can_suggest_alternative=True
    ),
    
    # IT band syndrome rules
    SafetyRule(
        name="it_band_trail",
        conditions=["it_band_syndrome", "trail_terrain"],
        conclusion="high_injury_risk",
        severity=SEVERITY_HIGH,
        explanation="Trail running with hills and uneven surfaces can aggravate IT band syndrome",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="it_band_track",
        conditions=["it_band_syndrome", "track_terrain"],
        conclusion="high_injury_risk",
        severity=SEVERITY_HIGH,
        explanation="Track running with repetitive turns in one direction aggravates IT band syndrome",
        can_suggest_alternative=True
    ),
    
    # Achilles tendonitis rules
    SafetyRule(
        name="achilles_trail",
        conditions=["achilles_tendonitis", "trail_terrain"],
        conclusion="high_injury_risk",
        severity=SEVERITY_HIGH,
        explanation="Trail running with elevation changes stresses Achilles tendon",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="achilles_hard_surface",
        conditions=["achilles_tendonitis", "hard_surface"],
        conclusion="medium_injury_risk",
        severity=SEVERITY_MEDIUM,
        explanation="Hard surfaces can aggravate Achilles tendonitis",
        can_suggest_alternative=True
    ),
    
    # Stress fracture rule (should rest, not just change terrain)
    SafetyRule(
        name="stress_fracture_running",
        conditions=["stress_fracture"],
        conclusion="unsafe_critical",
        severity=SEVERITY_CRITICAL,
        explanation="Stress fractures require complete rest from running to heal properly",
        can_suggest_alternative=False
    ),
    
    # Hip injury rule
    SafetyRule(
        name="hip_injury_trail",
        conditions=["hip_injury", "trail_terrain"],
        conclusion="high_injury_risk",
        severity=SEVERITY_HIGH,
        explanation="Trail running with uneven surfaces stresses hip stabilizers",
        can_suggest_alternative=True
    ),
    
    # Hamstring injury rule
    SafetyRule(
        name="hamstring_trail",
        conditions=["hamstring_injury", "trail_terrain"],
        conclusion="high_injury_risk",
        severity=SEVERITY_HIGH,
        explanation="Trail running with uneven surfaces and elevation changes stresses hamstrings",
        can_suggest_alternative=True
    ),
    
    # Calf injury rules
    SafetyRule(
        name="calf_trail",
        conditions=["calf_injury", "trail_terrain"],
        conclusion="high_injury_risk",
        severity=SEVERITY_HIGH,
        explanation="Trail running with elevation changes and uneven surfaces stresses calves",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="calf_hard_surface",
        conditions=["calf_injury", "hard_surface"],
        conclusion="medium_injury_risk",
        severity=SEVERITY_MEDIUM,
        explanation="Hard surfaces can aggravate calf injuries",
        can_suggest_alternative=True
    ),
    
    # Ankle injury rule
    SafetyRule(
        name="ankle_trail",
        conditions=["ankle_injury", "trail_terrain"],
        conclusion="high_injury_risk",
        severity=SEVERITY_HIGH,
        explanation="Trail running with uneven surfaces increases ankle instability and reinjury risk",
        can_suggest_alternative=True
    ),
    
    # Back injury rules
    SafetyRule(
        name="back_injury_trail",
        conditions=["back_injury", "trail_terrain"],
        conclusion="high_injury_risk",
        severity=SEVERITY_HIGH,
        explanation="Trail running with uneven surfaces and impact stresses lower back",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="back_injury_hard_surface",
        conditions=["back_injury", "hard_surface"],
        conclusion="medium_injury_risk",
        severity=SEVERITY_MEDIUM,
        explanation="Hard surfaces increase impact forces on back",
        can_suggest_alternative=True
    ),
]


# ============================================================================
# CATEGORY 3: TRAINING LOAD & PROGRESSION (4 rules)
# These enforce safe training progression
# ============================================================================

TRAINING_LOAD_RULES = [
    SafetyRule(
        name="excessive_distance",
        conditions=["excessive_distance"],
        conclusion="unsafe_high",
        severity=SEVERITY_HIGH,
        explanation="Long run distance exceeds safe limit (1.5x weekly mileage)",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="beginner_high_intensity",
        conditions=["beginner_runner", "high_intensity_workout"],
        conclusion="unsafe_high",
        severity=SEVERITY_HIGH,
        explanation="Beginners should not perform high-intensity workouts without proper base",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="consecutive_hard_workouts",
        conditions=["hard_workout_yesterday", "hard_workout_today", "no_rest_yesterday"],
        conclusion="overtraining_risk",
        severity=SEVERITY_MEDIUM,
        explanation="Back-to-back hard workouts without rest increases injury risk",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="race_week_long_run",
        conditions=["race_within_7_days", "long_run"],
        conclusion="unsafe_medium",
        severity=SEVERITY_MEDIUM,
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
        severity=SEVERITY_MEDIUM,
        explanation="High-intensity workouts require full recovery from previous training",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="poor_sleep_high_intensity",
        conditions=["poor_sleep", "high_intensity_workout"],
        conclusion="unsafe_medium",
        severity=SEVERITY_MEDIUM,
        explanation="Poor sleep impairs performance and increases injury risk during intense workouts",
        can_suggest_alternative=True
    ),
    SafetyRule(
        name="no_rest_days",
        conditions=["zero_rest_days_this_week", "six_plus_training_days"],
        conclusion="overtraining_risk",
        severity=SEVERITY_MEDIUM,
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
        severity=SEVERITY_MEDIUM,
        explanation="Extreme heat or cold increases risk of heat illness or hypothermia",
        can_suggest_alternative=False
    ),
    SafetyRule(
        name="not_hydrated",
        conditions=["not_hydrated"],
        conclusion="unsafe_medium",
        severity=SEVERITY_MEDIUM,
        explanation="Dehydration impairs performance and increases health risks",
        can_suggest_alternative=False
    ),
    SafetyRule(
        name="improper_footwear",
        conditions=["no_proper_footwear"],
        conclusion="unsafe_medium",
        severity=SEVERITY_MEDIUM,
        explanation="Improper footwear significantly increases injury risk",
        can_suggest_alternative=False
    ),
]


# ============================================================================
# COMBINED RULE SET
# All 31 rules in a single list for the inference engine
# Categories: 4 absolute + 17 injury-terrain + 4 training + 3 recovery + 3 environment
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
        17
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