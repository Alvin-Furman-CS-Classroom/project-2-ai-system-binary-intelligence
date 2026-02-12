"""
Action generation for the training plan search.

Given a search state, this module generates the possible successor states
by creating candidate weekly workout combinations. Each combination is a
set of workouts assigned to training days with specific types, distances,
and terrain assignments.

To keep the branching factor manageable, this module uses a template-based
approach: it defines a few workout-mix templates per experience level,
then varies terrain assignments across them.

Example:
    >>> from module2_plan_generator.states import TrainingState
    >>> from module2_plan_generator.actions import generate_week_candidates
    >>> state = TrainingState.create_start(
    ...     total_weeks=16, current_weekly_miles=15.0,
    ...     days_per_week=4, experience="beginner",
    ...     available_terrain=["road", "trail"],
    ... )
    >>> candidates = generate_week_candidates(state)
    >>> len(candidates) > 0
    True
"""

from __future__ import annotations

import itertools
from typing import Any

from .states import TrainingState


# ---------------------------------------------------------------------------
# Day assignment order (workouts are placed on these days)
# ---------------------------------------------------------------------------

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ---------------------------------------------------------------------------
# Workout templates by experience level and days per week
# ---------------------------------------------------------------------------
# Each template is a list of (workout_type, distance_fraction) tuples.
# distance_fraction is relative to the target weekly mileage.

_BEGINNER_TEMPLATES: dict[int, list[list[tuple[str, float]]]] = {
    3: [
        [("easy run", 0.30), ("easy run", 0.30), ("long run", 0.40)],
        [("easy run", 0.35), ("easy run", 0.25), ("long run", 0.40)],
    ],
    4: [
        [("easy run", 0.25), ("easy run", 0.20), ("easy run", 0.25), ("long run", 0.30)],
        [("easy run", 0.20), ("easy run", 0.25), ("easy run", 0.20), ("long run", 0.35)],
        [("easy run", 0.25), ("recovery run", 0.15), ("easy run", 0.25), ("long run", 0.35)],
    ],
    5: [
        [("easy run", 0.20), ("easy run", 0.20), ("easy run", 0.15),
         ("easy run", 0.20), ("long run", 0.25)],
        [("easy run", 0.20), ("recovery run", 0.10), ("easy run", 0.20),
         ("easy run", 0.20), ("long run", 0.30)],
    ],
    6: [
        [("easy run", 0.18), ("easy run", 0.15), ("easy run", 0.15),
         ("easy run", 0.15), ("easy run", 0.12), ("long run", 0.25)],
    ],
}

_INTERMEDIATE_TEMPLATES: dict[int, list[list[tuple[str, float]]]] = {
    3: [
        [("easy run", 0.30), ("tempo", 0.30), ("long run", 0.40)],
    ],
    4: [
        [("easy run", 0.25), ("tempo", 0.20), ("easy run", 0.20), ("long run", 0.35)],
        [("easy run", 0.20), ("intervals", 0.20), ("easy run", 0.25), ("long run", 0.35)],
    ],
    5: [
        [("easy run", 0.20), ("tempo", 0.18), ("easy run", 0.15),
         ("easy run", 0.17), ("long run", 0.30)],
        [("easy run", 0.20), ("easy run", 0.15), ("intervals", 0.18),
         ("easy run", 0.17), ("long run", 0.30)],
    ],
    6: [
        [("easy run", 0.15), ("tempo", 0.15), ("easy run", 0.15),
         ("recovery run", 0.10), ("easy run", 0.15), ("long run", 0.30)],
    ],
}

_ADVANCED_TEMPLATES: dict[int, list[list[tuple[str, float]]]] = {
    3: [
        [("tempo", 0.30), ("intervals", 0.25), ("long run", 0.45)],
    ],
    4: [
        [("easy run", 0.20), ("tempo", 0.20), ("intervals", 0.20), ("long run", 0.40)],
        [("easy run", 0.20), ("race pace", 0.20), ("easy run", 0.20), ("long run", 0.40)],
    ],
    5: [
        [("easy run", 0.15), ("tempo", 0.18), ("easy run", 0.15),
         ("intervals", 0.17), ("long run", 0.35)],
    ],
    6: [
        [("easy run", 0.12), ("tempo", 0.15), ("easy run", 0.12),
         ("intervals", 0.15), ("recovery run", 0.11), ("long run", 0.35)],
    ],
}

TEMPLATES_BY_EXPERIENCE = {
    "beginner": _BEGINNER_TEMPLATES,
    "intermediate": _INTERMEDIATE_TEMPLATES,
    "advanced": _ADVANCED_TEMPLATES,
}


# ---------------------------------------------------------------------------
# Mileage progression targets
# ---------------------------------------------------------------------------

def _compute_target_miles(
    state: TrainingState, week_index: int
) -> list[float]:
    """Compute candidate target weekly mileage values for the next week.

    Returns 2-3 mileage targets representing different progression rates:
    conservative (5%), standard (8%), and aggressive (10%).

    For drop-back weeks (every 4th week), targets are reduced by 15-20%.

    During taper (last 3 weeks), mileage decreases progressively.

    Args:
        state: Current search state.
        week_index: The 1-indexed week about to be planned.

    Returns:
        A list of candidate mileage targets (floats).
    """
    base = state.current_weekly_miles
    total = state.total_weeks
    weeks_remaining = total - state.week_number

    # Taper: last 3 weeks before race
    if weeks_remaining <= 3:
        taper_factor = 0.60 + 0.10 * (weeks_remaining - 1)
        # weeks_remaining=3 -> 0.80, =2 -> 0.70, =1 -> 0.60
        return [round(base * taper_factor, 1)]

    # Drop-back week every 4th week
    is_dropback = (week_index % 4 == 0)
    if is_dropback:
        return [round(base * 0.80, 1), round(base * 0.85, 1)]

    # Normal build weeks: offer two progression rates
    targets = [
        round(base * 1.05, 1),   # Conservative 5% increase
        round(base * 1.10, 1),   # Standard 10% increase (upper limit)
    ]

    return sorted(set(targets))


# ---------------------------------------------------------------------------
# Terrain assignment
# ---------------------------------------------------------------------------

def _assign_terrains(
    num_workouts: int, available_terrain: tuple[str, ...]
) -> list[tuple[str, ...]]:
    """Generate terrain assignments for a week of workouts.

    To keep the branching factor low, we generate just one or two
    diverse terrain assignments rather than all permutations.

    Args:
        num_workouts: Number of workouts to assign terrain to.
        available_terrain: Available terrain types.

    Returns:
        A list of terrain tuples, each of length ``num_workouts``.
    """
    terrain_list = list(available_terrain)

    if len(terrain_list) == 1:
        return [tuple(terrain_list * num_workouts)]

    # Single assignment: round-robin across all available terrains.
    # This maximises terrain variety (avoids PENALTY_TERRAIN_MONOTONY).
    rr = tuple(terrain_list[i % len(terrain_list)] for i in range(num_workouts))
    return [rr]


# ---------------------------------------------------------------------------
# Main action generation
# ---------------------------------------------------------------------------

def generate_week_candidates(state: TrainingState) -> list[tuple[tuple[dict, ...], float]]:
    """Generate all candidate weeks (successors) from the current state.

    Each candidate is a (workouts_tuple, weekly_miles) pair representing
    one possible week that could follow the current state.

    The branching factor is kept manageable by combining:
    - 2-3 workout-mix templates (per experience/days)
    - 2-4 mileage targets (progression rates)
    - 2-4 terrain assignments

    Typical branching factor: 10-30 candidates per state.

    Args:
        state: The current search state.

    Returns:
        A list of (workouts_tuple, weekly_miles) pairs. Each workouts_tuple
        contains workout dicts with keys: day, type, distance, terrain.
    """
    experience = state.experience
    days = state.days_per_week
    week_index = state.week_number + 1  # The week we are about to plan

    # Get templates for this experience level and day count.
    exp_templates = TEMPLATES_BY_EXPERIENCE.get(experience, _BEGINNER_TEMPLATES)
    templates = exp_templates.get(days, exp_templates.get(4, []))

    if not templates:
        return []

    # Get target mileage options.
    mileage_targets = _compute_target_miles(state, week_index)

    # Get terrain assignment options.
    terrain_assignments = _assign_terrains(days, state.available_terrain)

    # Combine templates x mileages x terrains.
    candidates: list[tuple[tuple[dict, ...], float]] = []

    for template in templates:
        for target_miles in mileage_targets:
            for terrains in terrain_assignments:
                workouts = _build_workouts(template, target_miles, terrains)
                actual_miles = sum(w["distance"] for w in workouts)
                candidates.append((tuple(workouts), actual_miles))

    # Deduplicate by converting workout tuples to a hashable form.
    seen: set[tuple[tuple[Any, ...], ...]] = set()
    unique: list[tuple[tuple[dict, ...], float]] = []
    for workouts, miles in candidates:
        key = tuple(
            (w["day"], w["type"], w["distance"], w["terrain"]) for w in workouts
        )
        if key not in seen:
            seen.add(key)
            unique.append((workouts, miles))

    return unique


def _build_workouts(
    template: list[tuple[str, float]],
    target_miles: float,
    terrains: tuple[str, ...],
) -> list[dict]:
    """Build concrete workout dicts from a template, mileage target, and terrains.

    Args:
        template: List of (workout_type, distance_fraction) pairs.
        target_miles: Target total mileage for the week.
        terrains: Terrain assignments, one per workout.

    Returns:
        A list of workout dicts.
    """
    num_workouts = len(template)

    # Spread workouts across the week with rest days between.
    if num_workouts <= 3:
        day_indices = [1, 3, 5][:num_workouts]  # Tue, Thu, Sat
    elif num_workouts == 4:
        day_indices = [1, 2, 4, 5]  # Tue, Wed, Fri, Sat
    elif num_workouts == 5:
        day_indices = [0, 1, 3, 4, 5]  # Mon, Tue, Thu, Fri, Sat
    else:
        day_indices = [0, 1, 2, 3, 4, 5][:num_workouts]

    workouts = []
    for i, (wtype, frac) in enumerate(template):
        distance = round(target_miles * frac, 1)
        distance = max(distance, 1.0)  # Minimum 1 mile per workout
        terrain = terrains[i] if i < len(terrains) else terrains[0]
        day = DAY_ORDER[day_indices[i]] if i < len(day_indices) else DAY_ORDER[i]
        workouts.append({
            "day": day,
            "type": wtype,
            "distance": distance,
            "terrain": terrain,
        })

    return workouts
