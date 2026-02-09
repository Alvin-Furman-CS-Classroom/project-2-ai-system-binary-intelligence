from __future__ import annotations

from typing import Any, Dict, List, Tuple


Inputs = Dict[str, Any]
WeekPlan = Dict[str, Any]


DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def mileage_options(last_week_miles: float, week_idx: int) -> List[float]:
    """
    Keep branching small: 3 growth options + occasional cutback.
    """
    opts = [
        last_week_miles * 1.05,
        last_week_miles * 1.08,
        last_week_miles * 1.10,
    ]
    # Cutback every 4th week (week_idx is 0-based for first planned week)
    if (week_idx + 1) % 4 == 0:
        opts.append(last_week_miles * 0.80)

    # Round for stability
    return sorted({round(x, 1) for x in opts})


def long_run_options(prev_long: float, week_idx: int, goal: str) -> List[float]:
    """
    Long run progression options. Cap depends on goal.
    """
    goal = goal.lower().strip()
    if "marathon" in goal:
        cap = 20.0
    elif "half" in goal:
        cap = 12.0
    else:
        cap = max(10.0, prev_long + 2.0)

    opts = [min(prev_long + 1.0, cap), min(prev_long + 2.0, cap)]

    # Cutback long run on cutback weeks
    if (week_idx + 1) % 4 == 0:
        opts.append(max(6.0, prev_long - 2.0))

    return sorted({round(x, 1) for x in opts})


def _rotate_terrains(available: List[str], count: int, start_idx: int = 0) -> List[str]:
    if not available:
        return ["road"] * count
    out = []
    for i in range(count):
        out.append(available[(start_idx + i) % len(available)])
    return out


def build_week_plan(
    week_number: int,
    target_weekly: float,
    target_long: float,
    days_per_week: int,
    available_terrain: List[str],
    experience: str,
) -> WeekPlan:
    """
    Build a reasonable week blueprint:
    - 1 long run
    - 0–1 quality day (tempo) depending on experience and phase
    - remaining easy runs
    - remaining days are rest
    """
    days_per_week = max(1, min(7, int(days_per_week)))
    run_days = DAYS[:days_per_week]  # simplistic: first N days are run days

    # Decide quality day
    exp = (experience or "").lower()
    quality = False
    if exp in {"intermediate", "advanced"}:
        quality = True
    elif exp == "beginner":
        # beginners: introduce quality lightly later; caller can also gate this
        quality = week_number >= 5

    # Distances
    # Allocate remaining mileage after long run across other run days
    non_long_runs = days_per_week - 1
    if non_long_runs <= 0:
        # Only one run day: it's the long run
        workouts = [{"day": run_days[-1], "type": "long run", "distance": round(target_long, 1), "terrain": available_terrain[0] if available_terrain else "road"}]
        return {
            "week": week_number,
            "workouts": workouts,
            "weekly_total": round(target_long, 1),
            "long_run": round(target_long, 1),
        }

    remaining = max(0.0, target_weekly - target_long)

    # Quality day distance: small fraction of remaining
    quality_miles = 0.0
    if quality and non_long_runs >= 2:
        quality_miles = max(3.0, min(6.0, remaining * 0.35))
        remaining_after_quality = max(0.0, remaining - quality_miles)
        easy_days = non_long_runs - 1
    else:
        remaining_after_quality = remaining
        easy_days = non_long_runs

    easy_miles_each = remaining_after_quality / max(1, easy_days)
    easy_miles_each = max(2.0, easy_miles_each)

    # Build workouts list
    workouts: List[Dict[str, Any]] = []

    # Terrain rotation across run days (helps variety)
    terrains = _rotate_terrains(available_terrain, days_per_week, start_idx=(week_number - 1) % max(1, len(available_terrain)))

    # Add easy runs first
    idx = 0
    for _ in range(easy_days):
        workouts.append(
            {
                "day": run_days[idx],
                "type": "easy run",
                "distance": round(easy_miles_each, 1),
                "terrain": terrains[idx],
            }
        )
        idx += 1

    # Add quality run if applicable
    if quality and non_long_runs >= 2:
        workouts.append(
            {
                "day": run_days[idx],
                "type": "tempo",
                "distance": round(quality_miles, 1),
                "terrain": terrains[idx],
            }
        )
        idx += 1

    # Add long run on last run day
    workouts.append(
        {
            "day": run_days[-1],
            "type": "long run",
            "distance": round(target_long, 1),
            "terrain": terrains[-1],
        }
    )

    weekly_total = sum(float(w["distance"]) for w in workouts)
    return {
        "week": week_number,
        "workouts": workouts,
        "weekly_total": round(weekly_total, 1),
        "long_run": round(target_long, 1),
    }


def generate_week_candidates(state: Any, inputs: Inputs) -> List[WeekPlan]:
    """
    Given current state, produce a small list of candidate week plans.
    """
    goal = inputs.get("goal", "complete marathon")
    days_per_week = int(inputs.get("days_per_week", 4))
    experience = inputs.get("experience", "beginner")
    terrains = list(inputs.get("available_terrain", ["road"]))

    week_number = state.week_idx + 1  # 1-based for output

    mileage_opts = mileage_options(state.weekly_miles, state.week_idx)
    long_opts = long_run_options(state.long_run, state.week_idx, goal)

    candidates: List[WeekPlan] = []
    for mw in mileage_opts:
        for lr in long_opts:
            # Avoid long run being too large a fraction of weekly mileage
            if lr > mw * 0.55:
                continue
            candidates.append(
                build_week_plan(
                    week_number=week_number,
                    target_weekly=mw,
                    target_long=lr,
                    days_per_week=days_per_week,
                    available_terrain=terrains,
                    experience=experience,
                )
            )

    # Keep branching bounded
    candidates.sort(key=lambda wp: (wp["weekly_total"], wp["long_run"]))
    return candidates[:20]
