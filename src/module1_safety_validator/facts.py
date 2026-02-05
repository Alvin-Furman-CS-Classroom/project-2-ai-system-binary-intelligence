"""
Fact extraction for workout safety validation.

This module converts structured input data (runner profile and proposed workout)
into propositional facts that can be used by the inference engine.
"""

from typing import Set, Dict, Any, Optional
from datetime import datetime, timedelta


def extract_facts(runner_profile: Dict[str, Any]) -> Set[str]:
    """
    Extract all propositional facts from runner profile and proposed workout.
    
    Converts structured input into a set of atomic propositions that the
    inference engine can reason about using the safety rules.
    
    Args:
        runner_profile: Dictionary containing runner data and proposed workout
        
    Returns:
        Set of propositional fact strings
        
    Example:
        >>> profile = {
        ...     "injuries": ["shin splints"],
        ...     "proposed_workout": {"type": "long run", "terrain": "track"}
        ... }
        >>> facts = extract_facts(profile)
        >>> "shin_splints" in facts
        True
        >>> "track_terrain" in facts
        True
    """
    facts = set()
    
    # Extract health and symptom facts
    facts.update(_extract_health_facts(runner_profile))
    
    # Extract injury facts
    facts.update(_extract_injury_facts(runner_profile))
    
    # Extract recovery facts
    facts.update(_extract_recovery_facts(runner_profile))
    
    # Extract training context facts
    facts.update(_extract_training_facts(runner_profile))
    
    # Extract environment and preparation facts
    facts.update(_extract_environment_facts(runner_profile))
    
    # Extract proposed workout facts
    facts.update(_extract_workout_facts(runner_profile))
    
    # Compute derived facts (facts that depend on calculations)
    facts.update(_compute_derived_facts(facts, runner_profile))
    
    return facts


def _extract_health_facts(profile: Dict[str, Any]) -> Set[str]:
    """
    Extract health and symptom-related facts.
    
    Args:
        profile: Runner profile dictionary
        
    Returns:
        Set of health-related propositional facts
    """
    facts = set()
    
    # Symptoms
    symptoms = profile.get("symptoms", [])
    if "chest_pain" in symptoms or "chest pain" in symptoms:
        facts.add("chest_pain")
    if "dizziness" in symptoms:
        facts.add("dizziness")
    
    # Pain level
    pain_level = profile.get("pain_level", "none")
    if pain_level == "severe":
        facts.add("severe_pain")
    
    return facts


def _extract_injury_facts(profile: Dict[str, Any]) -> Set[str]:
    """
    Extract injury-related facts.
    
    Args:
        profile: Runner profile dictionary
        
    Returns:
        Set of injury-related propositional facts
    """
    facts = set()
    
    injuries = profile.get("injuries", [])
    
    # Normalize injury names to propositional facts
    for injury in injuries:
        injury_lower = injury.lower()
        
        if "shin splint" in injury_lower:
            facts.add("shin_splints")
            facts.add("active_injury")
        elif "knee" in injury_lower:
            facts.add("knee_injury")
            facts.add("active_injury")
        elif "plantar fasciitis" in injury_lower or "plantar" in injury_lower:
            facts.add("plantar_fasciitis")
            facts.add("active_injury")
    
    # Check medical clearance
    if injuries and not profile.get("cleared_by_doctor", False):
        facts.add("not_cleared_by_doctor")
    
    return facts


def _extract_recovery_facts(profile: Dict[str, Any]) -> Set[str]:
    """
    Extract recovery and fatigue-related facts.
    
    Args:
        profile: Runner profile dictionary
        
    Returns:
        Set of recovery-related propositional facts
    """
    facts = set()
    
    # Recovery status
    if not profile.get("fully_recovered", True):
        facts.add("not_fully_recovered")
    
    # Sleep quality
    sleep_quality = profile.get("sleep_quality", "good")
    if sleep_quality == "poor":
        facts.add("poor_sleep")
    
    # Rest days
    rest_days = profile.get("rest_days_this_week", 0)
    if rest_days == 0:
        facts.add("zero_rest_days_this_week")
    
    # Training days
    days_trained = profile.get("days_trained_this_week", 0)
    if days_trained >= 6:
        facts.add("six_plus_training_days")
    
    # Previous workout
    if profile.get("hard_workout_yesterday", False):
        facts.add("hard_workout_yesterday")
    
    if not profile.get("rest_day_yesterday", True):
        facts.add("no_rest_yesterday")
    
    return facts


def _extract_training_facts(profile: Dict[str, Any]) -> Set[str]:
    """
    Extract training context facts.
    
    Args:
        profile: Runner profile dictionary
        
    Returns:
        Set of training-related propositional facts
    """
    facts = set()
    
    # Experience level
    experience = profile.get("experience_level", "beginner")
    if experience == "beginner":
        facts.add("beginner_runner")
    elif experience == "intermediate":
        facts.add("intermediate_runner")
    elif experience == "advanced":
        facts.add("advanced_runner")
    
    # Race proximity
    race_date_str = profile.get("race_date")
    if race_date_str:
        try:
            race_date = datetime.fromisoformat(race_date_str.replace("Z", "+00:00"))
            today = datetime.now(race_date.tzinfo) if race_date.tzinfo else datetime.now()
            days_until_race = (race_date - today).days
            
            if 0 <= days_until_race <= 7:
                facts.add("race_within_7_days")
        except (ValueError, AttributeError):
            # Invalid date format, skip
            pass
    
    return facts


