"""
Input validation for the training plan generator.

Validates planner inputs before search begins, checking that all required
fields are present and values are within acceptable ranges.

Example:
    >>> from module2_plan_generator.input_validation import validate_planner_input
    >>> config = {
    ...     "goal": "complete marathon",
    ...     "race_date": "2025-06-15",
    ...     "days_per_week": 4,
    ...     "current_weekly_miles": 15,
    ...     "experience": "beginner",
    ...     "available_terrain": ["road", "trail"],
    ... }
    >>> errors = validate_planner_input(config)
    >>> errors
    []
"""

from datetime import datetime, date
from typing import Any


# Valid values for constrained fields.
VALID_GOALS = {"complete marathon", "complete half marathon"}
VALID_EXPERIENCE_LEVELS = {"beginner", "intermediate", "advanced"}
VALID_TERRAIN_TYPES = {"road", "track", "trail", "treadmill"}


def validate_planner_input(config: dict[str, Any]) -> list[str]:
    """Validate all planner configuration fields and return a list of errors.

    An empty list means the input is valid. Each string in the returned list
    describes one validation failure.

    Args:
        config: Dictionary containing planner configuration. Required keys
            are ``goal``, ``race_date``, ``days_per_week``,
            ``current_weekly_miles``, ``experience``, and
            ``available_terrain``.

    Returns:
        A list of human-readable error strings. Empty when input is valid.

    Example:
        >>> errors = validate_planner_input({"goal": "fly to moon"})
        >>> len(errors) > 0
        True
    """
    errors: list[str] = []

    # --- required keys ---
    required_keys = [
        "goal",
        "race_date",
        "days_per_week",
        "current_weekly_miles",
        "experience",
        "available_terrain",
    ]
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required field: '{key}'.")

    # If required keys are missing we cannot validate further.
    if errors:
        return errors

    # --- goal ---
    goal = config["goal"]
    if not isinstance(goal, str) or goal.lower() not in VALID_GOALS:
        errors.append(
            f"Invalid goal: '{goal}'. Must be one of: {sorted(VALID_GOALS)}."
        )

    # --- race_date ---
    race_date = config["race_date"]
    parsed_date = _parse_date(race_date)
    if parsed_date is None:
        errors.append(
            f"Invalid race_date: '{race_date}'. Use ISO format YYYY-MM-DD."
        )
    else:
        today = date.today()
        if parsed_date <= today:
            errors.append("race_date must be in the future.")
        weeks_until = (parsed_date - today).days // 7
        if weeks_until < 4:
            errors.append(
                f"Race is only {weeks_until} weeks away. Need at least 4 weeks."
            )
        if weeks_until > 30:
            errors.append(
                f"Race is {weeks_until} weeks away. Maximum supported is 30 weeks."
            )

    # --- days_per_week ---
    days = config["days_per_week"]
    if not isinstance(days, int) or days < 3 or days > 6:
        errors.append(
            f"days_per_week must be an integer between 3 and 6. Got: {days}."
        )

    # --- current_weekly_miles ---
    miles = config["current_weekly_miles"]
    if not isinstance(miles, (int, float)) or miles < 0:
        errors.append(
            f"current_weekly_miles must be a non-negative number. Got: {miles}."
        )
    elif miles > 100:
        errors.append(
            f"current_weekly_miles of {miles} seems too high. Max supported is 100."
        )

    # --- experience ---
    exp = config["experience"]
    if not isinstance(exp, str) or exp.lower() not in VALID_EXPERIENCE_LEVELS:
        errors.append(
            f"Invalid experience: '{exp}'. "
            f"Must be one of: {sorted(VALID_EXPERIENCE_LEVELS)}."
        )

    # --- available_terrain ---
    terrain = config["available_terrain"]
    if not isinstance(terrain, list) or len(terrain) == 0:
        errors.append("available_terrain must be a non-empty list.")
    else:
        for t in terrain:
            if t.lower() not in VALID_TERRAIN_TYPES:
                errors.append(
                    f"Invalid terrain type: '{t}'. "
                    f"Must be one of: {sorted(VALID_TERRAIN_TYPES)}."
                )

    # --- cross-field: experience vs mileage consistency ---
    if not errors:
        exp_lower = config["experience"].lower()
        m = config["current_weekly_miles"]
        if exp_lower == "beginner" and m > 30:
            errors.append(
                f"Beginner runners typically run at most 30 miles/week. "
                f"Got {m}. Consider 'intermediate' or 'advanced'."
            )
        if exp_lower == "advanced" and m < 20:
            errors.append(
                f"Advanced runners typically run at least 20 miles/week. "
                f"Got {m}. Consider 'beginner' or 'intermediate'."
            )

    return errors


def _parse_date(value: Any) -> date | None:
    """Try to parse a value as a date. Returns None on failure."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None
