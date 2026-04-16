"""
Heuristic function for A* search in the training plan generator.

The heuristic h(n) estimates the minimum remaining cost (penalties) from
the current state to the goal state (complete plan). It is designed to be
both **admissible** and **consistent** so that A* with graph-search is
guaranteed to find an optimal plan.

Admissibility (slide 10):
    0 <= h(n) <= h*(n) for all n, where h*(n) is the true remaining cost.
    Our heuristic never overestimates because it only counts penalties that
    are mathematically unavoidable.

Consistency / monotonicity (slide 16):
    h(n) <= c(n, n') + h(n') for all successors n' of n.
    Adding a week can only reduce the number of remaining forced violations,
    and c(n, n') captures at least that reduction.

The heuristic uses domain knowledge to estimate forced 10% rule violations:
if the runner needs to reach a target mileage and cannot get there within
the remaining weeks while respecting the 10% rule, some violations are
unavoidable.

Example:
    >>> from module2_plan_generator.heuristics import compute_heuristic
    >>> from module2_plan_generator.states import TrainingState
    >>> state = TrainingState.create_start(
    ...     total_weeks=16, current_weekly_miles=15.0,
    ...     days_per_week=4, experience="beginner",
    ...     available_terrain=["road", "trail"],
    ... )
    >>> h = compute_heuristic(state)
    >>> h >= 0
    True
"""

from __future__ import annotations

import math

from .constraints import PENALTY_TEN_PERCENT_RULE
from .states import TrainingState


# Target peak weekly mileage by experience level (miles).
# These are conservative estimates based on standard marathon plans.
TARGET_PEAK_MILES = {
    "beginner": 35.0,
    "intermediate": 45.0,
    "advanced": 55.0,
}

# Taper weeks reduce mileage, so peak is reached 3 weeks before race.
TAPER_WEEKS = 3


def compute_heuristic(state: TrainingState) -> float:
    """Compute h(n): estimated minimum remaining penalty from state to goal.

    The heuristic counts the minimum number of weeks where the 10% rule
    must be violated in order to reach peak mileage in time, then
    multiplies by the 10% rule penalty weight.

    Why this is admissible:
        It only counts forced 10% rule violations. In reality, the
        remaining weeks may also accumulate penalties from terrain
        monotony, poor recovery, missing long runs, etc. So the true
        remaining cost h*(n) >= h(n) >= 0.

    Why this is consistent:
        When we move from state n to successor n', we plan one more week.
        That week either (a) does not violate the 10% rule, leaving the
        forced-violation count unchanged, or (b) does violate it, reducing
        the count by 1 while c(n, n') includes at least PENALTY_TEN_PERCENT_RULE.
        In both cases, h(n) <= c(n, n') + h(n').

    Args:
        state: The current search state.

    Returns:
        A non-negative heuristic cost estimate.
    """
    if state.is_goal():
        return 0.0

    remaining_weeks = state.total_weeks - state.week_number
    current_miles = state.current_weekly_miles

    # Determine the target peak mileage.
    target = TARGET_PEAK_MILES.get(state.experience, TARGET_PEAK_MILES["beginner"])

    # The runner needs to reach the target before the taper period.
    build_weeks = max(remaining_weeks - TAPER_WEEKS, 0)

    if build_weeks == 0 or current_miles >= target:
        # Already at target or in taper; no forced 10% violations.
        return 0.0

    # How many weeks does it take to reach target with perfect 10% growth?
    # After k weeks of 10% growth: miles * 1.10^k >= target
    # k >= log(target / current_miles) / log(1.10)
    if current_miles <= 0:
        # Avoid log(0). Assume at least 5 miles base.
        current_miles = 5.0

    weeks_needed_at_10pct = math.ceil(
        math.log(target / current_miles) / math.log(1.10)
    )

    if weeks_needed_at_10pct <= build_weeks:
        # Can reach target within build weeks at 10% growth; no forced violations.
        return 0.0

    # The runner cannot reach target in time with only 10% increases.
    # They must exceed 10% on at least (weeks_needed - build_weeks) weeks.
    forced_violations = weeks_needed_at_10pct - build_weeks

    return forced_violations * PENALTY_TEN_PERCENT_RULE
