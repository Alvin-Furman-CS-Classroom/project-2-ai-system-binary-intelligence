"""
demo_validator.py

Full runnable demo for the workout safety validator module.

How to run:
1) Put this file next to your package/module that exposes:
   - validate_workout
   - validate_workout_detailed
   - quick_validate
   - batch_validate

2) Update the import line below to match your project structure.

3) Run:
   python demo_validator.py
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import sys
import os

# Add project root to sys.path so we can import as a package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.module1_safety_validator.validator import (
    validate_workout,
    validate_workout_detailed,
    quick_validate,
    batch_validate,
)


def pretty(obj: Any) -> str:
    """Pretty JSON string for printing nested dicts cleanly."""
    return json.dumps(obj, indent=2, sort_keys=True, default=str)


def demo_validate_workout(profile: Dict[str, Any], workout: Dict[str, Any]) -> None:
    print("\n" + "=" * 80)
    print("DEMO 1) validate_workout(profile, workout)")
    print("=" * 80)

    result = validate_workout(profile, workout)

    print("Input profile:", pretty(profile))
    print("Input workout:", pretty(workout))
    print("\nResult:", pretty(result))

    # Safe access helpers
    print("\nKey fields:")
    print("  safe:", result.get("safe"))
    print("  severity:", result.get("severity"))
    print("  reason:", result.get("reason"))
    print("  alternative:", pretty(result.get("alternative")))
    print("  recommendation:", result.get("recommendation"))


def demo_validate_workout_detailed(profile: Dict[str, Any], workout: Dict[str, Any]) -> None:
    print("\n" + "=" * 80)
    print("DEMO 2) validate_workout_detailed(profile, workout, debug=True)")
    print("=" * 80)

    result = validate_workout_detailed(profile, workout, debug=True)

    print("\nResult:", pretty(result))

    debug = result.get("_debug_info")
    if debug:
        print("\nDebug breakdown:")
        print("  initial_facts:", pretty(debug.get("initial_facts")))
        print("  derived_facts:", pretty(debug.get("derived_facts")))
        print("  fired_rules:", pretty(debug.get("fired_rules")))
        print("  severity:", debug.get("severity"))
        print("  inference_chain:\n", debug.get("inference_chain"))
    else:
        print("\nNo _debug_info present (debug=False or module did not return it).")


def demo_quick_validate() -> None:
    print("\n" + "=" * 80)
    print("DEMO 3) quick_validate(...)  -> bool")
    print("=" * 80)

    is_safe = quick_validate(
        injuries=["shin splints"],
        workout_type="long run",
        distance=12,
        terrain="track",
        weekly_mileage=15,
    )

    print("quick_validate returned:", is_safe)


def demo_batch_validate(profile: Dict[str, Any]) -> None:
    print("\n" + "=" * 80)
    print("DEMO 4) batch_validate(profile, workouts)")
    print("=" * 80)

    workouts: List[Dict[str, Any]] = [
        {"type": "easy run", "distance": 4, "terrain": "road"},
        {"type": "tempo", "distance": 6, "terrain": "track"},
        {"type": "long run", "distance": 12, "terrain": "track"},
    ]

    results = batch_validate(profile, workouts)

    print("Workouts:", pretty(workouts))
    print("\nResults:")
    for i, r in enumerate(results, start=1):
        print(f"\nWorkout #{i}:")
        print(pretty(r))


def demo_input_validation_failure() -> None:
    """
    This demo intentionally passes bad input to show the "Invalid input: ..."
    path in validate_workout (the one that returns SEVERITY_CRITICAL).
    """
    print("\n" + "=" * 80)
    print("DEMO 5) Input validation failure example")
    print("=" * 80)

    bad_profile = {
        # missing required fields your validate_runner_profile likely expects
        "injuries": "shin splints",  # should be List[str], not str
        "weekly_mileage": "fifteen",  # should be float/number
        "hydrated": True,
    }
    workout = {"type": "easy run", "distance": 3, "terrain": "road"}

    result = validate_workout(bad_profile, workout)
    print("Bad profile:", pretty(bad_profile))
    print("Result:", pretty(result))


def main() -> None:
    # A fairly complete profile that should satisfy validate_runner_profile(full_profile)
    profile: Dict[str, Any] = {
        "symptoms": [],
        "injuries": ["shin splints"],
        "pain_level": "moderate",          # "none"|"mild"|"moderate"|"severe"
        "cleared_by_doctor": False,
        "fully_recovered": True,
        "sleep_quality": "good",           # "poor"|"fair"|"good"
        "rest_days_this_week": 1,
        "days_trained_this_week": 4,
        "hard_workout_yesterday": False,
        "weekly_mileage": 15.0,
        "experience_level": "beginner",    # "beginner"|"intermediate"|"advanced"
        "race_date": None,                 # or "2026-04-10"
        "weather": "normal",               # "normal"|"extreme_heat"|"extreme_cold"
        "hydrated": True,
        "proper_footwear": True,
        "available_terrain": ["treadmill", "track", "road"],
    }

    workout: Dict[str, Any] = {
        "type": "long run",   # "easy run"|"long run"|"tempo"|"intervals"
        "distance": 12.0,
        "terrain": "track",   # "track"|"road"|"trail"|"treadmill"
    }

    demo_validate_workout(profile, workout)
    demo_validate_workout_detailed(profile, workout)
    demo_quick_validate()
    demo_batch_validate(profile)
    demo_input_validation_failure()


if __name__ == "__main__":
    main()
