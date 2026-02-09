"""
Module 1: Workout safety validator using propositional logic and forward chaining.

Public API:
    validate_workout       - Main entry: validate a proposed workout for a runner.
    validate_workout_detailed - Same with optional debug info.
    quick_validate         - Minimal-input yes/no validation.
    batch_validate        - Validate multiple workouts for one runner.
"""

from .module1_safety_validator.validator import (
    validate_workout,
    validate_workout_detailed,
    quick_validate,
    batch_validate,
)

__all__ = [
    "validate_workout",
    "validate_workout_detailed",
    "quick_validate",
    "batch_validate",
]
