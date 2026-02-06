"""
Main workout safety validator module.

This module provides the primary interface for validating workout safety
using propositional logic, forward chaining inference, and alternative
workout generation.
"""

from typing import Dict, Any, List
from .facts import extract_facts
from .rules import SAFETY_RULES
from .inference import forward_chain, determine_safety
from .alternatives import generate_alternative, can_suggest_alternative, suggest_rest_day_message


def validate_workout(
    runner_profile: Dict[str, Any],
    proposed_workout: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Validate workout safety using propositional logic and forward chaining.
    
    This is the main entry point for Module 1. It takes a runner profile
    and proposed workout, extracts propositional facts, applies safety rules
    through forward chaining, and returns a validation result with reasoning
    and alternative suggestions if applicable.
    
    Args:
        runner_profile: Dictionary containing runner health, training, and environment data:
            - symptoms: List[str] - current symptoms (e.g., ["chest_pain"])
            - injuries: List[str] - current injuries (e.g., ["shin splints"])
            - pain_level: str - "none", "mild", "moderate", "severe"
            - cleared_by_doctor: bool - medical clearance for injuries
            - fully_recovered: bool - recovery status from previous workout
            - sleep_quality: str - "poor", "fair", "good"
            - rest_days_this_week: int - rest days taken this week
            - days_trained_this_week: int - training days this week
            - hard_workout_yesterday: bool - whether yesterday was hard workout
            - weekly_mileage: float - current weekly mileage
            - experience_level: str - "beginner", "intermediate", "advanced"
            - race_date: str - ISO format date string (optional)
            - weather: str - "normal", "extreme_heat", "extreme_cold"
            - hydrated: bool - hydration status
            - proper_footwear: bool - appropriate shoes
            - available_terrain: List[str] - terrain options
            
        proposed_workout: Dictionary containing workout details (can also be in runner_profile):
            - type: str - "easy run", "long run", "tempo", "intervals"
            - distance: float - distance in miles
            - terrain: str - "track", "road", "trail", "treadmill"
    
    Returns:
        Dictionary with validation result:
            - safe: bool - whether workout is safe to perform
            - reason: str - explanation of safety determination
            - alternative: Optional[Dict] - safe alternative workout if available
            - recommendation: str - "rest" if no alternative exists (only present when alternative is None)
        
    Example:
        >>> profile = {
        ...     "injuries": ["shin splints"],
        ...     "weekly_mileage": 15,
        ...     "rest_days_this_week": 1,
        ...     "available_terrain": ["treadmill", "track"],
        ...     "experience_level": "beginner",
        ...     "hydrated": True,
        ...     "proper_footwear": True,
        ...     "weather": "normal"
        ... }
        >>> workout = {"type": "long run", "distance": 12, "terrain": "track"}
        >>> result = validate_workout(profile, workout)
        >>> result["safe"]
        False
        >>> result["alternative"]["terrain"]
        'treadmill'
    """
    # Handle case where proposed_workout is passed separately or embedded in profile
    if proposed_workout is not None:
        full_profile = {**runner_profile, "proposed_workout": proposed_workout}
    else:
        full_profile = runner_profile
        proposed_workout = runner_profile.get("proposed_workout", {})
    
    # Validate inputs first (CRITICAL: prevents garbage in/garbage out)
    from .input_validation import validate_runner_profile
    
    input_error = validate_runner_profile(full_profile)
    if input_error:
        return {
            "safe": False,
            "reason": f"Invalid input: {input_error}",
            "alternative": None,
            "recommendation": None
        }
    
    # Validate input has required fields
    if not proposed_workout:
        return {
            "safe": False,
            "reason": "No proposed workout provided",
            "alternative": None,
            "recommendation": "rest"
        }
    
    # Extract propositional facts from input
    facts = extract_facts(full_profile)
    
    # Apply forward chaining inference
    all_facts, fired_rules = forward_chain(facts, SAFETY_RULES)
    
    # Determine if workout is safe
    is_safe, severity = determine_safety(all_facts)
    
    # If safe, return success
    if is_safe:
        return {
            "safe": True,
            "reason": "Workout meets all safety criteria",
            "alternative": None
        }
    
    # Workout is unsafe - generate explanation
    reason = _generate_reason(fired_rules)
    
    # Try to generate alternative workout
    alternative = None
    if can_suggest_alternative(fired_rules):
        alternative = generate_alternative(runner_profile, proposed_workout, fired_rules)
    
    # Build response
    result = {
        "safe": False,
        "reason": reason,
        "alternative": alternative
    }
    
    # Add recommendation if no alternative exists
    if alternative is None:
        result["recommendation"] = "rest"
    
    return result


def _generate_reason(fired_rules: List) -> str:
    """
    Generate human-readable explanation from fired rules.
    
    Combines explanations from all fired rules into a coherent message.
    
    Args:
        fired_rules: List of SafetyRule objects that fired
        
    Returns:
        Explanation string
    """
    if not fired_rules:
        return "Unknown safety concern"
    
    # Get unique explanations (in case multiple rules have same explanation)
    explanations = []
    seen = set()
    
    for rule in fired_rules:
        if rule.explanation not in seen:
            explanations.append(rule.explanation)
            seen.add(rule.explanation)
    
    # Join with semicolons
    return "; ".join(explanations)


def validate_workout_detailed(
    runner_profile: Dict[str, Any],
    proposed_workout: Dict[str, Any] = None,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Validate workout with additional debug information.
    
    Extended version that includes internal details useful for debugging
    and understanding the inference process.
    
    Args:
        runner_profile: Runner health, training, and environment data
        proposed_workout: Workout to validate
        debug: If True, include detailed inference information
        
    Returns:
        Validation result with optional debug fields:
            - safe: bool
            - reason: str
            - alternative: Optional[Dict]
            - recommendation: str (if applicable)
            - _debug_info: Dict (only if debug=True) containing:
                - initial_facts: Set[str]
                - derived_facts: Set[str]
                - fired_rules: List[str]
                - severity: str
                - inference_chain: str
    """
    # Handle case where proposed_workout is passed separately or embedded in profile
    if proposed_workout is not None:
        full_profile = {**runner_profile, "proposed_workout": proposed_workout}
    else:
        full_profile = runner_profile
        proposed_workout = runner_profile.get("proposed_workout", {})
    
    # Extract facts
    initial_facts = extract_facts(full_profile)
    
    # Apply inference
    all_facts, fired_rules = forward_chain(initial_facts, SAFETY_RULES)
    
    # Determine safety
    is_safe, severity = determine_safety(all_facts)
    
    # Get basic result
    if is_safe:
        result = {
            "safe": True,
            "reason": "Workout meets all safety criteria",
            "alternative": None
        }
    else:
        reason = _generate_reason(fired_rules)
        alternative = None
        if can_suggest_alternative(fired_rules):
            alternative = generate_alternative(runner_profile, proposed_workout, fired_rules)
        
        result = {
            "safe": False,
            "reason": reason,
            "alternative": alternative
        }
        
        if alternative is None:
            result["recommendation"] = "rest"
    
    # Add debug info if requested
    if debug:
        from .inference import explain_inference
        
        result["_debug_info"] = {
            "initial_facts": sorted(list(initial_facts)),
            "derived_facts": sorted(list(all_facts)),
            "fired_rules": [rule.name for rule in fired_rules],
            "severity": severity,
            "inference_chain": explain_inference(initial_facts, all_facts, fired_rules)
        }
    
    return result


def quick_validate(
    injuries: List[str],
    workout_type: str,
    distance: float,
    terrain: str,
    weekly_mileage: float
) -> bool:
    """
    Quick validation with minimal input for simple use cases.
    
    Provides a simplified interface when you only have basic information
    and just need a yes/no answer without alternatives.
    
    Args:
        injuries: List of current injuries
        workout_type: Type of workout
        distance: Distance in miles
        terrain: Terrain type
        weekly_mileage: Current weekly mileage
        
    Returns:
        True if safe, False if unsafe
        
    Example:
        >>> quick_validate(["shin splints"], "long run", 12, "track", 15)
        False
        >>> quick_validate([], "easy run", 5, "road", 20)
        True
    """
    profile = {
        "injuries": injuries,
        "symptoms": [],
        "weekly_mileage": weekly_mileage,
        "rest_days_this_week": 1,
        "days_trained_this_week": 3,
        "experience_level": "intermediate",
        "hydrated": True,
        "proper_footwear": True,
        "weather": "normal",
        "fully_recovered": True,
        "sleep_quality": "good",
        "available_terrain": [terrain]
    }
    
    workout = {
        "type": workout_type,
        "distance": distance,
        "terrain": terrain
    }
    
    result = validate_workout(profile, workout)
    return result["safe"]


def batch_validate(
    runner_profile: Dict[str, Any],
    proposed_workouts: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Validate multiple workouts at once.
    
    Useful for validating an entire week's training plan in one call.
    
    Args:
        runner_profile: Runner health, training, and environment data
        proposed_workouts: List of workout dictionaries to validate
        
    Returns:
        List of validation results, one per workout
        
    Example:
        >>> workouts = [
        ...     {"type": "easy run", "distance": 5, "terrain": "road"},
        ...     {"type": "long run", "distance": 12, "terrain": "track"}
        ... ]
        >>> results = batch_validate(profile, workouts)
        >>> len(results)
        2
    """
    results = []
    
    for workout in proposed_workouts:
        result = validate_workout(runner_profile, workout)
        results.append(result)
    
    return results