def _extract_environment_facts(profile: Dict[str, Any]) -> Set[str]:
    """
    Extract environment and preparation facts.
    
    Args:
        profile: Runner profile dictionary
        
    Returns:
        Set of environment-related propositional facts
    """
    facts = set()
    
    # Weather conditions
    weather = profile.get("weather", "normal")
    if weather in ["extreme_heat", "extreme_cold"]:
        facts.add("extreme_weather")
    
    # Hydration
    if not profile.get("hydrated", True):
        facts.add("not_hydrated")
    
    # Footwear
    if not profile.get("proper_footwear", True):
        facts.add("no_proper_footwear")
    
    return facts


def _extract_workout_facts(profile: Dict[str, Any]) -> Set[str]:
    """
    Extract proposed workout facts.
    
    Args:
        profile: Runner profile dictionary (contains proposed_workout)
        
    Returns:
        Set of workout-related propositional facts
    """
    facts = set()
    
    workout = profile.get("proposed_workout", {})
    
    # Workout type
    workout_type = workout.get("type", "").lower()
    if "long run" in workout_type or "long" in workout_type:
        facts.add("long_run")
    elif "tempo" in workout_type:
        facts.add("tempo_run")
        facts.add("high_intensity_workout")
        facts.add("hard_workout_today")
    elif "interval" in workout_type:
        facts.add("intervals")
        facts.add("high_intensity_workout")
        facts.add("hard_workout_today")
    elif "easy" in workout_type:
        facts.add("easy_run")
    
    # Terrain
    terrain = workout.get("terrain", "").lower()
    if "track" in terrain:
        facts.add("track_terrain")
        facts.add("hard_surface")
    elif "road" in terrain:
        facts.add("road_terrain")
        facts.add("hard_surface")
    elif "trail" in terrain:
        facts.add("trail_terrain")
    elif "treadmill" in terrain:
        facts.add("treadmill_terrain")
    
    return facts


def _compute_derived_facts(facts: Set[str], profile: Dict[str, Any]) -> Set[str]:
    """
    Compute facts that require numerical calculations or complex logic.
    
    Args:
        facts: Current set of extracted facts
        profile: Runner profile dictionary
        
    Returns:
        Set of derived propositional facts
    """
    derived = set()
    
    workout = profile.get("proposed_workout", {})
    distance = workout.get("distance", 0)
    weekly_mileage = profile.get("weekly_mileage", 0)
    
    # Excessive distance check (long run > 1.5x weekly mileage)
    if "long_run" in facts and weekly_mileage > 0:
        safe_limit = weekly_mileage * 1.5
        if distance > safe_limit:
            derived.add("excessive_distance")
    
    # Excessive progression check (10% rule)
    # Note: This would require knowing next week's planned mileage
    # For now, we'll add it if the proposed workout would push weekly mileage up significantly
    # This is a simplified version - a more complete implementation would track planned weekly totals
    proposed_weekly = profile.get("proposed_weekly_mileage")
    if proposed_weekly and weekly_mileage > 0:
        increase_ratio = proposed_weekly / weekly_mileage
        if increase_ratio > 1.1:
            derived.add("excessive_progression")
    
    return derived


def profile_to_facts(runner_profile: Dict[str, Any]) -> Set[str]:
    """
    Alias for extract_facts for backward compatibility.
    
    Args:
        runner_profile: Runner profile dictionary
        
    Returns:
        Set of propositional facts
    """
    return extract_facts(runner_profile)


def get_fact_explanation(fact: str) -> str:
    """
    Get a human-readable explanation of what a propositional fact means.
    
    Args:
        fact: Propositional fact string
        
    Returns:
        Human-readable explanation
        
    Example:
        >>> get_fact_explanation("shin_splints")
        'Runner has shin splints injury'
    """
    explanations = {
        # Health
        "chest_pain": "Runner experiencing chest pain",
        "dizziness": "Runner experiencing dizziness",
        "severe_pain": "Runner experiencing severe pain",
        
        # Injuries
        "shin_splints": "Runner has shin splints injury",
        "knee_injury": "Runner has knee injury",
        "plantar_fasciitis": "Runner has plantar fasciitis",
        "active_injury": "Runner has an active injury",
        "not_cleared_by_doctor": "Injury not cleared by medical professional",
        
        # Recovery
        "not_fully_recovered": "Runner not fully recovered from previous workout",
        "poor_sleep": "Runner had poor sleep quality",
        "zero_rest_days_this_week": "No rest days taken this week",
        "six_plus_training_days": "Trained 6 or more days this week",
        "hard_workout_yesterday": "Completed hard workout yesterday",
        "no_rest_yesterday": "No rest day yesterday",
        
        # Training
        "beginner_runner": "Runner is a beginner",
        "intermediate_runner": "Runner is intermediate level",
        "advanced_runner": "Runner is advanced level",
        "race_within_7_days": "Race scheduled within 7 days",
        
        # Environment
        "extreme_weather": "Extreme heat or cold conditions",
        "not_hydrated": "Runner is not properly hydrated",
        "no_proper_footwear": "Runner does not have proper footwear",
        
        # Workout
        "long_run": "Proposed workout is a long run",
        "tempo_run": "Proposed workout is a tempo run",
        "intervals": "Proposed workout is intervals",
        "easy_run": "Proposed workout is an easy run",
        "high_intensity_workout": "Proposed workout is high intensity",
        "hard_workout_today": "Today's workout is hard/intense",
        
        # Terrain
        "track_terrain": "Proposed terrain is track",
        "road_terrain": "Proposed terrain is road",
        "trail_terrain": "Proposed terrain is trail",
        "treadmill_terrain": "Proposed terrain is treadmill",
        "hard_surface": "Proposed terrain is a hard surface",
        
        # Derived
        "excessive_distance": "Distance exceeds safe limit for weekly mileage",
        "excessive_progression": "Weekly mileage increase exceeds 10% rule",
    }
    
    return explanations.get(fact, f"Unknown fact: {fact}")