"""
Training constraints and penalty calculations for marathon plans.

Encodes evidence-based marathon training principles as constraint checks.
Each constraint returns a penalty score: 0 means the constraint is satisfied,
and a positive value indicates the severity of the violation.

Sources:
    - 10% rule: Marathon Handbook, widely cited in sports medicine
    - Long run percentage: Hal Higdon training plans, Runner's World
    - Recovery patterns: Therapeutic Associates, HSS injury prevention
    - Taper principles: Pfitzinger & Douglas, "Advanced Marathoning"

Example:
    >>> from module2_plan_generator.constraints import check_progression
    >>> check_progression(20, 25, "beginner")  # 25% > 8%
    10
    >>> check_progression(20, 22, "intermediate")  # 10% ok
    0
"""

# ---------------------------------------------------------------------------
# Penalty weights (points added to g(n) per violation)
# ---------------------------------------------------------------------------

PENALTY_MISSING_LONG_RUN = 8        # No long run in week or too short
PENALTY_POOR_RECOVERY = 8           # Back-to-back hard days
PENALTY_TERRAIN_MONOTONY = 4        # All workouts on same terrain
PENALTY_INSUFFICIENT_REST = 6       # Fewer than 1 rest day
PENALTY_TAPER_VIOLATION = 10        # Mileage not decreasing during taper
PENALTY_EXCESSIVE_LONG_RUN = 6      # Long run > 35% of weekly mileage
PENALTY_LONG_RUN_OVER_55 = 4        # Long run > 55% of weekly (softer band)
PENALTY_NO_DROPBACK = 5             # No recovery week every 3-4 weeks
PENALTY_BEGINNER_QUALITY_OVERLOAD = 6  # Beginners: >1 tempo/intervals per week

# Experience-based progression: threshold (max allowed growth) and penalty weight
PROGRESSION_BEGINNER = (0.08, 10)       # 8% threshold, penalty 10
PROGRESSION_INTERMEDIATE = (0.10, 10)   # 10% threshold, penalty 10
PROGRESSION_ADVANCED = (0.12, 8)        # 12% threshold, penalty 8
PENALTY_TEN_PERCENT_RULE = 10           # Used by check_ten_percent_rule (intermediate)

# ---------------------------------------------------------------------------
# Workout type classifications
# ---------------------------------------------------------------------------

HARD_WORKOUT_TYPES = {"long run", "tempo", "intervals", "race pace"}
EASY_WORKOUT_TYPES = {"easy run", "recovery run"}


def check_progression(
    previous_miles: float, current_miles: float, experience: str = "beginner"
) -> int:
    """Check whether weekly mileage increase exceeds experience-based threshold.

    Beginners: 8% max growth. Intermediate: 10%. Advanced: 12%.
    The 10% rule is widely cited; we tighten for beginners and relax for advanced.

    Args:
        previous_miles: Total mileage from the previous week.
        current_miles: Total mileage for the current week.
        experience: "beginner", "intermediate", or "advanced".

    Returns:
        0 if within threshold, else penalty (weight varies by experience).
    """
    if previous_miles <= 0:
        return 0
    exp = (experience or "beginner").lower()
    if exp == "beginner":
        threshold, weight = PROGRESSION_BEGINNER
    elif exp == "advanced":
        threshold, weight = PROGRESSION_ADVANCED
    else:
        threshold, weight = PROGRESSION_INTERMEDIATE
    increase_pct = (current_miles - previous_miles) / previous_miles
    if increase_pct > threshold:
        return weight
    return 0


def check_ten_percent_rule(previous_miles: float, current_miles: float) -> int:
    """Legacy: progression check with 10% threshold (intermediate). Use check_progression for experience-based thresholds."""
    return check_progression(previous_miles, current_miles, "intermediate")


def check_long_run_present(
    workouts: list[dict], weekly_miles: float
) -> int:
    """Check that the week contains a long run of appropriate length.

    A long run should be roughly 20-35% of weekly mileage. Missing a long
    run entirely or having one that is too short both incur a penalty.

    Args:
        workouts: List of workout dicts, each with at least a ``type``
            and ``distance`` key.
        weekly_miles: Total planned miles for the week.

    Returns:
        0 if a suitable long run exists, penalty value otherwise.
    """
    long_runs = [w for w in workouts if w.get("type") == "long run"]
    if not long_runs:
        return PENALTY_MISSING_LONG_RUN

    longest = max(w["distance"] for w in long_runs)
    if weekly_miles > 0 and longest / weekly_miles < 0.20:
        return PENALTY_MISSING_LONG_RUN
    return 0


