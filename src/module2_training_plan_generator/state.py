from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


WeekPlan = Dict[str, Any]

@dataclass(frozen=True)
class TrainingState:
    #current week number
    week_idx: int
    #total number of weeks in the plan
    weeks_total: int

    #previous week's mileage, used for progression rules
    last_week_miles: float
    #current week's total mileage
    weekly_miles: float
    #current week's long run distance
    long_run: float

    # recent terrain usage(trail, road, track)
    terrain_hist: Tuple[Tuple[str, int], ...] = field(default_factory=tuple)

    # complete history of plan generated so far, used for rationale and terrain_hist reconstruction
    plan_so_far: Tuple[WeekPlan, ...] = field(default_factory=tuple)


#create hashtable idenfier for duduplication
def state_key(s: TrainingState) -> Tuple:
    return (
        s.week_idx,
        round(s.weekly_miles, 1),
        round(s.long_run, 1),
        round(s.last_week_miles, 1),
        s.terrain_hist,
    )


def _update_terrain_hist(prev: Tuple[Tuple[str, int], ...], week_plan: WeekPlan, window_weeks: int = 3) -> Tuple[Tuple[str, int], ...]:
    """
    Maintain compact terrain counts across a short window.
    We store (terrain,count) pairs sorted for stable hashing.
    Simple approach: recompute counts over last `window_weeks` week plans.
    """
    # prev is not enough to reconstruct exact last N weeks, so we recompute in apply_week_plan
    # using plan_so_far. This helper is kept for clarity; actual logic in apply_week_plan.
    return prev


def apply_week_plan(prev: TrainingState, week_plan: WeekPlan, terrain_window_weeks: int = 3) -> TrainingState:
    
    new_plan = prev.plan_so_far + (week_plan,)

    # Recompute terrain counts across last N weeks in plan_so_far (including this one)
    recent = list(new_plan[-terrain_window_weeks:])
    counts: Dict[str, int] = {}
    for w in recent:
        for wo in w.get("workouts", []):
            t = wo.get("terrain")
            if t:
                counts[t] = counts.get(t, 0) + 1

    terrain_hist = tuple(sorted(counts.items(), key=lambda x: x[0]))

    return TrainingState(
        week_idx=prev.week_idx + 1,
        weeks_total=prev.weeks_total,
        last_week_miles=float(prev.weekly_miles),
        weekly_miles=float(week_plan.get("weekly_total", prev.weekly_miles)),
        long_run=float(week_plan.get("long_run", prev.long_run)),
        terrain_hist=terrain_hist,
        plan_so_far=new_plan,
    )
