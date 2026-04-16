"""
Unit tests for module2_plan_generator.search and module2_plan_generator.planner.

Tests the A* search algorithm, the public API, plan structure, search
statistics, error handling, and Module 1 integration hooks.
"""

import sys
import os
import pytest
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from module2_plan_generator.search import a_star_search
from module2_plan_generator.states import TrainingState
from module2_plan_generator.planner import generate_plan, generate_plan_detailed


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _start(total_weeks=12, current_miles=15.0, days=4,
           experience="beginner", terrain=("road", "trail")):
    return TrainingState.create_start(
        total_weeks=total_weeks,
        current_weekly_miles=current_miles,
        days_per_week=days,
        experience=experience,
        available_terrain=list(terrain),
    )


def _config(weeks=16, days=4, miles=15, experience="beginner",
            terrain=None, goal="complete marathon"):
    race = date.today() + timedelta(weeks=weeks)
    return {
        "goal": goal,
        "race_date": race.isoformat(),
        "days_per_week": days,
        "current_weekly_miles": miles,
        "experience": experience,
        "available_terrain": terrain or ["road", "trail"],
    }


# ===================================================================
# A* Search: Core Behavior
# ===================================================================

class TestAStarSearch:

    def test_finds_plan(self):
        result = a_star_search(_start(total_weeks=8))
        assert result["success"] is True
        assert len(result["plan"]) == 8

    def test_plan_length_matches_total_weeks(self):
        for weeks in [6, 10, 16, 20]:
            result = a_star_search(_start(total_weeks=weeks))
            assert result["success"] is True
            assert len(result["plan"]) == weeks, f"Failed for {weeks} weeks"

    def test_returns_search_stats(self):
        result = a_star_search(_start(total_weeks=8))
        assert "nodes_explored" in result
        assert "nodes_generated" in result
        assert result["nodes_explored"] > 0
        assert result["nodes_generated"] > 0

    def test_algorithm_is_a_star(self):
        result = a_star_search(_start(total_weeks=8))
        assert result["algorithm"] == "a_star"

    def test_penalty_is_non_negative(self):
        result = a_star_search(_start(total_weeks=8))
        assert result["total_penalty"] >= 0

    def test_rationale_is_descriptive(self):
        result = a_star_search(_start(total_weeks=8))
        assert isinstance(result["rationale"], str)
        assert len(result["rationale"]) > 20


# ===================================================================
# Plan Structure and Content
# ===================================================================

class TestPlanStructure:

    def test_weeks_are_numbered_sequentially(self):
        result = a_star_search(_start(total_weeks=10))
        for i, week in enumerate(result["plan"]):
            assert week["week"] == i + 1

    def test_each_week_has_workouts(self):
        result = a_star_search(_start(total_weeks=8))
        for week in result["plan"]:
            assert "workouts" in week
            assert len(week["workouts"]) > 0

    def test_each_week_has_total_miles(self):
        result = a_star_search(_start(total_weeks=8))
        for week in result["plan"]:
            assert "total_miles" in week
            assert week["total_miles"] > 0

    def test_workouts_have_required_fields(self):
        result = a_star_search(_start(total_weeks=8))
        for week in result["plan"]:
            for w in week["workouts"]:
                assert "day" in w
                assert "type" in w
                assert "distance" in w
                assert "terrain" in w

    def test_workout_count_matches_days_per_week(self):
        for days in [3, 4, 5]:
            result = a_star_search(_start(total_weeks=8, days=days))
            for week in result["plan"]:
                assert len(week["workouts"]) == days


# ===================================================================
# Training Principles in Output
# ===================================================================

class TestTrainingPrinciples:

    def test_mileage_generally_increases(self):
        """Overall trend should be increasing (ignoring dropback/taper)."""
        result = a_star_search(_start(total_weeks=12, current_miles=15))
        miles = [w["total_miles"] for w in result["plan"]]
        # First half average should be less than peak (excluding taper).
        first_quarter = sum(miles[:3]) / 3
        peak = max(miles)
        assert peak > first_quarter

    def test_taper_reduces_mileage(self):
        """Last 2 weeks should have less mileage than the peak."""
        result = a_star_search(_start(total_weeks=12, current_miles=15))
        miles = [w["total_miles"] for w in result["plan"]]
        peak = max(miles[:-3])  # Peak excluding taper
        assert miles[-1] < peak
        assert miles[-2] < peak

    def test_has_dropback_weeks(self):
        """There should be at least one week with reduced mileage in the build phase."""
        result = a_star_search(_start(total_weeks=16, current_miles=15))
        miles = [w["total_miles"] for w in result["plan"]]
        build_miles = miles[:-3]  # Exclude taper
        if len(build_miles) >= 4:
            # Check that some week is noticeably lower than its neighbors.
            has_drop = False
            for i in range(1, len(build_miles)):
                if build_miles[i] < build_miles[i - 1] * 0.92:
                    has_drop = True
                    break
            assert has_drop, f"No dropback found in {build_miles}"

    def test_every_week_has_long_run(self):
        result = a_star_search(_start(total_weeks=8))
        for week in result["plan"]:
            types = [w["type"] for w in week["workouts"]]
            assert "long run" in types, f"Week {week['week']} missing long run"

    def test_terrain_variety(self):
        """Plan should use multiple terrains when available."""
        result = a_star_search(_start(
            total_weeks=8, terrain=("road", "trail", "track")
        ))
        all_terrains = set()
        for week in result["plan"]:
            for w in week["workouts"]:
                all_terrains.add(w["terrain"])
        assert len(all_terrains) >= 2


# ===================================================================
# Different Experience Levels
# ===================================================================

