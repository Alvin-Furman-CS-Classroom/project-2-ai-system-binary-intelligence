"""
Search state representation for the training plan generator.

A ``TrainingState`` captures everything A* needs to know about a partially
built training plan. It is the "node" in the search graph. States are
immutable so they can be stored in sets and used as dictionary keys.

Terminology (matches Informed Search lecture slides):
    - g(n): path cost from start to this state (accumulated penalties)
    - h(n): heuristic estimate of remaining cost to goal
    - f(n) = g(n) + h(n): total estimated cost through this state

Example:
    >>> from module2_plan_generator.states import TrainingState
    >>> start = TrainingState.create_start(
    ...     total_weeks=16,
    ...     current_weekly_miles=15.0,
    ...     days_per_week=4,
    ...     experience="beginner",
    ...     available_terrain=["road", "trail"],
    ... )
    >>> start.week_number
    0
    >>> start.is_goal()
    False
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TrainingState:
    """Immutable snapshot of a partially built training plan.

    Attributes:
        week_number: How many weeks have been planned so far (0 = start).
        total_weeks: Total weeks in the plan (depth of the goal state).
        current_weekly_miles: The mileage of the most recently planned
            week.  For the start state this is the runner's current base.
        days_per_week: Training days per week (constant through plan).
        experience: Runner experience level.
        available_terrain: Tuple of terrain types (tuple for hashability).
        weekly_miles_history: Tuple of mileage totals for all planned
            weeks so far.
        plan_weeks: Tuple of tuples of workout dicts, one inner tuple
            per planned week.
        g_cost: Accumulated penalty from start through this state.
        parent: Reference to the previous state (for path recovery).
    """

    week_number: int
    total_weeks: int
    current_weekly_miles: float
    days_per_week: int
    experience: str
    available_terrain: tuple[str, ...]
    weekly_miles_history: tuple[float, ...]
    plan_weeks: tuple[tuple[dict, ...], ...]
    g_cost: float
    parent: TrainingState | None = field(default=None, compare=False, hash=False)

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create_start(
        cls,
        total_weeks: int,
        current_weekly_miles: float,
        days_per_week: int,
        experience: str,
        available_terrain: list[str],
    ) -> TrainingState:
        """Create the initial search state (empty plan).

        Args:
            total_weeks: Number of weeks until race day.
            current_weekly_miles: Runner's current weekly mileage base.
            days_per_week: How many days per week the runner trains.
            experience: One of 'beginner', 'intermediate', 'advanced'.
            available_terrain: List of terrain strings.

        Returns:
            A ``TrainingState`` representing the search start node.
        """
        return cls(
            week_number=0,
            total_weeks=total_weeks,
            current_weekly_miles=current_weekly_miles,
            days_per_week=days_per_week,
            experience=experience,
            available_terrain=tuple(t.lower() for t in available_terrain),
            weekly_miles_history=(),
            plan_weeks=(),
            g_cost=0.0,
            parent=None,
        )

    # ------------------------------------------------------------------
    # Goal test
    # ------------------------------------------------------------------

    def is_goal(self) -> bool:
        """Return True if all weeks in the plan have been filled."""
        return self.week_number >= self.total_weeks

    # ------------------------------------------------------------------
    # Successor generation helper
    # ------------------------------------------------------------------

    def add_week(
        self,
        workouts: tuple[dict, ...],
        week_miles: float,
        week_penalty: float,
    ) -> TrainingState:
        """Return a new state with one additional week appended.

        This is the "action" in the search: transitioning from week k to
        week k+1 by choosing a specific set of workouts.

        Args:
            workouts: Tuple of workout dicts for the new week.
            week_miles: Total mileage for the new week.
            week_penalty: The cost c(n, n') for this transition (the
                penalty score of the new week).

        Returns:
            A new ``TrainingState`` representing the successor.
        """
        return TrainingState(
            week_number=self.week_number + 1,
            total_weeks=self.total_weeks,
            current_weekly_miles=week_miles,
            days_per_week=self.days_per_week,
            experience=self.experience,
            available_terrain=self.available_terrain,
            weekly_miles_history=self.weekly_miles_history + (week_miles,),
            plan_weeks=self.plan_weeks + (workouts,),
            g_cost=self.g_cost + week_penalty,
            parent=self,
        )

    # ------------------------------------------------------------------
    # Path recovery
    # ------------------------------------------------------------------

    def recover_plan(self) -> list[dict]:
        """Walk back through parent pointers to reconstruct the full plan.

        Returns:
            A list of week dicts, each containing ``week``, ``total_miles``,
            ``weekly_total`` (alias), ``long_run`` (miles), and ``workouts``.
        """
        states: list[TrainingState] = []
        current: TrainingState | None = self
        while current is not None and current.week_number > 0:
            states.append(current)
            current = current.parent
        states.reverse()

        plan = []
        for i, state in enumerate(states):
            week_workouts = list(state.plan_weeks[i]) if i < len(state.plan_weeks) else []
            total_miles = state.weekly_miles_history[i] if i < len(state.weekly_miles_history) else 0
            long_run = 0.0
            for w in week_workouts:
                if w.get("type") == "long run":
                    long_run = max(long_run, float(w.get("distance", 0)))
            plan.append({
                "week": i + 1,
                "total_miles": total_miles,
                "weekly_total": total_miles,
                "long_run": round(long_run, 1),
                "workouts": week_workouts,
            })
        return plan

    # ------------------------------------------------------------------
    # Hashing (for OPEN / CLOSED sets)
    # ------------------------------------------------------------------

    def __hash__(self) -> int:
        return hash((self.week_number, self.weekly_miles_history))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TrainingState):
            return NotImplemented
        return (
            self.week_number == other.week_number
            and self.weekly_miles_history == other.weekly_miles_history
        )
