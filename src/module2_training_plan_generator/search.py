from __future__ import annotations

import heapq
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from .cost import heuristic, step_cost
from .plan_formatter import format_plan
from .state import TrainingState, apply_week_plan, state_key
from .templates import generate_week_candidates


Inputs = Dict[str, Any]
WeekPlan = Dict[str, Any]
SafetyValidator = Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]  # (profile, proposed_workout) -> assessment


@dataclass
class SearchResult:
    output: Dict[str, Any]
    total_cost: float
    expanded_nodes: int


def _weeks_until(race_date_str: str) -> int:
    # Expect YYYY-MM-DD
    rd = datetime.strptime(race_date_str, "%Y-%m-%d").date()
    today = date.today()
    delta_days = (rd - today).days
    # Minimum 1 week
    return max(1, (delta_days + 6) // 7)


def _is_goal(state: TrainingState) -> bool:
    # Goal when we've planned all required weeks
    return state.week_idx >= state.weeks_total


def _validate_and_repair_week(
    runner_profile: Dict[str, Any],
    week_plan: WeekPlan,
    safety_validator: Optional[SafetyValidator],
) -> Optional[WeekPlan]:
    if safety_validator is None:
        return week_plan

    repaired = {"week": week_plan["week"], "workouts": [], "weekly_total": 0.0, "long_run": week_plan.get("long_run", 0.0)}

    for wo in week_plan.get("workouts", []):
        assessment = safety_validator(runner_profile, wo)
        if assessment.get("safe", True):
            repaired["workouts"].append(wo)
        else:
            alt = assessment.get("alternative")
            if not alt:
                return None
            # Keep same day if missing in alt
            if "day" not in alt and "day" in wo:
                alt["day"] = wo["day"]
            repaired["workouts"].append(alt)

    repaired["weekly_total"] = round(sum(float(w["distance"]) for w in repaired["workouts"]), 1)
    repaired["long_run"] = round(
        max((float(w["distance"]) for w in repaired["workouts"] if w.get("type") == "long run"), default=repaired.get("long_run", 0.0)),
        1,
    )
    return repaired


def astar_plan(
    inputs: Inputs,
    runner_profile: Optional[Dict[str, Any]] = None,
    safety_validator: Optional[SafetyValidator] = None,
    max_expansions: int = 50_000,
) -> SearchResult:
    """
    Generate a training plan using A* search.

    inputs must include:
      - goal, race_date (YYYY-MM-DD), days_per_week, current_weekly_miles, experience, available_terrain

    runner_profile is passed to Module 1 validator if provided.
    """
    runner_profile = runner_profile or {}

    weeks_total = _weeks_until(inputs["race_date"])

    start_weekly = float(inputs.get("current_weekly_miles", 10.0))
    start_long = max(4.0, round(start_weekly * 0.35, 1))

    start = TrainingState(
        week_idx=0,
        weeks_total=weeks_total,
        last_week_miles=start_weekly,
        weekly_miles=start_weekly,
        long_run=start_long,
        terrain_hist=tuple(),
        plan_so_far=tuple(),
    )

    # Priority queue: (f, tie, state)
    open_heap: List[Tuple[float, int, TrainingState]] = []
    tie = 0

    g_score: Dict[Tuple, float] = {state_key(start): 0.0}
    heapq.heappush(open_heap, (heuristic(start, inputs), tie, start))

    best_final: Optional[TrainingState] = None
    best_final_cost = float("inf")
    expanded = 0

    while open_heap and expanded < max_expansions:
        _, _, cur = heapq.heappop(open_heap)
        cur_key = state_key(cur)

        if _is_goal(cur):
            cur_cost = g_score.get(cur_key, float("inf"))
            if cur_cost < best_final_cost:
                best_final = cur
                best_final_cost = cur_cost
            continue

        expanded += 1

        candidates = generate_week_candidates(cur, inputs)
        for wp in candidates:
            wp2 = _validate_and_repair_week(runner_profile, wp, safety_validator)
            if wp2 is None:
                continue

            nxt = apply_week_plan(cur, wp2)
            nxt_key = state_key(nxt)

            step = step_cost(cur, wp2, inputs, nxt)
            tentative_g = g_score[cur_key] + step

            if tentative_g < g_score.get(nxt_key, float("inf")):
                g_score[nxt_key] = tentative_g
                tie += 1
                f = tentative_g + heuristic(nxt, inputs)
                heapq.heappush(open_heap, (f, tie, nxt))

    if best_final is None:
        # Fallback: greedy build (take lowest-cost candidate each week)
        cur = start
        for _ in range(weeks_total):
            cands = generate_week_candidates(cur, inputs)
            best_wp = None
            best_step = float("inf")
            for wp in cands:
                wp2 = _validate_and_repair_week(runner_profile, wp, safety_validator)
                if wp2 is None:
                    continue
                nxt = apply_week_plan(cur, wp2)
                sc = step_cost(cur, wp2, inputs, nxt)
                if sc < best_step:
                    best_step = sc
                    best_wp = wp2
            if best_wp is None:
                break
            cur = apply_week_plan(cur, best_wp)
        output = format_plan(cur.plan_so_far, inputs)
        return SearchResult(output=output, total_cost=float("inf"), expanded_nodes=expanded)

    output = format_plan(best_final.plan_so_far, inputs)
    return SearchResult(output=output, total_cost=best_final_cost, expanded_nodes=expanded)
