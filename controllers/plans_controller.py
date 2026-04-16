from urllib.request import Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from src.module2_plan_generator.search import a_star_search
from src.module2_plan_generator.states import TrainingState

templates = Jinja2Templates(directory="templates")


def show_form(request: Request):
    return templates.TemplateResponse(
        "plan_form.html",
        {"request": request}
    )


def handle_form(request: Request, form_data: dict):
    # Get race type and calculate target distance
    race_type = form_data.get("race_type", "full_marathon")
    race_distances = {
        "full_marathon": {"name": "Full Marathon", "distance_km": 42.2, "distance_miles": 26.2, "peak_long_run_miles": 20},
        "half_marathon": {"name": "Half Marathon", "distance_km": 21.1, "distance_miles": 13.1, "peak_long_run_miles": 11},
        "10k": {"name": "10K", "distance_km": 10, "distance_miles": 6.2, "peak_long_run_miles": 7},
        "custom": {"name": "Custom", "distance_km": 0, "distance_miles": 0, "peak_long_run_miles": 0},
    }
    race_info = race_distances.get(race_type, race_distances["full_marathon"])

    # Calculate total weeks from today to race date
    race_date_str = form_data["race_date"]
    race_date = datetime.strptime(race_date_str, "%Y-%m-%d").date()
    today = date.today()

    days_until_race = (race_date - today).days
    total_weeks = max(1, days_until_race // 7)  # At least 1 week

    start = TrainingState.create_start(
        total_weeks=total_weeks,
        days_per_week=int(form_data["days_per_week"]),
        current_weekly_miles=float(form_data["current_weekly_miles"]),
        available_terrain=form_data.get("available_terrain", ["road"]),
        experience=form_data.get("experience", "beginner"),
    )

    result = a_star_search(start)

    # Assign workouts to specific days
    training_days = form_data.get("training_days", [])
    if result.get("plan") and training_days:
        for week in result["plan"]:
            workouts = week.get("workouts", [])

            # Strategy: Assign long run to last day, spread others across remaining days
            # Separate long runs from other workouts
            long_runs = [w for w in workouts if w.get("type") == "long run"]
            other_workouts = [w for w in workouts if w.get("type") != "long run"]

            # Sort training days so weekend days come last (good for long runs)
            sorted_days = sorted(training_days, key=lambda d: (
                d not in ["Saturday", "Sunday"],  # Weekend last
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(d)
            ))

            day_index = 0
            # Assign other workouts first
            for workout in other_workouts:
                if day_index < len(sorted_days):
                    workout["day"] = sorted_days[day_index]
                    day_index += 1

            # Assign long runs to remaining days (preferably weekends)
            for workout in long_runs:
                if day_index < len(sorted_days):
                    workout["day"] = sorted_days[day_index]
                    day_index += 1

    # Add race info to result for display
    result["race_type"] = race_info["name"]
    result["race_distance"] = f"{race_info['distance_km']} km / {race_info['distance_miles']} miles"
    result["race_date"] = race_date_str
    result["total_weeks"] = total_weeks
    result["training_days"] = ", ".join(training_days)

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "result": result
        }
    )