def check_excessive_long_run(
    workouts: list[dict], weekly_miles: float
) -> int:
    """Check that the long run is not too large a share of weekly mileage.

    A long run exceeding about 35% of weekly volume puts
    disproportionate stress on the body (Hal Higdon, Runner's World).
    """
    long_runs = [w for w in workouts if w.get("type") == "long run"]
    if not long_runs or weekly_miles <= 0:
        return 0
    longest = max(w["distance"] for w in long_runs)
    if longest / weekly_miles > 0.35:
        return PENALTY_EXCESSIVE_LONG_RUN
    return 0


def check_long_run_fraction_55(workouts: list[dict], weekly_miles: float) -> int:
    """Softer band: penalize long run > 55% of weekly (partner-style rule)."""
    long_runs = [w for w in workouts if w.get("type") == "long run"]
    if not long_runs or weekly_miles <= 0:
        return 0
    longest = max(w["distance"] for w in long_runs)
    if longest / weekly_miles > 0.55:
        return PENALTY_LONG_RUN_OVER_55
    return 0


def check_beginner_quality_overload(
    workouts: list[dict], experience: str
) -> int:
    """Beginners: penalize more than one quality workout (tempo/intervals) per week."""
    if (experience or "").lower() != "beginner":
        return 0
    quality_types = {"tempo", "intervals", "interval"}
    count = sum(1 for w in workouts if w.get("type", "").lower() in quality_types)
    if count > 1:
        return PENALTY_BEGINNER_QUALITY_OVERLOAD
    return 0


def check_recovery_pattern(workouts: list[dict]) -> int:
    """Check that hard workouts are not scheduled on consecutive days.

    Back-to-back hard efforts increase overtraining and injury risk.
    There should be at least one easy day between hard workout days.

    Args:
        workouts: List of workout dicts sorted by day order. Each must
            have a ``type`` key.

    Returns:
        0 if recovery pattern is respected, penalty otherwise.
    """
    prev_hard = False
    for w in workouts:
        is_hard = w.get("type", "").lower() in HARD_WORKOUT_TYPES
        if is_hard and prev_hard:
            return PENALTY_POOR_RECOVERY
        prev_hard = is_hard
    return 0


def check_terrain_variety(
    workouts: list[dict], available_terrain: list[str]
) -> int:
    """Check that the week uses more than one terrain type.

    Terrain rotation helps prevent repetitive-stress injuries and builds
    well-rounded fitness. If the runner has multiple terrains available,
    using only one incurs a small penalty.

    Args:
        workouts: List of workout dicts, each with a ``terrain`` key.
        available_terrain: Terrains the runner can access.

    Returns:
        0 if terrain variety is adequate, penalty otherwise.
    """
    if len(available_terrain) <= 1:
        return 0  # Cannot diversify with only one option.
    used = {w.get("terrain") for w in workouts}
    if len(used) <= 1:
        return PENALTY_TERRAIN_MONOTONY
    return 0


def check_rest_days(days_per_week: int, num_workouts: int) -> int:
    """Check that there is at least one rest day in the week.

    Args:
        days_per_week: Total days available (always 7).
        num_workouts: Number of workouts scheduled.

    Returns:
        0 if at least one rest day exists, penalty otherwise.
    """
    rest_days = days_per_week - num_workouts
    if rest_days < 1:
        return PENALTY_INSUFFICIENT_REST
    return 0


def check_taper(
    week_number: int, total_weeks: int, current_miles: float,
    previous_miles: float
) -> int:
    """Check taper compliance in the final weeks before race day.

    During the last 2-3 weeks, mileage should decrease to allow the body
    to recover before the race. Increasing mileage during taper is a
    violation.

    Args:
        week_number: 1-indexed week in the plan.
        total_weeks: Total number of weeks in the plan.
        current_miles: Mileage for this week.
        previous_miles: Mileage for the prior week.

    Returns:
        0 if not in taper or taper is respected, penalty otherwise.
    """
    weeks_remaining = total_weeks - week_number
    if weeks_remaining > 3:
        return 0  # Not in taper period yet.
    if current_miles > previous_miles:
        return PENALTY_TAPER_VIOLATION
    return 0


