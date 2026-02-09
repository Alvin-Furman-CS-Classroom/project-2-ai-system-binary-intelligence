import json
import logging
from datetime import date, timedelta

# Adjust path if needed or run as 'python -m ...'
# but assuming we are in project root, we can import src
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

try:
    from src.module2_training_plan_generator.search import astar_plan
    from src.module1_safety_validator.validator import validate_workout
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure you are running this from the project root and paths are correct.")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def run_demo():
    print("=== Running Module 2 Demo (Training Plan Generator) ===")

    # 1. Define Input Constraints
    race_date = (date.today() + timedelta(weeks=12)).strftime("%Y-%m-%d")
    inputs = {
        "goal": "marathon",
        "race_date": race_date,
        "days_per_week": 4,
        "current_weekly_miles": 20.0,
        "experience": "intermediate",
        "available_terrain": ["road", "trail"],
        "min_long_run": 6.0
    }
    
    # 2. Define a Dummy Profile for Validation
    profile = {
        "injuries": [],
        "weekly_mileage": 20.0,
        "experience_level": "intermediate",
        "hydrated": True,
        "proper_footwear": True,
        "weather": "normal"
    }

    # 3. Wrapper for Safety Validator (Module 1 integration)
    # The search expects (profile, workout) -> result_dict
    def safety_wrapper(p, w):
        return validate_workout(p, w)

    print(f"Goal: {inputs['goal']}")
    print(f"Race Date: {inputs['race_date']}")
    print(f"Starting Mileage: {inputs['current_weekly_miles']}")
    print("-" * 40)

    # 4. Run Search
    print("Starting A* Search...")
    result = astar_plan(
        inputs=inputs, 
        runner_profile=profile, 
        safety_validator=safety_wrapper,
        max_expansions=10000
    )

    # 5. Output Results
    print(f"\nPlan Generated!")
    print(f"Total Cost: {result.total_cost}")
    print(f"Nodes Expanded: {result.expanded_nodes}")
    
    # Correct key is 'plan' not 'weeks' per plan_formatter.py
    print("\n--- First 3 Weeks of Plan ---")
    weeks = result.output.get("plan", [])
    
    if not weeks:
        print("No weeks found in output. Plan dictionary keys:", result.output.keys())
        
    for w in weeks[:3]:
        print(f"\nWeek {w['week']} (Total: {w['weekly_total']} miles, Long Run: {w['long_run']} miles)")
        for day in w["workouts"]:
            print(f"  {day['day']}: {day['type']} - {day['distance']} miles ({day['terrain']})")
            
    print(f"\n... (Total {len(weeks)} weeks) ...")

if __name__ == "__main__":
    run_demo()
