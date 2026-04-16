from __future__ import annotations

import heapq
from typing import Any

from .actions import generate_week_candidates
from .constraints import compute_week_penalty
from .heuristics import compute_heuristic
from .states import TrainingState


# Tie-breaking counter so heapq never compares TrainingState objects.
_counter = 0


def a_star_search(
    start: TrainingState,
    max_nodes: int = 100_000,
    beam_width: int = 10,
    validate_fn: Any = None,
    runner_profile: dict | None = None,
) -> dict:
    
    global _counter
    _counter = 0

    nodes_explored = 0
    nodes_generated = 0

    # Current frontier: (f_cost, counter, state).
    h_start = compute_heuristic(start)
    f_start = start.g_cost + h_start
    current_beam: list[tuple[float, int, TrainingState]] = [(f_start, _counter, start)]
    _counter += 1

    for depth in range(start.total_weeks):
        next_beam: list[tuple[float, int, TrainingState]] = []

        for _, _, state in current_beam:
            if state.is_goal():
                plan = state.recover_plan()
                return {
                    "success": True,
                    "plan": plan,
                    "total_penalty": state.g_cost,
                    "nodes_explored": nodes_explored,
                    "nodes_generated": nodes_generated,
                    "algorithm": "a_star",
                    "rationale": _build_rationale(state, nodes_explored),
                }

            nodes_explored += 1
            if nodes_explored >= max_nodes:
                break

            candidates = generate_week_candidates(state)
            for workouts, weekly_miles in candidates:
                if validate_fn and runner_profile:
                    workouts = _validate_workouts(workouts, validate_fn, runner_profile, state)
                    if workouts is None:
                        continue
                    weekly_miles = sum(w["distance"] for w in workouts)

                week_number = state.week_number + 1
                penalty, violations = compute_week_penalty(
                    workouts=list(workouts),
                    weekly_miles=weekly_miles,
                    previous_miles=state.current_weekly_miles,
                    week_number=week_number,
                    total_weeks=state.total_weeks,
                    days_per_week=state.days_per_week,
                    available_terrain=list(state.available_terrain),
                    weekly_miles_history=list(state.weekly_miles_history),
                    experience=state.experience,
                )
                successor = state.add_week(
                    workouts=tuple(workouts) if isinstance(workouts, list) else workouts,
                    week_miles=weekly_miles,
                    week_penalty=penalty,
                )
                nodes_generated += 1
                h = compute_heuristic(successor)
                next_beam.append((successor.g_cost + h, _counter, successor))
                _counter += 1

        if not next_beam:
            break
        next_beam.sort(key=lambda x: x[0])
        current_beam = next_beam[:beam_width]

    for _, _, state in current_beam:
        if state.is_goal():
            plan = state.recover_plan()
            return {
                "success": True,
                "plan": plan,
                "total_penalty": state.g_cost,
                "nodes_explored": nodes_explored,
                "nodes_generated": nodes_generated,
                "algorithm": "a_star",
                "rationale": _build_rationale(state, nodes_explored),
            }

    best_candidates = [s for _, _, s in current_beam if s.week_number == start.total_weeks]
    if best_candidates:
        best = min(best_candidates, key=lambda s: s.g_cost)
        plan = best.recover_plan()
        return {
            "success": True,
            "plan": plan,
            "total_penalty": best.g_cost,
            "nodes_explored": nodes_explored,
            "nodes_generated": nodes_generated,
            "algorithm": "a_star",
            "rationale": _build_rationale(best, nodes_explored),
        }

    # Greedy fallback: build a plan by picking lowest-cost week at each step
    fallback_state, fallback_explored = _greedy_build(
        start, validate_fn, runner_profile
    )
    if fallback_state is not None:
        plan = fallback_state.recover_plan()
        return {
            "success": True,
            "plan": plan,
            "total_penalty": fallback_state.g_cost,
            "nodes_explored": nodes_explored + fallback_explored,
            "nodes_generated": nodes_generated,
            "algorithm": "a_star",
            "rationale": _build_rationale(fallback_state, nodes_explored + fallback_explored, fallback=True),
        }

    return {
        "success": False,
        "plan": [],
        "total_penalty": float("inf"),
        "nodes_explored": nodes_explored,
        "nodes_generated": nodes_generated,
        "algorithm": "a_star",
        "rationale": f"Search exhausted after exploring {nodes_explored} states.",
    }


