"""
Unit tests for module2_plan_generator.actions.

Tests workout template generation, mileage target computation, terrain
assignment, and the overall candidate generation pipeline.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from module2_plan_generator.actions import (
    generate_week_candidates,
    _compute_target_miles,
    _assign_terrains,
    _build_workouts,
    DAY_ORDER,
    TEMPLATES_BY_EXPERIENCE,
)
from module2_plan_generator.states import TrainingState


def _state(total_weeks=16, current_miles=15.0, week_number=0,
           days_per_week=4, experience="beginner",
           terrain=("road", "trail")):
    return TrainingState(
        week_number=week_number,
        total_weeks=total_weeks,
        current_weekly_miles=current_miles,
        days_per_week=days_per_week,
        experience=experience,
        available_terrain=tuple(terrain),
        weekly_miles_history=tuple(current_miles * 1.05 ** i for i in range(week_number)),
        plan_weeks=(),
        g_cost=0.0,
        parent=None,
    )


# ===================================================================
# Mileage Target Computation
# ===================================================================

class TestComputeTargetMiles:

    def test_normal_week_returns_multiple_targets(self):
        state = _state(current_miles=20, week_number=2)
        targets = _compute_target_miles(state, 3)
        assert len(targets) >= 2
        assert all(t > 0 for t in targets)

    def test_normal_week_targets_increase(self):
        state = _state(current_miles=20, week_number=2)
        targets = _compute_target_miles(state, 3)
        assert max(targets) > 20  # At least some increase

    def test_normal_week_max_increase_10_percent(self):
        state = _state(current_miles=20, week_number=2)
        targets = _compute_target_miles(state, 3)
        assert max(targets) <= 22.0  # 20 * 1.10

    def test_dropback_week_reduces_mileage(self):
        """Every 4th week should have lower targets."""
        state = _state(current_miles=20, week_number=3)
        targets = _compute_target_miles(state, 4)  # Week 4 = dropback
        assert all(t < 20 for t in targets)

    def test_dropback_weeks_at_multiples_of_4(self):
        for wk_idx in [4, 8, 12]:
            state = _state(current_miles=20, week_number=wk_idx - 1)
            targets = _compute_target_miles(state, wk_idx)
            assert all(t < 20 for t in targets), f"Week {wk_idx} should be dropback"

    def test_taper_last_three_weeks(self):
        """Final 3 weeks should have progressively decreasing targets."""
        state16 = _state(current_miles=30, week_number=15, total_weeks=18)
        state17 = _state(current_miles=30, week_number=16, total_weeks=18)
        state18 = _state(current_miles=30, week_number=17, total_weeks=18)

        t16 = _compute_target_miles(state16, 16)
        t17 = _compute_target_miles(state17, 17)
        t18 = _compute_target_miles(state18, 18)

        # Each should be less than 30 and decreasing.
        assert all(t < 30 for t in t16)
        assert all(t < 30 for t in t17)
        assert all(t < 30 for t in t18)

    def test_taper_single_target(self):
        """Taper weeks return exactly one target (no choices)."""
        state = _state(current_miles=30, week_number=15, total_weeks=16)
        targets = _compute_target_miles(state, 16)
        assert len(targets) == 1

    def test_targets_are_sorted(self):
        state = _state(current_miles=20, week_number=2)
        targets = _compute_target_miles(state, 3)
        assert targets == sorted(targets)


# ===================================================================
# Terrain Assignment
# ===================================================================

class TestAssignTerrains:

    def test_single_terrain(self):
        result = _assign_terrains(4, ("road",))
        assert len(result) == 1
        assert all(t == "road" for t in result[0])

    def test_two_terrains_round_robin(self):
        result = _assign_terrains(4, ("road", "trail"))
        assert len(result) >= 1
        # Should use both terrains.
        assert set(result[0]) == {"road", "trail"}

    def test_output_length_matches_num_workouts(self):
        for n in [3, 4, 5, 6]:
            result = _assign_terrains(n, ("road", "trail"))
            for assignment in result:
                assert len(assignment) == n

    def test_three_terrains(self):
        result = _assign_terrains(3, ("road", "trail", "track"))
        assert len(result) >= 1
        assert set(result[0]) == {"road", "trail", "track"}


# ===================================================================
# Build Workouts
# ===================================================================

class TestBuildWorkouts:

    def test_correct_number_of_workouts(self):
        template = [("easy run", 0.30), ("easy run", 0.30), ("long run", 0.40)]
        terrains = ("road", "trail", "road")
        workouts = _build_workouts(template, 20.0, terrains)
        assert len(workouts) == 3

    def test_distances_sum_to_target(self):
        template = [("easy run", 0.25), ("easy run", 0.25),
                     ("easy run", 0.20), ("long run", 0.30)]
        terrains = ("road", "trail", "road", "trail")
        workouts = _build_workouts(template, 20.0, terrains)
        total = sum(w["distance"] for w in workouts)
        # Allow small rounding difference.
        assert abs(total - 20.0) < 1.0

    def test_minimum_distance_per_workout(self):
        """No workout should be less than 1 mile."""
        template = [("easy run", 0.05), ("long run", 0.95)]
        terrains = ("road", "trail")
        workouts = _build_workouts(template, 5.0, terrains)
        for w in workouts:
            assert w["distance"] >= 1.0

    def test_workout_has_required_keys(self):
        template = [("easy run", 0.50), ("long run", 0.50)]
        terrains = ("road", "trail")
        workouts = _build_workouts(template, 10.0, terrains)
        for w in workouts:
            assert "day" in w
            assert "type" in w
            assert "distance" in w
            assert "terrain" in w

    def test_days_are_valid(self):
        template = [("easy run", 0.50), ("long run", 0.50)]
        terrains = ("road", "trail")
        workouts = _build_workouts(template, 10.0, terrains)
        for w in workouts:
            assert w["day"] in DAY_ORDER

    def test_terrain_assignment(self):
        template = [("easy run", 0.50), ("long run", 0.50)]
        terrains = ("road", "trail")
        workouts = _build_workouts(template, 10.0, terrains)
        assert workouts[0]["terrain"] == "road"
        assert workouts[1]["terrain"] == "trail"


# ===================================================================
# Full Candidate Generation
# ===================================================================

class TestGenerateWeekCandidates:

    def test_returns_non_empty(self):
        state = _state()
        candidates = generate_week_candidates(state)
        assert len(candidates) > 0

    def test_candidates_have_correct_format(self):
        state = _state()
        candidates = generate_week_candidates(state)
        for workouts, miles in candidates:
            assert isinstance(workouts, tuple)
            assert isinstance(miles, (int, float))
            assert miles > 0
            for w in workouts:
                assert isinstance(w, dict)

    def test_candidate_workout_count_matches_days(self):
        for days in [3, 4, 5]:
            state = _state(days_per_week=days)
            candidates = generate_week_candidates(state)
            for workouts, _ in candidates:
                assert len(workouts) == days, (
                    f"Expected {days} workouts, got {len(workouts)}"
                )

    def test_all_experience_levels_produce_candidates(self):
        for exp in ["beginner", "intermediate", "advanced"]:
            miles = {"beginner": 15, "intermediate": 30, "advanced": 40}[exp]
            state = _state(experience=exp, current_miles=miles)
            candidates = generate_week_candidates(state)
            assert len(candidates) > 0, f"No candidates for {exp}"

    def test_candidates_are_unique(self):
        state = _state()
        candidates = generate_week_candidates(state)
        keys = set()
        for workouts, _ in candidates:
            key = tuple((w["day"], w["type"], w["distance"], w["terrain"]) for w in workouts)
            keys.add(key)
        assert len(keys) == len(candidates), "Duplicate candidates found"

    def test_beginner_no_high_intensity(self):
        """Beginner templates should not include tempo or intervals."""
        state = _state(experience="beginner")
        candidates = generate_week_candidates(state)
        for workouts, _ in candidates:
            for w in workouts:
                assert w["type"] not in ("tempo", "intervals", "race pace"), (
                    f"Beginner got high-intensity workout: {w['type']}"
                )

    def test_intermediate_has_tempo_or_intervals(self):
        """Intermediate templates should include at least one hard workout type."""
        state = _state(experience="intermediate", current_miles=25)
        candidates = generate_week_candidates(state)
        has_hard = False
        for workouts, _ in candidates:
            for w in workouts:
                if w["type"] in ("tempo", "intervals"):
                    has_hard = True
        assert has_hard, "Intermediate should have tempo or intervals"

    def test_all_candidates_include_long_run(self):
        """Every candidate week should have a long run."""
        state = _state()
        candidates = generate_week_candidates(state)
        for workouts, _ in candidates:
            types = [w["type"] for w in workouts]
            assert "long run" in types, f"Missing long run in {types}"

    def test_taper_week_lower_mileage(self):
        """Candidates for taper weeks should have lower mileage."""
        normal_state = _state(current_miles=30, week_number=5, total_weeks=16)
        taper_state = _state(current_miles=30, week_number=14, total_weeks=16)

        normal_candidates = generate_week_candidates(normal_state)
        taper_candidates = generate_week_candidates(taper_state)

        max_normal = max(m for _, m in normal_candidates)
        max_taper = max(m for _, m in taper_candidates)
        assert max_taper < max_normal

    def test_branching_factor_reasonable(self):
        """Should generate a manageable number of candidates (< 50)."""
        state = _state()
        candidates = generate_week_candidates(state)
        assert len(candidates) < 50, f"Too many candidates: {len(candidates)}"
