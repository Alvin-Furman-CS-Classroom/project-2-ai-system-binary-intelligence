"""
Alternative workout generation for unsafe workouts.

This module generates safe workout alternatives when the original proposed
workout is deemed unsafe. It attempts to fix specific safety violations
while maintaining the workout's general intent.
"""

from typing import Optional, Dict, Any, List, Set
from .rules import SafetyRule


def generate_alternative(
    runner_profile: Dict[str, Any],
    unsafe_workout: Dict[str, Any],
    fired_rules: List[SafetyRule]
) -> Optional[Dict[str, Any]]:
    """
    Generate a safe alternative workout based on which safety rules fired.
    
    Strategy:
    1. If any critical/non-alternative rules fired, return None (must rest)
    2. For injury-terrain rules, switch to safer terrain
    3. For excessive distance, reduce to safe limit
    4. For beginner + high intensity, switch to easy run
    5. For overtraining, suggest easier workout or rest
    6. Validate the alternative is actually safe before returning
    
    Args:
        runner_profile: Runner's health, training, and environment data
        unsafe_workout: The workout that failed validation
        fired_rules: List of rules that determined workout was unsafe
        
    Returns:
        Safe alternative workout dict, or None if no safe alternative exists
        
    Example:
        >>> profile = {"injuries": ["shin splints"], "weekly_mileage": 20, 
        ...            "available_terrain": ["track", "treadmill"]}
        >>> workout = {"type": "long run", "distance": 10, "terrain": "track"}
        >>> alt = generate_alternative(profile, workout, fired_rules)
        >>> alt["terrain"]
        'treadmill'
    """
    # Check if any rules prevent alternatives
    blocking_rules = [r for r in fired_rules if not r.can_suggest_alternative]
    if blocking_rules:
        return None  # Must rest, no alternatives possible
    
    # Start with a copy of the unsafe workout
    alternative = unsafe_workout.copy()
    modified = False
    
    # Apply fixes based on fired rules
    for rule in fired_rules:
        # Handle injury-terrain contraindications
        if "terrain" in rule.name or "injury_risk" in rule.conclusion:
            new_terrain = _find_safe_terrain(
                runner_profile.get("injuries", []),
                runner_profile.get("available_terrain", []),
                alternative.get("terrain", "")
            )
            if new_terrain:
                alternative["terrain"] = new_terrain
                modified = True
            else:
                return None  # No safe terrain available
        
        # Handle excessive distance
        if "excessive_distance" in rule.conclusion or rule.name == "excessive_distance":
            safe_distance = _calculate_safe_distance(
                runner_profile.get("weekly_mileage", 0),
                alternative.get("type", "")
            )
            if safe_distance:
                alternative["distance"] = safe_distance
                modified = True
        
        # Handle beginner + high intensity
        if rule.name == "beginner_high_intensity":
            alternative["type"] = "easy run"
            modified = True
        
        # Handle overtraining concerns
        if "overtraining" in rule.conclusion or rule.name in ["consecutive_hard_workouts", "no_rest_days"]:
            # Suggest easier workout or shorter distance
            if alternative.get("type") in ["tempo", "intervals"]:
                alternative["type"] = "easy run"
                modified = True
            if alternative.get("distance", 0) > 5:
                alternative["distance"] = max(3, alternative.get("distance", 0) * 0.5)
                modified = True
        
        # Handle race week long run
        if rule.name == "race_week_long_run":
            # Suggest shorter easy run instead
            alternative["type"] = "easy run"
            alternative["distance"] = min(5, alternative.get("distance", 0) * 0.5)
            modified = True
    
    # Return alternative only if we made modifications
    return alternative if modified else None


def _find_safe_terrain(
    injuries: List[str],
    available_terrain: List[str],
    current_terrain: str
) -> Optional[str]:
    """
    Find a safe terrain given injuries and available options.
    
    Terrain safety ranking for common injuries:
    - Shin splints: treadmill (best) > trail > road > track (worst)
    - Knee injury: treadmill (best) > road > track > trail (worst)
    - Plantar fasciitis: treadmill or trail (best) > track/road (worst)
    
    Args:
        injuries: List of current injuries
        available_terrain: List of terrain options
        current_terrain: Current (unsafe) terrain to avoid
        
    Returns:
        Safe terrain string, or None if no safe option exists
    """
    # Normalize injury names
    injuries_lower = [inj.lower() for inj in injuries]
    
    # Build preference list based on injuries
    if any("shin splint" in inj for inj in injuries_lower):
        # Treadmill is best for shin splints
        preference_order = ["treadmill", "trail", "road", "track"]
    elif any("knee" in inj for inj in injuries_lower):
        # Treadmill is best for knee issues
        preference_order = ["treadmill", "road", "track", "trail"]
    elif any("plantar" in inj for inj in injuries_lower):
        # Soft surfaces best for plantar fasciitis
        preference_order = ["treadmill", "trail", "track", "road"]
    else:
        # Generic preference for any injury
        preference_order = ["treadmill", "trail", "road", "track"]
    
    # Find best available terrain that's not the current one
    for terrain in preference_order:
        if terrain in available_terrain and terrain != current_terrain:
            return terrain
    
    return None


