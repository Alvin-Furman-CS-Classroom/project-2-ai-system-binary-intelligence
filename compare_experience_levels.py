import json
from datetime import date, timedelta
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from src.module2_training_plan_generator.search import astar_plan
from src.module1_safety_validator.validator import validate_workout

def run_comparison():
    print("=== Comparing Beginner vs Intermediate Training Plans ===\n")

    race_date = (date.today() + timedelta(weeks=12)).strftime("%Y-%m-%d")

    # Test both experience levels
    for exp_level in ["beginner", "intermediate"]:
        print(f"\n{'='*60}")
        print(f"Experience Level: {exp_level.upper()}")
        print(f"{'='*60}")

        inputs = {
            "goal": "marathon",
            "race_date": race_date,
            "days_per_week": 4,
            "current_weekly_miles": 20.0,
            "experience": exp_level,
            "available_terrain": ["road", "trail"],
            "min_long_run": 6.0
        }

        profile = {
            "injuries": [],
            "weekly_mileage": 20.0,
            "experience_level": exp_level,
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal"
        }

        def safety_wrapper(p, w):
            return validate_workout(p, w)

        result = astar_plan(
            inputs=inputs,
            runner_profile=profile,
            safety_validator=safety_wrapper,
            max_expansions=10000
        )

        print(f"\nTotal Cost: {result.total_cost:.2f}")
        print(f"Nodes Expanded: {result.expanded_nodes}")

        weeks = result.output.get("plan", [])

        # Show first 3 weeks
        print("\n--- First 3 Weeks ---")
        for w in weeks[:3]:
            print(f"\nWeek {w['week']}: {w['weekly_total']} miles total, {w['long_run']} mile long run")
            for day in w["workouts"]:
                print(f"  {day['day']}: {day['type']} - {day['distance']} miles ({day['terrain']})")

        # Show final week
        if len(weeks) > 3:
            print(f"\n--- Final Week (Week {weeks[-1]['week']}) ---")
            w = weeks[-1]
            print(f"Weekly Total: {w['weekly_total']} miles, Long Run: {w['long_run']} miles")
            for day in w["workouts"]:
                print(f"  {day['day']}: {day['type']} - {day['distance']} miles ({day['terrain']})")

        # Summary statistics
        total_miles = sum(w['weekly_total'] for w in weeks)
        avg_weekly = total_miles / len(weeks) if weeks else 0
        max_weekly = max((w['weekly_total'] for w in weeks), default=0)
        max_long = max((w['long_run'] for w in weeks), default=0)

        print(f"\n--- Summary Statistics ---")
        print(f"Total Weeks: {len(weeks)}")
        print(f"Total Miles: {total_miles:.1f}")
        print(f"Average Weekly Miles: {avg_weekly:.1f}")
        print(f"Peak Weekly Miles: {max_weekly:.1f}")
        print(f"Peak Long Run: {max_long:.1f}")

        # Count quality workouts
        quality_count = sum(
            1 for w in weeks for day in w["workouts"]
            if day.get("type") in {"tempo", "interval", "intervals"}
        )
        print(f"Total Quality Workouts: {quality_count}")

if __name__ == "__main__":
    run_comparison()
