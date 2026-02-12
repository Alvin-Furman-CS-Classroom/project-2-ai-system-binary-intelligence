"""
Module 2: Training Plan Generator using A* search.

Generates personalized multi-week marathon training plans by searching
through possible workout combinations using the A* algorithm with a
domain-specific heuristic. Every candidate workout is optionally
validated through Module 1 (safety validator) before inclusion.

Public API:
    generate_plan          - Main entry: generate a training plan.
    generate_plan_detailed - Same with per-week penalty analysis.

Example:
    >>> from src.module2_plan_generator import generate_plan
    >>> config = {
    ...     "goal": "complete marathon",
    ...     "race_date": "2025-10-15",
    ...     "days_per_week": 4,
    ...     "current_weekly_miles": 15,
    ...     "experience": "beginner",
    ...     "available_terrain": ["road", "trail"],
    ... }
    >>> result = generate_plan(config)
    >>> result["success"]
    True
    >>> len(result["plan"]) > 0
    True

Integration with Module 1:
    >>> from src.module1_safety_validator import validate_workout
    >>> profile = {"weekly_mileage": 15, "experience_level": "beginner", ...}
    >>> result = generate_plan(config, validate_fn=validate_workout,
    ...                        runner_profile=profile)
"""

from .planner import generate_plan, generate_plan_detailed

__all__ = [
    "generate_plan",
    "generate_plan_detailed",
]
