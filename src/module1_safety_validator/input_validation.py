"""
Input validation for runner profiles and workout data.

Validates that input data is realistic and consistent before processing.
Prevents garbage in/garbage out scenarios.
"""

from typing import Dict, Any, Optional, List
from .experience_levels import (
    validate_experience_level_consistency,
    validate_workout_for_experience,
    EXPERIENCE_LEVELS
)


def validate_runner_profile(runner_profile: Dict[str, Any]) -> Optional[str]:
    """
    Validate runner profile for realistic and consistent data.
    
    Validates structural issues and realistic bounds on input data.
    Does NOT validate safety concerns like injury-terrain compatibility
    or training load appropriateness - those are handled by the inference
    engine which applies the full rule set and can suggest alternatives.
    
    Checks:
    - Realistic weekly mileage bounds (0-250 miles)
    - Experience level consistency with mileage
    - Valid workout structure (distance bounds, terrain validity)
    - Realistic training frequency (days trained, rest days)
    - Available terrain is provided when injuries exist
    
    Args:
        runner_profile: Runner profile dictionary
        
    Returns:
        Error message string if invalid, None if valid
        
    Example:
        >>> profile = {"weekly_mileage": 2000, "experience_level": "beginner"}
        >>> validate_runner_profile(profile)
        "Weekly mileage of 2000 miles exceeds realistic maximum..."
    """
    errors = []
    
    # Validate weekly mileage bounds
    weekly_mileage = runner_profile.get("weekly_mileage", 0)
    if weekly_mileage < 0:
        errors.append("Weekly mileage cannot be negative")
    elif weekly_mileage > 250:
        errors.append(
            f"Weekly mileage of {weekly_mileage} miles exceeds realistic maximum "
            f"(even elite marathoners rarely exceed 200 miles/week)"
        )
    
    # Validate experience level consistency
    experience_level = runner_profile.get("experience_level", "beginner")
    if weekly_mileage > 0:
        is_valid, error = validate_experience_level_consistency(
            experience_level,
            weekly_mileage
        )
        if not is_valid:
            errors.append(error)
    
    # Validate proposed workout structure (not appropriateness)
    workout = runner_profile.get("proposed_workout")
    if workout:
        workout_errors = validate_workout_structure(workout)
        if workout_errors:
            errors.extend(workout_errors)
    
    # Validate training frequency
    days_trained = runner_profile.get("days_trained_this_week", 0)
    if days_trained < 0:
        errors.append("Days trained cannot be negative")
    elif days_trained > 7:
        errors.append(f"Days trained ({days_trained}) cannot exceed 7 days in a week")
    
    rest_days = runner_profile.get("rest_days_this_week", 0)
    if rest_days < 0:
        errors.append("Rest days cannot be negative")
    elif rest_days > 7:
        errors.append(f"Rest days ({rest_days}) cannot exceed 7 days in a week")
    
    # Check if days trained + rest days is realistic
    if days_trained + rest_days > 7:
        errors.append(
            f"Days trained ({days_trained}) + rest days ({rest_days}) "
            f"cannot exceed 7 days in a week"
        )
    
    # Validate available terrain if injuries present
    injuries = runner_profile.get("injuries", [])
    available_terrain = runner_profile.get("available_terrain", [])
    
    if injuries and not available_terrain:
        errors.append(
            "Runner has injuries but no available_terrain provided. "
            "System cannot suggest terrain alternatives without this information."
        )
    
    # Validate terrain options are valid
    if available_terrain:
        valid_terrains = ["road", "track", "trail", "treadmill"]
        invalid_terrains = [t for t in available_terrain if t.lower() not in valid_terrains]
        if invalid_terrains:
            errors.append(
                f"Invalid terrain options: {', '.join(invalid_terrains)}. "
                f"Valid options: {', '.join(valid_terrains)}"
            )
    
    # Return first error or None
    return errors[0] if errors else None


def validate_workout_structure(workout: Dict[str, Any]) -> List[str]:
    """
    Validate workout structure and data types only.
    
    Checks for structural issues like invalid terrain names, negative distances,
    or unrealistic distance values. Does NOT validate safety concerns like
    whether a beginner should do tempo runs or whether distance is too long
    for weekly mileage - those are handled by the inference engine.
    
    Args:
        workout: Proposed workout dictionary
        
    Returns:
        List of structural error messages (empty if valid)
    """
    errors = []
    
    # Validate distance
    distance = workout.get("distance", 0)
    if distance < 0:
        errors.append("Workout distance cannot be negative")
    elif distance > 50:
        errors.append(
            f"Single workout distance of {distance} miles is extremely high. "
            f"Even marathon distance is only 26.2 miles. Please verify this is correct."
        )
    
    # Validate terrain
    terrain = workout.get("terrain", "")
    valid_terrains = ["road", "track", "trail", "treadmill"]
    if terrain and terrain.lower() not in valid_terrains:
        errors.append(
            f"Invalid terrain: '{terrain}'. "
            f"Valid options: {', '.join(valid_terrains)}"
        )
    
    return errors


def validate_workout_data(
    workout: Dict[str, Any],
    runner_profile: Dict[str, Any]
) -> List[str]:
    """
    Validate proposed workout data including appropriateness for runner.
    
    This is a comprehensive validation that includes checking if workout
    is appropriate for experience level. Used for standalone validation,
    not in the main validation flow (which uses inference engine).
    
    Args:
        workout: Proposed workout dictionary
        runner_profile: Runner profile for context
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # First check structure
    errors.extend(validate_workout_structure(workout))
    
    # Then check appropriateness for experience level
    workout_type = workout.get("type", "")
    experience_level = runner_profile.get("experience_level", "beginner")
    
    if workout_type:
        is_valid, error = validate_workout_for_experience(
            experience_level,
            workout_type
        )
        if not is_valid:
            errors.append(error)
    
    return errors


def validate_injury_data(injuries: List[str]) -> Optional[str]:
    """
    Validate injury list for common data entry errors.
    
    Args:
        injuries: List of injury names
        
    Returns:
        Warning message if suspicious, None otherwise
        
    Note: This is a soft validation - we still process unknown injuries,
    but warn the user in case of typos.
    """
    if not injuries:
        return None
    
    # Known injury types (for warning purposes only)
    known_injuries = [
        "shin splints", "knee", "plantar fasciitis", "it band", "itb",
        "achilles", "stress fracture", "hip", "hamstring", "calf",
        "quad", "ankle", "foot", "back", "runner's knee"
    ]
    
    unrecognized = []
    for injury in injuries:
        injury_lower = injury.lower()
        if not any(known in injury_lower for known in known_injuries):
            unrecognized.append(injury)
    
    if unrecognized:
        return (
            f"Warning: Unrecognized injury types: {', '.join(unrecognized)}. "
            f"System will treat these as generic injuries requiring medical clearance. "
            f"If this is a typo, please correct it."
        )
    
    return None


def get_validation_summary(runner_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get comprehensive validation summary with warnings and errors.
    
    Args:
        runner_profile: Runner profile to validate
        
    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    errors = []
    warnings = []
    
    # Critical errors
    error = validate_runner_profile(runner_profile)
    if error:
        errors.append(error)
    
    # Warnings (non-blocking)
    injuries = runner_profile.get("injuries", [])
    injury_warning = validate_injury_data(injuries)
    if injury_warning:
        warnings.append(injury_warning)
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }