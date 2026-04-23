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

DEMO_PROFILES = {
    "alex": {
        "display_name": "Alex",
        "race_type": "half_marathon",
        "race_date": "2026-10-04",
        "training_days": ["Monday", "Wednesday", "Friday", "Sunday"],
        "current_weekly_miles": 20.0,
        "experience": "intermediate",
        "available_terrain": ["road", "trail"],
    },
    "sam": {
        "display_name": "Sam",
        "race_type": "full_marathon",
        "race_date": "2026-11-15",
        "training_days": ["Tuesday", "Thursday", "Saturday", "Sunday"],
        "current_weekly_miles": 35.0,
        "experience": "advanced",
        "available_terrain": ["road"],
    },
    "jordan": {
        "display_name": "Jordan",
        "race_type": "10k",
        "race_date": "2026-08-22",
        "training_days": ["Monday", "Wednesday", "Saturday"],
        "current_weekly_miles": 10.0,
        "experience": "beginner",
        "available_terrain": ["treadmill", "road"],
    },
}


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

    # Attach actual dates to each week and workout for chart + calendar
    from datetime import timedelta
    _day_to_weekday = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6,
    }
    if result.get("plan"):
        for week in result["plan"]:
            week_num = week.get("week", 1)
            week_start = today + timedelta(weeks=week_num - 1)
            week["week_start_date"] = week_start.strftime("%b %d")

            # Map workout day-names to concrete dates
            start_wd = week_start.weekday()
            for workout in week.get("workouts", []):
                wday = workout.get("day", "")
                if wday in _day_to_weekday:
                    offset = (_day_to_weekday[wday] - start_wd) % 7
                    wdate = week_start + timedelta(days=offset)
                    workout["workout_date"] = wdate.isoformat()

            # Build 7-day calendar row for this week
            calendar_days = []
            for i in range(7):
                day_date = week_start + timedelta(days=i)
                day_iso = day_date.isoformat()
                day_workouts = [w for w in week.get("workouts", []) if w.get("workout_date") == day_iso]
                calendar_days.append({
                    "date": day_date.strftime("%-d"),
                    "month": day_date.strftime("%b"),
                    "day_name": day_date.strftime("%a"),
                    "workouts": day_workouts,
                })
            week["calendar_days"] = calendar_days

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


def generate_for_user(request: Request, name: str):
    profile = DEMO_PROFILES.get(name.lower())
    if not profile:
        available = ", ".join(f"/user/{k}" for k in DEMO_PROFILES)
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "message": f"Demo user '{name}' not found. Try: {available}"},
            status_code=404,
        )
    return handle_form(request, {**profile, "days_per_week": len(profile["training_days"])})