def _validate_workouts(
    workouts: tuple[dict, ...],
    validate_fn: Any,
    runner_profile: dict,
    state: TrainingState,
) -> tuple[dict, ...] | None:

    validated: list[dict] = []
    for w in workouts:
        profile = {
            **runner_profile,
            "weekly_mileage": state.current_weekly_miles,
            "days_trained_this_week": len(workouts),
            "rest_days_this_week": 7 - len(workouts),
        }
        workout_input = {"type": w["type"], "distance": w["distance"], "terrain": w["terrain"]}
        try:
            result = validate_fn(profile, workout_input)
        except Exception:
            validated.append(w)
            continue

        if result.get("safe", True):
            validated.append(w)
            continue

        severity = result.get("severity", "high")
        if severity == "critical":
            return None
        if severity == "high" and result.get("alternative"):
            alt = result["alternative"]
            validated.append({
                "day": w.get("day"),
                "type": alt.get("type", w["type"]),
                "distance": alt.get("distance", w["distance"]),
                "terrain": alt.get("terrain", w["terrain"]),
            })
            continue
        if severity == "high":
            if w.get("type") == "long run":
                return None
            continue
        if severity == "medium":
            validated.append(w)
            continue
        if w.get("type") == "long run":
            return None
    return tuple(validated) if validated else None


def _greedy_build(
    start: TrainingState,
    validate_fn: Any,
    runner_profile: dict | None,
) -> tuple[TrainingState | None, int]:
    """Build a plan greedily by picking the lowest-cost valid week at each step.

    Returns (goal_state, nodes_expanded) or (None, 0) if no valid plan could be built.
    """
    state = start
    expanded = 0
    for _ in range(start.total_weeks):
        candidates = generate_week_candidates(state)
        best_successor = None
        best_penalty = float("inf")
        for workouts, weekly_miles in candidates:
            if validate_fn and runner_profile:
                workouts = _validate_workouts(workouts, validate_fn, runner_profile, state)
                if workouts is None:
                    continue
                weekly_miles = sum(w["distance"] for w in workouts)
            week_number = state.week_number + 1
            penalty, _ = compute_week_penalty(
                workouts=list(workouts),
                weekly_miles=weekly_miles,
                previous_miles=state.current_weekly_miles,
                week_number=week_number,
                total_weeks=state.total_weeks,
                days_per_week=state.days_per_week,
                available_terrain=list(state.available_terrain),
                weekly_miles_history=list(state.weekly_miles_history),
                experience=state.experience,
            )
            expanded += 1
            if penalty < best_penalty:
                best_penalty = penalty
                best_successor = (workouts, weekly_miles)
        if best_successor is None:
            return None, expanded
        workouts, weekly_miles = best_successor
        state = state.add_week(
            workouts=tuple(workouts) if isinstance(workouts, list) else workouts,
            week_miles=weekly_miles,
            week_penalty=best_penalty,
        )
    return state, expanded


def _build_rationale(
    goal_state: TrainingState, nodes_explored: int, fallback: bool = False
) -> str:
    """Build a human-readable description of the plan found.

    Uses partner-style wording: buildup, peaking at X miles/week and Y-mile long run,
    terrain options used.
    """
    total_weeks = goal_state.total_weeks
    peak_miles = max(goal_state.weekly_miles_history) if goal_state.weekly_miles_history else 0
    peak_long = 0.0
    for week in goal_state.plan_weeks:
        for w in week:
            if w.get("type") == "long run":
                peak_long = max(peak_long, float(w.get("distance", 0)))
    terrain_used = set()
    for week in goal_state.plan_weeks:
        for w in week:
            terrain_used.add(w.get("terrain", "unknown"))
    terrain_str = ", ".join(sorted(terrain_used)) if terrain_used else "road"

    rationale = (
        f"{total_weeks}-week buildup targeting steady mileage progression with periodic cutbacks, "
        f"peaking around {peak_miles:.1f} miles/week and a {peak_long:.1f}-mile long run. "
        f"Terrain options used: {terrain_str}."
    )
    if fallback:
        rationale += (
            f" A* did not find a goal state; plan generated by greedy fallback "
            f"({nodes_explored} nodes explored). Total penalty: {goal_state.g_cost:.0f}."
        )
    else:
        rationale += (
            f" A* explored {nodes_explored} states to find the lowest-penalty plan "
            f"(total penalty: {goal_state.g_cost:.0f})."
        )
    return rationale
