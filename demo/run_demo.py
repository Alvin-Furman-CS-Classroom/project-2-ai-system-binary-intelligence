#!/usr/bin/env python3
"""
Demo: Module 1 (safety validator) + Module 2 (plan generator).

Generates a marathon plan; every workout is safety-checked by Module 1.
Shows any warnings for your current profile and an example of checking
one workout (warning + alternative or what to do).

Run from repo root:  PYTHONPATH=. python demo/run_demo.py
"""

import sys
from pathlib import Path

# Add repo root so "src" is importable when run from demo/ or via Code Runner
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from datetime import date, timedelta

from src.module1_safety_validator import validate_workout
from src.module2_plan_generator import generate_plan


def main() -> None:
    # Race ~16 weeks out so the plan has room to build
    race_date = (date.today() + timedelta(weeks=13)).strftime("%Y-%m-%d")

    # Runner: beginner, healthy, road + track
    runner_profile = {
        "weekly_mileage": 8,
        "experience_level": "beginner",
        "injuries": [],
        "symptoms": [],
        "pain_level": "none",
        "fully_recovered": True,
        "sleep_quality": "good",
        "rest_days_this_week": 2,
        "days_trained_this_week": 3,
        "hydrated": True,
        "proper_footwear": True,
        "weather": "normal",
        "available_terrain": ["road", "track"],
    }

    # Plan config (must match profile for consistency)
    config = {
        "goal": "complete marathon",
        "race_date": race_date,
        "days_per_week": 5,
        "current_weekly_miles": 8,
        "experience": "intermediate",
        "available_terrain": ["road", "track"],
    }

    print("Long Run — Demo: Module 1 + Module 2")
    print("=" * 50)
    print(f"Runner: {config['experience']}, {config['current_weekly_miles']} mi/week, {', '.join(config['available_terrain'])}")
    print(f"Race date: {race_date}")
    print()

    # Generate plan with Module 1 validating every candidate workout
    result = generate_plan(
        config,
        validate_fn=validate_workout,
        runner_profile=runner_profile,
    )

    if not result["success"]:
        print("Plan generation failed:", result.get("errors", result.get("rationale", "Unknown")))
        return

    plan = result["plan"]
    print(f"Generated {len(plan)}-week plan (search: {result['search_stats']['nodes_explored']} nodes)")
    print()
    print("Full plan (all weeks):")
    for week_data in plan:
        week_num = week_data["week"]
        miles = week_data["total_miles"]
        workouts = week_data["workouts"]
        print(f"  Week {week_num}: {miles:.1f} mi — {len(workouts)} workouts")
        for w in workouts:
            print(f"    - {w.get('type', '?')} {w.get('distance', 0):.1f} mi ({w.get('terrain', '?')})")
    print()

    # Unique warnings for your profile (e.g. hydrate, footwear) — fix before you run
    advisories = result.get("advisory_notes", [])
    if advisories:
        print("Before you run:")
        for msg in advisories:
            print(f"  • {msg}")
        print()

    # Example: check one workout and get a clear warning + alternative or what to do
    sample_workout = plan[1]["workouts"][0]
    check = validate_workout(runner_profile, sample_workout)
    w = sample_workout
    print("Example — checking one planned workout with Module 1:")
    print(f"  \"Can I do {w.get('type')} {w.get('distance')} mi on {w.get('terrain')}?\"")
    if check["safe"]:
        print("  → Good to go.")
    else:
        print(f"  → Warning: {check['reason']}")
        if check.get("alternative"):
            alt = check["alternative"]
            print(f"  → Try this instead: {alt.get('type')} {alt.get('distance')} mi on {alt.get('terrain')}.")
        elif check.get("severity") == "medium":
            print("  → What to do: fix the issue above before running (e.g. hydrate, proper shoes).")
        elif check.get("recommendation"):
            print(f"  → What to do: {check['recommendation']}.")
    print()
    print(result["rationale"])


if __name__ == "__main__":
    main()