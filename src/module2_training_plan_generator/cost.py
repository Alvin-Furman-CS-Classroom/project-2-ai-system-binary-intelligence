from __future__ import annotations

from typing import Any, Dict, Tuple


Inputs = Dict[str, Any]
WeekPlan = Dict[str, Any]

def penalty_progression(prev_weekly: float, new_weekly: float, experience: str = "beginner") -> float:
    if prev_weekly <= 0:
        return 0.0
    growth = (new_weekly - prev_weekly) / prev_weekly

    # Experience-based thresholds and penalties
    exp = (experience or "beginner").lower()
    if exp == "beginner":
        # Beginners: conservative, allow up to 8% growth
        threshold = 0.08
        penalty_multiplier = 80.0  # Higher penalty for aggressive progression
    elif exp == "intermediate":
        # Intermediate: moderate, allow up to 10% growth
        threshold = 0.10
        penalty_multiplier = 50.0
    else:  # advanced
        # Advanced: aggressive, allow up to 12% growth
        threshold = 0.12
        penalty_multiplier = 30.0

    return penalty_multiplier * max(0.0, growth - threshold)

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
    experience = inputs.get("experience", "beginner")

    cost = 0.0
    cost += penalty_progression(float(prev_state.weekly_miles), new_weekly, experience)
    cost += penalty_long_run_fraction(new_weekly, new_long)
    cost += penalty_beginner_quality_overload(experience, next_week_plan)
    cost += penalty_terrain_monotony(getattr(next_state, "terrain_hist", tuple()))
    return cost


def _targets(inputs: Inputs) -> Dict[str, float]:
    goal = (inputs.get("goal", "") or "").lower()
    experience = (inputs.get("experience", "beginner") or "beginner").lower()

    # Base targets by goal
    if "marathon" in goal:
        base_long, base_weekly = 20.0, 40.0
    elif "half" in goal:
        base_long, base_weekly = 12.0, 28.0
    else:
        base_long, base_weekly = 10.0, 25.0

    # Adjust targets based on experience level
    if experience == "beginner":
        # Beginners: more conservative targets (80% of base)
        return {"peak_long": base_long * 0.80, "peak_weekly": base_weekly * 0.80}
    elif experience == "intermediate":
        # Intermediate: standard targets (90% of base)
        return {"peak_long": base_long * 0.90, "peak_weekly": base_weekly * 0.90}
    else:  # advanced
        # Advanced: full targets
        return {"peak_long": base_long, "peak_weekly": base_weekly}


def heuristic(state: Any, inputs: Inputs) -> float:
    """∂
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