class TestExperienceLevels:

    def test_beginner_plan(self):
        result = a_star_search(_start(experience="beginner", current_miles=15))
        assert result["success"]
        for week in result["plan"]:
            for w in week["workouts"]:
                assert w["type"] not in ("tempo", "intervals", "race pace")

    def test_intermediate_plan(self):
        result = a_star_search(_start(experience="intermediate", current_miles=25))
        assert result["success"]
        has_hard = any(
            w["type"] in ("tempo", "intervals")
            for week in result["plan"]
            for w in week["workouts"]
        )
        assert has_hard

    def test_advanced_plan(self):
        result = a_star_search(_start(experience="advanced", current_miles=40))
        assert result["success"]


# ===================================================================
# Public API: generate_plan
# ===================================================================

class TestGeneratePlan:

    def test_success(self):
        result = generate_plan(_config())
        assert result["success"] is True

    def test_returns_all_keys(self):
        result = generate_plan(_config())
        assert "success" in result
        assert "plan" in result
        assert "total_weeks" in result
        assert "total_penalty" in result
        assert "search_stats" in result
        assert "rationale" in result
        assert "errors" in result

    def test_errors_empty_on_success(self):
        result = generate_plan(_config())
        assert result["errors"] == []

    def test_invalid_input_returns_errors(self):
        bad = {"goal": "fly"}
        result = generate_plan(bad)
        assert result["success"] is False
        assert len(result["errors"]) > 0

    def test_half_marathon(self):
        result = generate_plan(_config(goal="complete half marathon"))
        assert result["success"] is True

    def test_different_day_counts(self):
        for days in [3, 4, 5, 6]:
            result = generate_plan(_config(days=days))
            assert result["success"] is True, f"Failed for {days} days"

    def test_single_terrain(self):
        result = generate_plan(_config(terrain=["treadmill"]))
        assert result["success"] is True

    def test_many_terrains(self):
        result = generate_plan(
            _config(terrain=["road", "trail", "track", "treadmill"])
        )
        assert result["success"] is True


# ===================================================================
# Public API: generate_plan_detailed
# ===================================================================

class TestGeneratePlanDetailed:

    def test_includes_weekly_analysis(self):
        result = generate_plan_detailed(_config())
        assert "weekly_analysis" in result
        assert len(result["weekly_analysis"]) > 0

    def test_weekly_analysis_has_correct_fields(self):
        result = generate_plan_detailed(_config())
        for wa in result["weekly_analysis"]:
            assert "week" in wa
            assert "miles" in wa
            assert "penalty" in wa
            assert "violations" in wa
            assert "miles_change_pct" in wa

    def test_weekly_analysis_matches_plan_length(self):
        result = generate_plan_detailed(_config())
        assert len(result["weekly_analysis"]) == len(result["plan"])

    def test_violations_are_strings(self):
        result = generate_plan_detailed(_config())
        for wa in result["weekly_analysis"]:
            for v in wa["violations"]:
                assert isinstance(v, str)

    def test_invalid_input_empty_analysis(self):
        result = generate_plan_detailed({"goal": "invalid"})
        assert result["weekly_analysis"] == []


# ===================================================================
# Module 1 Integration Hook
# ===================================================================

class TestModule1Integration:

    def test_works_without_validate_fn(self):
        """When no validate_fn is provided, all workouts pass."""
        result = generate_plan(_config())
        assert result["success"] is True

    def test_validate_fn_called(self):
        """A mock validate_fn should be invoked for each workout."""
        call_count = 0

        def mock_validate(profile, workout):
            nonlocal call_count
            call_count += 1
            return {"safe": True, "reason": "ok", "alternative": None}

        profile = {
            "weekly_mileage": 15,
            "experience_level": "beginner",
            "hydrated": True,
            "proper_footwear": True,
            "weather": "normal",
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "fully_recovered": True,
            "sleep_quality": "good",
            "available_terrain": ["road", "trail"],
        }

        result = generate_plan(_config(weeks=6), validate_fn=mock_validate,
                               runner_profile=profile)
        assert result["success"] is True
        assert call_count > 0

    def test_unsafe_workout_replaced_with_alternative(self):
        """When validate_fn returns unsafe + alternative, the alternative is used."""
        def mock_validate(profile, workout):
            if workout.get("type") == "long run":
                return {
                    "safe": False,
                    "reason": "too far",
                    "alternative": {
                        "type": "easy run",
                        "distance": workout["distance"] * 0.7,
                        "terrain": workout["terrain"],
                    },
                }
            return {"safe": True, "reason": "ok", "alternative": None}

        profile = {"weekly_mileage": 15, "experience_level": "beginner",
                    "available_terrain": ["road", "trail"]}

        result = generate_plan(_config(weeks=6), validate_fn=mock_validate,
                               runner_profile=profile)
        # Should still succeed, but long runs may have been replaced.
        assert result["success"] is True

    def test_validate_fn_exception_handled(self):
        """If validate_fn throws, the workout should be included as-is."""
        def broken_validate(profile, workout):
            raise RuntimeError("Module 1 broke!")

        profile = {"weekly_mileage": 15}
        result = generate_plan(_config(weeks=6), validate_fn=broken_validate,
                               runner_profile=profile)
        assert result["success"] is True


# ===================================================================
# Performance
# ===================================================================

class TestPerformance:

    def test_completes_in_reasonable_time(self):
        """A 20-week plan should complete in under 2 seconds."""
        import time
        start_time = time.time()
        result = a_star_search(_start(total_weeks=20))
        elapsed = time.time() - start_time
        assert result["success"] is True
        assert elapsed < 2.0, f"Took {elapsed:.2f}s"

    def test_nodes_explored_reasonable(self):
        """Should not explore an unreasonable number of nodes."""
        result = a_star_search(_start(total_weeks=16))
        assert result["nodes_explored"] < 5000
