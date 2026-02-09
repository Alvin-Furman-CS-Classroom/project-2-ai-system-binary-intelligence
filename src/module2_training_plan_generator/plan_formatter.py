from __future__ import annotations

from typing import Any, Dict, List, Tuple


WeekPlan = Dict[str, Any]


def add_rationale(plan: List[WeekPlan], inputs: Dict[str, Any]) -> str:
    weeks = len(plan)
    if weeks == 0:
        return "No plan generated."
    peak_weekly = max(w.get("weekly_total", 0) for w in plan)
    peak_long = max(w.get("long_run", 0) for w in plan)
    terrains = inputs.get("available_terrain", [])
    return (
        f"{weeks}-week buildup targeting steady mileage progression with periodic cutbacks, "
        f"peaking around {peak_weekly:.1f} miles/week and a {peak_long:.1f}-mile long run. "
        f"Terrain options used: {', '.join(terrains) if terrains else 'road'}."
    )


def format_plan(plan_so_far: Tuple[WeekPlan, ...], inputs: Dict[str, Any]) -> Dict[str, Any]:
    plan = list(plan_so_far)
    return {
        "plan": plan,
        "rationale": add_rationale(plan, inputs),
    }