def check_dropback_week(
    week_number: int, weekly_miles_history: list[float]
) -> int:
    """Check that a recovery (drop-back) week occurs every 3-4 weeks.

    Every third or fourth week should have reduced mileage to allow
    adaptation. A drop-back week is one where mileage is at least 15%
    below the highest week in the recent window.

    Args:
        week_number: 1-indexed week in the plan.
        weekly_miles_history: List of weekly mileage totals so far
            (not including the current week).

    Returns:
        0 if drop-back schedule is maintained, penalty otherwise.
    """
    if week_number < 4:
        return 0  # Too early to need a drop-back.

    # Look at the last 4 weeks of history.
    recent = weekly_miles_history[-4:] if len(weekly_miles_history) >= 4 else weekly_miles_history
    if len(recent) < 4:
        return 0

    peak = max(recent)
    if peak <= 0:
        return 0

    # At least one of the last 4 weeks should be noticeably lower than peak.
    has_dropback = any(m <= peak * 0.85 for m in recent)
    if not has_dropback:
        return PENALTY_NO_DROPBACK
    return 0


def compute_week_penalty(
    workouts: list[dict],
    weekly_miles: float,
    previous_miles: float,
    week_number: int,
    total_weeks: int,
    days_per_week: int,
    available_terrain: list[str],
    weekly_miles_history: list[float],
    experience: str = "beginner",
) -> tuple[int, list[str]]:
    """Compute the total penalty for a single week of training.

    Runs all constraint checks and sums the penalties. Also returns a
    list of human-readable violation descriptions for debugging.

    Args:
        workouts: The workouts planned for this week.
        weekly_miles: Sum of distances for this week.
        previous_miles: Sum of distances for the previous week.
        week_number: 1-indexed week number in the plan.
        total_weeks: Total weeks in the training plan.
        days_per_week: Number of training days per week.
        available_terrain: Terrains the runner can access.
        weekly_miles_history: Mileage totals from all previous weeks.
        experience: Runner experience (affects progression threshold and quality overload).

    Returns:
        A tuple of (total_penalty, list_of_violation_descriptions).

    Example:
        >>> workouts = [
        ...     {"type": "easy run", "distance": 4, "terrain": "road"},
        ...     {"type": "easy run", "distance": 4, "terrain": "road"},
        ...     {"type": "long run", "distance": 8, "terrain": "road"},
        ... ]
        >>> penalty, violations = compute_week_penalty(
        ...     workouts, 16, 14, 1, 16, 4, ["road", "trail"], [], "beginner"
        ... )
    """
    total = 0
    violations: list[str] = []

    p = check_progression(previous_miles, weekly_miles, experience)
    if p:
        increase = ((weekly_miles - previous_miles) / previous_miles * 100
                     if previous_miles > 0 else 0)
        violations.append(
            f"Progression rule violated: {increase:.0f}% increase "
            f"({previous_miles:.1f} -> {weekly_miles:.1f} miles)"
        )
        total += p

    p = check_long_run_present(workouts, weekly_miles)
    if p:
        violations.append("Missing or insufficient long run")
        total += p

    p = check_excessive_long_run(workouts, weekly_miles)
    if p:
        violations.append("Long run exceeds 35% of weekly mileage")
        total += p

    p = check_long_run_fraction_55(workouts, weekly_miles)
    if p:
        violations.append("Long run exceeds 55% of weekly mileage")
        total += p

    p = check_beginner_quality_overload(workouts, experience)
    if p:
        violations.append("Beginners: more than one quality workout (tempo/intervals) in week")
        total += p

    p = check_recovery_pattern(workouts)
    if p:
        violations.append("Back-to-back hard workout days")
        total += p

    p = check_terrain_variety(workouts, available_terrain)
    if p:
        violations.append("All workouts on same terrain")
        total += p

    p = check_rest_days(7, len(workouts))
    if p:
        violations.append("Insufficient rest days")
        total += p

    p = check_taper(week_number, total_weeks, weekly_miles, previous_miles)
    if p:
        violations.append("Mileage increased during taper period")
        total += p

    p = check_dropback_week(week_number, weekly_miles_history)
    if p:
        violations.append("No recovery week in last 4 weeks")
        total += p

    return total, violations
