"""
Demo runner for your A* / beam-A* training plan generator.

Usage:
  python demo_plan_search.py
  python demo_plan_search.py --weeks 20 --current-miles 22 --days 5 --beam-width 15
  python demo_plan_search.py --use-validator
  python demo_plan_search.py --beam-width none   # unlimited beam (pure A* style, if supported)

Notes:
- This demo includes a robust summarize_plan() that works even if your plan schema
  doesn't store week_number / weekly_miles at the top level.
- If your a_star_search currently crashes on beam_width=None, see the patch snippet
  near the bottom of this file.
"""

from __future__ import annotations

import argparse
from typing import Any, Iterable

import sys
import os

# Fix path/imports so we can run this file directly
if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from src.module2_plan_generator.search import a_star_search
    from src.module2_plan_generator.states import TrainingState
else:
    from .search import a_star_search
    from .states import TrainingState


# ----------------------------
# Optional validator stub
# ----------------------------
def validate_workout_stub(profile: dict, workout: dict) -> dict:
    """
    A simple stand-in for Module 1 validate_workout(profile, workout).

    Example (soft) rules:
      - critical if long run > 45% of weekly mileage
      - high if any single run > 65% of weekly mileage (provide an alternative)
      - otherwise safe
    """
    weekly = float(profile.get("weekly_mileage", 0.0) or 0.0)
    dist = float(workout.get("distance", 0.0) or 0.0)
    wtype = workout.get("type", "")

    if weekly > 0 and wtype == "long run" and dist > 0.45 * weekly:
        return {"safe": False, "severity": "critical"}

    if weekly > 0 and dist > 0.65 * weekly:
        alt_dist = max(1.0, 0.55 * weekly)
        return {
            "safe": False,
            "severity": "high",
            "alternative": {
                "type": workout.get("type", "easy"),
                "distance": alt_dist,
                "terrain": workout.get("terrain", "road"),
            },
        }

    return {"safe": True}


# ----------------------------
# Robust plan summarizer
# ----------------------------
def _first_key(d: dict, keys: list[str]):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _to_float(x):
    try:
        return float(x)
    except Exception:
        return None


def _flatten_workouts(maybe_workouts: Any) -> list[dict]:
    """
    Attempts to normalize many possible schemas into a flat list[dict] workouts.
    Handles:
      - list[workout_dict]
      - list[list[workout_dict]] (days)
      - list[day_dict with "workouts"]
      - dict with "workouts"/"days"/"sessions"/etc
    """
    if maybe_workouts is None:
        return []

    # If someone passed a dict week object by accident
    if isinstance(maybe_workouts, dict):
        for k in ("workouts", "days", "sessions", "week"):
            if k in maybe_workouts:
                return _flatten_workouts(maybe_workouts[k])
        return []

    if not isinstance(maybe_workouts, list):
        return []

    if not maybe_workouts:
        return []

    first = maybe_workouts[0]

    # Already list[dict] workouts
    if isinstance(first, dict) and ("type" in first or "distance" in first):
        return [w for w in maybe_workouts if isinstance(w, dict)]

    # list[list[dict]] days -> flatten
    if isinstance(first, list):
        flat: list[dict] = []
        for day in maybe_workouts:
            if isinstance(day, list):
                flat.extend([w for w in day if isinstance(w, dict)])
        return flat

    # list[day_dict] each has "workouts"
    if isinstance(first, dict) and "workouts" in first:
        flat = []
        for day in maybe_workouts:
            if isinstance(day, dict):
                flat.extend(day.get("workouts", []) or [])
        return [w for w in flat if isinstance(w, dict)]

    return []


def print_weekly_instructions(plan: list[dict]) -> None:
    print("\n=== What to do each week ===")
    for week in plan:
        if not isinstance(week, dict):
            continue

        wk = week.get("week") or week.get("week_number") or week.get("wk") or "?"
        total = week.get("weekly_total")
        if total is None:
            total = week.get("total_miles")
        if total is None:
            # fallback: compute from workouts
            total = sum(float(w.get("distance", 0) or 0) for w in (week.get("workouts") or []))

        long_run = week.get("long_run")
        workouts = week.get("workouts") or []

        total_str = f"{float(total):.1f}" if total is not None else "?"
        lr_str = f"{float(long_run):.1f}" if long_run is not None else "—"

        print(f"\nWeek {wk} — total {total_str} mi (long run {lr_str} mi)")
        for w in workouts:
            day = w.get("day", "Day")
            wtype = w.get("type", "workout")
            dist = w.get("distance", "?")
            terr = w.get("terrain", "road")
            # nice formatting
            dist_str = f"{float(dist):.1f}" if isinstance(dist, (int, float)) else str(dist)
            print(f"  - {day}: {wtype} — {dist_str} mi ({terr})")

# ----------------------------
# Main demo
# ----------------------------
def parse_beam_width(x: str) -> int | None:
    x = x.strip().lower()
    if x in ("none", "null", "unlimited", "inf", "infinite"):
        return None
    return int(x)

def main():
    total_weeks = 7
    current_miles = 15.0
    days_per_week = 4
    experience = "beginner"
    terrain = ["road", "trail"]
    beam_width = 10
    max_nodes = 100_000

    start = TrainingState.create_start(
        total_weeks=total_weeks,
        current_weekly_miles=current_miles,
        days_per_week=days_per_week,
        experience=experience,
        available_terrain=terrain,
    )

    result = a_star_search(
        start,
        max_nodes=max_nodes,
        beam_width=beam_width,
    )

    print("success:", result["success"])
    print("rationale:", result["rationale"])
    print_weekly_instructions(result["plan"])



if __name__ == "__main__":
    main()


"""
If you want beam_width=None to mean "no pruning", make sure your a_star_search
handles it. In your search loop, replace:

    current_beam = next_beam[:beam_width]

with:

    current_beam = next_beam if beam_width is None else next_beam[:beam_width]

and change the signature to:

    beam_width: int | None = 10
"""
