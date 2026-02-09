from __future__ import annotations

from typing import Any, Dict, Tuple


Inputs = Dict[str, Any]
WeekPlan = Dict[str, Any]

def penalty_progression(prev_weekly: float, new_weekly: float) -> float:
    if prev_weekly <= 0:
        return 0.0
    growth = (new_weekly - prev_weekly) / prev_weekly
    # Allow up to 10% growth, penalize beyond
    return 50.0 * max(0.0, growth - 0.10)

def penalty_long_run_fraction(weekly: float, long_run: float) -> float:
    if weekly <= 0:
        return 0.0
    frac = long_run / weekly
    # Penalize if long run > 55% of weekly
    return 40.0 * max(0.0, frac - 0.55)

def penalty_terrain_monotony(terrain_hist: Tuple[Tuple[str, int], ...]) -> float:
    total = sum(c for _, c in terrain_hist)
    if total == 0:
        return 0.0
    dominant = max(c for _, c in terrain_hist) / total
    # penalize if one terrain dominates > 60%
    return 10.0 * max(0.0, dominant - 0.60)


def penalty_beginner_quality_overload(experience: str, week_plan: WeekPlan) -> float:
    exp = (experience or "").lower()
    if exp != "beginner":
        return 0.0
    quality = sum(1 for w in week_plan.get("workouts", []) if w.get("type") in {"tempo", "interval", "intervals"})
    return 30.0 * max(0, quality - 1)


def step_cost(prev_state: Any, next_week_plan: WeekPlan, inputs: Inputs, next_state: Any) -> float:
    new_weekly = float(next_week_plan.get("weekly_total", prev_state.weekly_miles))
    new_long = float(next_week_plan.get("long_run", prev_state.long_run))

    cost = 0.0
    cost += penalty_progression(float(prev_state.weekly_miles), new_weekly)
    cost += penalty_long_run_fraction(new_weekly, new_long)
    cost += penalty_beginner_quality_overload(inputs.get("experience", "beginner"), next_week_plan)
    cost += penalty_terrain_monotony(getattr(next_state, "terrain_hist", tuple()))
    return cost


def _targets(inputs: Inputs) -> Dict[str, float]:
    goal = (inputs.get("goal", "") or "").lower()
    if "marathon" in goal:
        return {"peak_long": 20.0, "peak_weekly": 40.0}
    if "half" in goal:
        return {"peak_long": 12.0, "peak_weekly": 28.0}
    return {"peak_long": 10.0, "peak_weekly": 25.0}


def heuristic(state: Any, inputs: Inputs) -> float:
    """
    A simple guiding heuristic: remaining gap to target peaks.
    """
    t = _targets(inputs)
    h = 0.0
    h += 5.0 * max(0.0, t["peak_long"] - float(state.long_run))
    h += 2.0 * max(0.0, t["peak_weekly"] - float(state.weekly_miles))
    # If we are late in the plan and still far from peaks, penalize more
    weeks_left = int(state.weeks_total - state.week_idx)
    if weeks_left <= 4:
        h += 10.0 * max(0.0, (t["peak_long"] - float(state.long_run)) / 2.0)
    return h