def _calculate_safe_distance(weekly_mileage: float, workout_type: str) -> Optional[float]:
    """
    Calculate safe distance based on weekly mileage and workout type.
    
    Safe distance limits:
    - Long run: max 1.5x weekly mileage
    - Tempo run: max 0.4x weekly mileage
    - Intervals: max 0.3x weekly mileage
    - Easy run: max 0.5x weekly mileage
    
    Args:
        weekly_mileage: Current weekly mileage
        workout_type: Type of workout
        
    Returns:
        Safe distance in miles, or None if mileage is 0
    """
    if weekly_mileage <= 0:
        return None
    
    workout_type_lower = workout_type.lower()
    
    if "long" in workout_type_lower:
        safe_limit = weekly_mileage * 1.5
    elif "tempo" in workout_type_lower:
        safe_limit = weekly_mileage * 0.4
    elif "interval" in workout_type_lower:
        safe_limit = weekly_mileage * 0.3
    else:  # easy run or other
        safe_limit = weekly_mileage * 0.5
    
    # Round to 1 decimal place
    return round(safe_limit, 1)


def can_suggest_alternative(fired_rules: List[SafetyRule]) -> bool:
    """
    Check if alternatives can be suggested given the fired rules.
    
    Args:
        fired_rules: List of rules that fired
        
    Returns:
        True if alternatives are possible, False if must rest
        
    Example:
        >>> rules = [SafetyRule(..., can_suggest_alternative=False)]
        >>> can_suggest_alternative(rules)
        False
    """
    return all(rule.can_suggest_alternative for rule in fired_rules)


def get_alternative_explanation(
    original_workout: Dict[str, Any],
    alternative_workout: Dict[str, Any]
) -> str:
    """
    Generate explanation of what changed between original and alternative.
    
    Args:
        original_workout: Original unsafe workout
        alternative_workout: Safe alternative workout
        
    Returns:
        Human-readable explanation of changes
        
    Example:
        >>> original = {"type": "long run", "distance": 12, "terrain": "track"}
        >>> alternative = {"type": "long run", "distance": 9, "terrain": "treadmill"}
        >>> explanation = get_alternative_explanation(original, alternative)
        >>> "terrain" in explanation and "distance" in explanation
        True
    """
    changes = []
    
    # Check what changed
    if original_workout.get("type") != alternative_workout.get("type"):
        changes.append(
            f"workout type changed from {original_workout.get('type')} to {alternative_workout.get('type')}"
        )
    
    if original_workout.get("distance") != alternative_workout.get("distance"):
        changes.append(
            f"distance reduced from {original_workout.get('distance')} to {alternative_workout.get('distance')} miles"
        )
    
    if original_workout.get("terrain") != alternative_workout.get("terrain"):
        changes.append(
            f"terrain changed from {original_workout.get('terrain')} to {alternative_workout.get('terrain')}"
        )
    
    if changes:
        return "Alternative workout: " + "; ".join(changes)
    else:
        return "Alternative workout suggested with minor adjustments"


def suggest_rest_day_message(fired_rules: List[SafetyRule]) -> str:
    """
    Generate appropriate rest recommendation message based on fired rules.
    
    Args:
        fired_rules: List of rules that fired
        
    Returns:
        Rest recommendation message
        
    Example:
        >>> rules = [SafetyRule(name="chest_pain_block", severity="critical", ...)]
        >>> message = suggest_rest_day_message(rules)
        >>> "medical attention" in message.lower()
        True
    """
    # Check severity of fired rules
    critical_rules = [r for r in fired_rules if r.severity == "critical"]
    
    if critical_rules:
        # Critical issues require immediate attention
        if any("chest_pain" in r.name for r in critical_rules):
            return "Seek immediate medical attention for chest pain. Do not exercise."
        elif any("dizziness" in r.name for r in critical_rules):
            return "Dizziness requires medical evaluation. Rest until cleared by doctor."
        else:
            return "Rest required. Consult with a healthcare provider before resuming training."
    
    # Non-critical but still need rest
    high_severity = [r for r in fired_rules if r.severity == "high"]
    if high_severity:
        return "Rest recommended to prevent injury. Resume training when conditions improve."
    
    # Medium severity
    return "Consider taking a rest day or easy recovery activity instead."