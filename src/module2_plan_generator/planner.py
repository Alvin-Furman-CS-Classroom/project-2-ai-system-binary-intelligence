"""
Main entry point for the training plan generator.

This module provides the public-facing functions that external code calls.
It orchestrates input validation, state creation, A* search, and result
formatting, analogous to how ``validator.py`` works in Module 1.

Example:
    >>> from module2_plan_generator.planner import generate_plan
    >>> config = {
    ...     "goal": "complete marathon",
    ...     "race_date": "2025-10-15",
    ...     "days_per_week": 4,
    ...     "current_weekly_miles": 15,
    ...     "experience": "beginner",
    ...     "available_terrain": ["road", "trail"],
    ... }
    >>> result = generate_plan(config)
    >>> result["success"]
    True
    >>> len(result["plan"]) > 0
    True
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

from .input_validation import validate_planner_input
from .states import TrainingState
from .search import a_star_search


def generate_plan(
    config: dict[str, Any],
    validate_fn: Callable | None = None,
    runner_profile: dict | None = None,
    max_nodes: int = 50_000,
) -> dict[str, Any]:
    """Generate a complete marathon training plan using A* search.

    This is the main public function. It validates input, sets up the
    search, and returns a structured plan.

    Args:
        config: Planner configuration dict with keys:
            - ``goal`` (str): Race goal, e.g. "complete marathon".
            - ``race_date`` (str): ISO date string (YYYY-MM-DD).
            - ``days_per_week`` (int): Training days per week (3-6).
            - ``current_weekly_miles`` (float): Current base mileage.
            - ``experience`` (str): "beginner", "intermediate", or
              "advanced".
            - ``available_terrain`` (list[str]): Terrain options.
        validate_fn: Optional reference to Module 1's
            ``validate_workout(profile, workout)`` function. When
            provided, every candidate workout is safety-checked.
        runner_profile: Runner profile dict for Module 1 validation.
        max_nodes: Maximum search nodes to expand (safety limit).

    Returns:
        A dict with keys:
        - ``success`` (bool): Whether a plan was generated.
        - ``plan`` (list[dict]): List of week dicts, each with ``week``,
          ``total_miles``, and ``workouts``.
        - ``total_weeks`` (int): Number of weeks in the plan.
        - ``total_penalty`` (float): Total constraint violation score.
        - ``search_stats`` (dict): Nodes explored/generated, algorithm.
        - ``rationale`` (str): Human-readable plan description.
        - ``errors`` (list[str]): Validation errors (if any).

    Example:
        >>> result = generate_plan({
        ...     "goal": "complete marathon",
        ...     "race_date": "2025-12-01",
        ...     "days_per_week": 4,
        ...     "current_weekly_miles": 20,
        ...     "experience": "intermediate",
        ...     "available_terrain": ["road", "track", "trail"],
        ... })
        >>> result["success"]
        True
    """
    # Step 1: Validate input.
    errors = validate_planner_input(config)
    if errors:
        return {
            "success": False,
            "plan": [],
            "total_weeks": 0,
            "total_penalty": float("inf"),
            "search_stats": {},
            "rationale": "Input validation failed.",
            "errors": errors,
            "advisory_notes": [],
        }

    # Step 2: Compute weeks until race.
    race_date = _parse_race_date(config["race_date"])
    today = date.today()
    total_weeks = (race_date - today).days // 7

    # Step 2b: Tier 1 pre-check — if runner has critical safety issue, do not generate plan.
    if validate_fn and runner_profile and total_weeks > 0:
        try:
            probe = validate_fn(
                runner_profile,
                {"type": "easy run", "distance": 2.0, "terrain": (config["available_terrain"] or ["road"])[0]},
            )
            if not probe.get("safe", True) and probe.get("severity") == "critical":
                return {
                    "success": False,
                    "plan": [],
                    "total_weeks": total_weeks,
                    "total_penalty": float("inf"),
                    "search_stats": {},
                    "rationale": "Doctor's clearance required before a training plan can be generated.",
                    "errors": ["Doctor's clearance required before a training plan can be generated."],
                    "advisory_notes": [],
                }
        except Exception:
            # If Module 1 fails on pre-check, proceed; search will handle per-workout validation.
            pass

    # Step 3: Create start state.
    start = TrainingState.create_start(
        total_weeks=total_weeks,
        current_weekly_miles=float(config["current_weekly_miles"]),
        days_per_week=config["days_per_week"],
        experience=config["experience"].lower(),
        available_terrain=config["available_terrain"],
    )

    # Step 4: Run A* search.
    search_result = a_star_search(
        start=start,
        validate_fn=validate_fn,
        runner_profile=runner_profile,
    )

    # Step 5: Format and return result.
    out = {
        "success": search_result["success"],
        "plan": search_result["plan"],
        "total_weeks": total_weeks,
        "total_penalty": search_result["total_penalty"],
        "search_stats": {
            "nodes_explored": search_result["nodes_explored"],
            "nodes_generated": search_result["nodes_generated"],
            "algorithm": search_result["algorithm"],
        },
        "rationale": search_result["rationale"],
        "errors": [],
    }
    # Tier 2 advisories: one pass over the plan to collect medium-severity notes.
    if search_result["success"] and validate_fn and runner_profile and search_result["plan"]:
        out["advisory_notes"] = _collect_advisory_notes(
            search_result["plan"], validate_fn, runner_profile, config
        )
    else:
        out["advisory_notes"] = []
    return out


def generate_plan_detailed(
    config: dict[str, Any],
    validate_fn: Callable | None = None,
    runner_profile: dict | None = None,
    max_nodes: int = 50_000,
) -> dict[str, Any]:
    """Generate a plan with additional debug and analysis information.

    Same as ``generate_plan`` but includes per-week penalty breakdowns
    and search statistics useful for development and testing.

    Args:
        config: Same as ``generate_plan``.
        validate_fn: Same as ``generate_plan``.
        runner_profile: Same as ``generate_plan``.
        max_nodes: Same as ``generate_plan``.

    Returns:
        Same as ``generate_plan`` plus:
        - ``weekly_analysis`` (list[dict]): Per-week penalty breakdown.
    """
    result = generate_plan(config, validate_fn, runner_profile, max_nodes)

    if not result["success"]:
        result["weekly_analysis"] = []
        return result

    # Compute per-week analysis.
    from .constraints import compute_week_penalty

    plan = result["plan"]
    analysis = []
    prev_miles = float(config["current_weekly_miles"])
    miles_history: list[float] = []
    terrain = config["available_terrain"]
    total_weeks = result["total_weeks"]

    for week_data in plan:
        week_num = week_data["week"]
        workouts = week_data["workouts"]
        weekly_miles = week_data["total_miles"]

        penalty, violations = compute_week_penalty(
            workouts=workouts,
            weekly_miles=weekly_miles,
            previous_miles=prev_miles,
            week_number=week_num,
            total_weeks=total_weeks,
            days_per_week=config["days_per_week"],
            available_terrain=terrain,
            weekly_miles_history=miles_history,
            experience=config.get("experience", "beginner"),
        )

        analysis.append({
            "week": week_num,
            "miles": weekly_miles,
            "penalty": penalty,
            "violations": violations,
            "miles_change_pct": (
                round((weekly_miles - prev_miles) / prev_miles * 100, 1)
                if prev_miles > 0 else 0
            ),
        })

        prev_miles = weekly_miles
        miles_history.append(weekly_miles)

    result["weekly_analysis"] = analysis
    return result


def _collect_advisory_notes(
    plan: list[dict],
    validate_fn: Callable,
    runner_profile: dict,
    config: dict[str, Any],
) -> list[str]:
    """One pass over the plan: collect unique medium-severity (Tier 2) reasons."""
    notes: list[str] = []
    seen: set[str] = set()
    prev_miles = float(config.get("current_weekly_miles", 0))
    for week_data in plan:
        profile = {
            **runner_profile,
            "weekly_mileage": prev_miles,
            "days_trained_this_week": len(week_data.get("workouts", [])),
            "rest_days_this_week": 7 - len(week_data.get("workouts", [])),
        }
        for w in week_data.get("workouts", []):
            try:
                r = validate_fn(profile, {"type": w["type"], "distance": w["distance"], "terrain": w["terrain"]})
                if not r.get("safe", True) and r.get("severity") == "medium":
                    reason = r.get("reason", "Preparation advisory.")
                    if reason not in seen:
                        seen.add(reason)
                        notes.append(reason)
            except Exception:
                pass
        prev_miles = week_data.get("total_miles", prev_miles)
    return notes


def _parse_race_date(value: Any) -> date:
    """Parse race_date to a date object."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.strptime(value, "%Y-%m-%d").date()
