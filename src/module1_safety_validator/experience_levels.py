"""
Runner experience level definitions and validation.

Defines clear criteria for beginner, intermediate, and advanced runners based on
evidence-based practices from sports medicine research and running coaching experts.
See README.md References section for sources.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class ExperienceLevelCriteria:
    """
    Defines criteria and safe limits for a runner experience level.
    
    Attributes:
        name: Experience level name (beginner, intermediate, advanced)
        min_weekly_mileage: Minimum expected weekly mileage
        max_weekly_mileage: Maximum safe weekly mileage
        max_long_run: Maximum safe long run distance
        can_do_high_intensity: Whether high-intensity workouts are appropriate
        description: Human-readable description of this level
    """
    name: str
    min_weekly_mileage: float
    max_weekly_mileage: float
    max_long_run: float
    can_do_high_intensity: bool
    description: str


# Experience level definitions based on research and coaching best practices
BEGINNER = ExperienceLevelCriteria(
    name="beginner",
    min_weekly_mileage=0,
    max_weekly_mileage=30,
    max_long_run=13,
    can_do_high_intensity=False,
    description=(
        "Less than 1 year of consistent running OR training for first race. "
        "Focus: Building base endurance, learning proper form, gradual progression. "
        "Should avoid high-intensity workouts (tempo, intervals)."
    )
)

INTERMEDIATE = ExperienceLevelCriteria(
    name="intermediate",
    min_weekly_mileage=20,
    max_weekly_mileage=50,
    max_long_run=18,
    can_do_high_intensity=True,
    description=(
        "1-3 years of consistent running OR completed 2+ races. "
        "Has solid running base, can handle tempo runs and moderate intervals, "
        "understands pacing, working on speed and endurance."
    )
)

ADVANCED = ExperienceLevelCriteria(
    name="advanced",
    min_weekly_mileage=40,
    max_weekly_mileage=200,  # Elite runners can reach 100-200 miles/week
    max_long_run=26,
    can_do_high_intensity=True,
    description=(
        "3+ years of consistent running OR completed 5+ races including marathons. "
        "Strong aerobic base, can handle all workout types, training for PRs "
        "or competitive times, experienced with race strategy."
    )
)

# Map of all experience levels
EXPERIENCE_LEVELS = {
    "beginner": BEGINNER,
    "intermediate": INTERMEDIATE,
    "advanced": ADVANCED
}


def get_experience_criteria(level: str) -> Optional[ExperienceLevelCriteria]:
    """
    Get criteria for a specific experience level.
    
    Args:
        level: Experience level name (case-insensitive)
        
    Returns:
        ExperienceLevelCriteria object or None if level not found
        
    Example:
        >>> criteria = get_experience_criteria("beginner")
        >>> criteria.max_weekly_mileage
        30
    """
    return EXPERIENCE_LEVELS.get(level.lower())


def validate_experience_level_consistency(
    declared_level: str,
    weekly_mileage: float
) -> Tuple[bool, Optional[str]]:
    """
    Validate if declared experience level is consistent with actual training data.
    
    Checks if the runner's weekly mileage is appropriate for their declared
    experience level. Helps catch data entry errors or runners misclassifying
    their level.
    
    Args:
        declared_level: Self-declared experience level
        weekly_mileage: Current weekly running mileage
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if consistent, False if mismatch detected
        - error_message: Explanation if invalid, None if valid
        
    Example:
        >>> validate_experience_level_consistency("beginner", 2000)
        (False, "Beginner runners should not exceed 30 miles/week. Current: 2000 miles/week.")
    """
    # Normalize level name
    level_lower = declared_level.lower()
    
    # Check if valid level
    if level_lower not in EXPERIENCE_LEVELS:
        return False, (
            f"Invalid experience level: '{declared_level}'. "
            f"Must be one of: beginner, intermediate, advanced"
        )
    
    criteria = EXPERIENCE_LEVELS[level_lower]
    
    # Check if mileage exceeds maximum for this level
    if weekly_mileage > criteria.max_weekly_mileage:
        return False, (
            f"{criteria.name.capitalize()} runners should not exceed "
            f"{criteria.max_weekly_mileage} miles/week. "
            f"Current: {weekly_mileage} miles/week. "
            f"Consider selecting '{get_appropriate_level(weekly_mileage)}' experience level."
        )
    
    # Check if mileage is suspiciously low for advanced runners
    if level_lower == "advanced" and weekly_mileage < INTERMEDIATE.min_weekly_mileage:
        return False, (
            f"Advanced runners typically run at least {INTERMEDIATE.min_weekly_mileage} miles/week. "
            f"Current: {weekly_mileage} miles/week. "
            f"Consider selecting 'beginner' or 'intermediate' experience level."
        )
    
    return True, None


def get_appropriate_level(weekly_mileage: float) -> str:
    """
    Suggest appropriate experience level based on weekly mileage.
    
    Args:
        weekly_mileage: Current weekly running mileage
        
    Returns:
        Suggested experience level name
        
    Example:
        >>> get_appropriate_level(45)
        'intermediate'
    """
    if weekly_mileage <= BEGINNER.max_weekly_mileage:
        return "beginner"
    elif weekly_mileage <= INTERMEDIATE.max_weekly_mileage:
        return "intermediate"
    else:
        return "advanced"


def validate_workout_for_experience(
    experience_level: str,
    workout_type: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate if a workout type is appropriate for an experience level.
    
    Beginners should not do high-intensity workouts like tempo runs or intervals.
    
    Args:
        experience_level: Runner's experience level
        workout_type: Type of workout (e.g., "tempo", "intervals", "easy run")
        
    Returns:
        Tuple of (is_appropriate, warning_message)
        
    Example:
        >>> validate_workout_for_experience("beginner", "tempo")
        (False, "Beginners should not perform high-intensity workouts like tempo runs...")
    """
    level_lower = experience_level.lower()
    workout_lower = workout_type.lower()
    
    if level_lower not in EXPERIENCE_LEVELS:
        return True, None  # Can't validate unknown level
    
    criteria = EXPERIENCE_LEVELS[level_lower]
    
    # Check if workout requires high intensity
    high_intensity_workouts = ["tempo", "interval", "intervals", "hill", "fartlek"]
    is_high_intensity = any(hw in workout_lower for hw in high_intensity_workouts)
    
    if is_high_intensity and not criteria.can_do_high_intensity:
        return False, (
            f"{criteria.name.capitalize()} runners should not perform high-intensity "
            f"workouts like {workout_type}. Focus on easy runs and gradual mileage "
            f"increases to build a solid base first."
        )
    
    return True, None