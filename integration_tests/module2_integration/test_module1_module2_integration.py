"""
Integration tests: Module 1 (safety validator) + Module 2 (plan generator).

These tests verify that the full pipeline works: plan generation with real
Module 1 validation, plan structure, safety of every workout, critical
safety blocking, advisories, and experience-level behavior.

Run from repo root: pytest integration_tests/module2_integration/ -v
Or: PYTHONPATH=. pytest integration_tests/ -v
"""
from __future__ import annotations

from datetime import date, timedelta

from src.module1_safety_validator import validate_workout
from src.module2_plan_generator import generate_plan, generate_plan_detailed


# ---------------------------------------------------------------------------
# Shared fixtures: config and runner profiles
# ---------------------------------------------------------------------------


def _plan_config(
    weeks: int = 12,
    days_per_week: int = 4,
    current_weekly_miles: float = 15.0,
    experience: str = "beginner",
    terrain: list | None = None,
    goal: str = "complete marathon",
) -> dict:
    """Build a planner config with race_date in the future."""
    race_date = date.today() + timedelta(weeks=max(weeks, 1))
    return {
        "goal": goal,
        "race_date": race_date.isoformat(),
        "days_per_week": days_per_week,
        "current_weekly_miles": current_weekly_miles,
        "experience": experience,
        "available_terrain": terrain or ["road", "track"],
    }


def _healthy_runner_profile(
    weekly_mileage: float = 15.0,
    experience_level: str = "beginner",
    terrain: list | None = None,
    injuries: list | None = None,
    symptoms: list | None = None,
) -> dict:
    """Runner profile that passes Module 1 for normal workouts."""
    return {
        "weekly_mileage": weekly_mileage,
        "experience_level": experience_level,
        "injuries": injuries or [],
        "symptoms": symptoms or [],
        "pain_level": "none",
        "fully_recovered": True,
        "sleep_quality": "good",
        "rest_days_this_week": 2,
        "days_trained_this_week": 3,
        "hydrated": True,
        "proper_footwear": True,
        "weather": "normal",
        "available_terrain": terrain or ["road", "track"],
    }


# ===========================================================================
# Full pipeline: Module 1 + Module 2 together
# ===========================================================================


class TestFullPipeline:
    """End-to-end: generate_plan with real validate_workout."""

    def test_full_pipeline_generates_plan(self):
        """With Module 1 validation, a valid plan is produced."""
        config = _plan_config(weeks=10)
        profile = _healthy_runner_profile(
            weekly_mileage=config["current_weekly_miles"],
            experience_level=config["experience"],
            terrain=config["available_terrain"],
        )
        result = generate_plan(
            config,
            validate_fn=validate_workout,
            runner_profile=profile,
        )
        assert result["success"] is True
        assert len(result["plan"]) == 10
        assert result["errors"] == []
        assert "search_stats" in result
        assert result["search_stats"]["nodes_explored"] > 0
        assert isinstance(result["rationale"], str) and len(result["rationale"]) > 0

    def test_plan_structure_complete(self):
        """Each week has week, total_miles, weekly_total, long_run, workouts."""
        config = _plan_config(weeks=8, days_per_week=4)
        profile = _healthy_runner_profile()
        result = generate_plan(config, validate_fn=validate_workout, runner_profile=profile)
        assert result["success"] is True
        for week_data in result["plan"]:
            assert "week" in week_data
            assert "total_miles" in week_data
            assert week_data.get("weekly_total", week_data["total_miles"]) == week_data["total_miles"]
            assert "long_run" in week_data
            assert "workouts" in week_data
            assert len(week_data["workouts"]) == config["days_per_week"]
            for w in week_data["workouts"]:
                assert "day" in w
                assert "type" in w
                assert "distance" in w
                assert "terrain" in w

    def test_weeks_numbered_sequentially(self):
        """Plan weeks are 1, 2, ..., total_weeks."""
        config = _plan_config(weeks=6)
        profile = _healthy_runner_profile()
        result = generate_plan(config, validate_fn=validate_workout, runner_profile=profile)
        assert result["success"] is True
        for i, week_data in enumerate(result["plan"]):
            assert week_data["week"] == i + 1

    def test_every_week_has_long_run(self):
        """Each week contains at least one long run workout."""
        config = _plan_config(weeks=8)
        profile = _healthy_runner_profile()
        result = generate_plan(config, validate_fn=validate_workout, runner_profile=profile)
        assert result["success"] is True
        for week_data in result["plan"]:
            types = [w["type"] for w in week_data["workouts"]]
            assert "long run" in types, f"Week {week_data['week']} missing long run"

    def test_plan_uses_only_available_terrain(self):
        """Workouts only use terrain from config."""
        config = _plan_config(weeks=8, terrain=["road", "treadmill"])
        profile = _healthy_runner_profile(terrain=["road", "treadmill"])
        result = generate_plan(config, validate_fn=validate_workout, runner_profile=profile)
        assert result["success"] is True
        allowed = {"road", "treadmill"}
        for week_data in result["plan"]:
            for w in week_data["workouts"]:
                assert w["terrain"] in allowed, f"Unexpected terrain {w['terrain']}"

    def test_different_plan_lengths(self):
        """Pipeline works for short and longer plans."""
        for weeks in [6, 12, 16]:
            config = _plan_config(weeks=weeks)
            profile = _healthy_runner_profile()
            result = generate_plan(config, validate_fn=validate_workout, runner_profile=profile)
            assert result["success"] is True, f"Failed for {weeks} weeks"
            assert len(result["plan"]) == weeks


# ===========================================================================
# Safety: every workout in the plan passes Module 1
# ===========================================================================


class TestPlanSafetyValidated:
    """When generated with Module 1, every workout should be safe for the profile."""

    def test_every_workout_passes_module1_validation(self):
        """Each workout in the plan is validated safe by Module 1 for the runner."""
        config = _plan_config(weeks=8)
        profile = _healthy_runner_profile(
            weekly_mileage=config["current_weekly_miles"],
            experience_level=config["experience"],
            terrain=config["available_terrain"],
        )
        result = generate_plan(config, validate_fn=validate_workout, runner_profile=profile)
        assert result["success"] is True

        # Simulate the cumulative profile as the planner would: update mileage and days each week
        prev_miles = float(config["current_weekly_miles"])
        for week_data in result["plan"]:
            workouts = week_data["workouts"]
            profile_this_week = {
                **profile,
                "weekly_mileage": prev_miles,
                "days_trained_this_week": len(workouts),
                "rest_days_this_week": 7 - len(workouts),
            }
            for w in workouts:
                workout = {"type": w["type"], "distance": w["distance"], "terrain": w["terrain"]}
                validation = validate_workout(profile_this_week, workout)
                assert validation.get("safe") is True, (
                    f"Week {week_data['week']} workout {w} failed: {validation.get('reason')}"
                )
            prev_miles = week_data["total_miles"]

    def test_beginner_plan_no_tempo_or_intervals(self):
        """Beginner plans do not include tempo or intervals (Module 2 + Module 1)."""
        config = _plan_config(weeks=8, experience="beginner")
        profile = _healthy_runner_profile(experience_level="beginner")
        result = generate_plan(config, validate_fn=validate_workout, runner_profile=profile)
        assert result["success"] is True
        for week_data in result["plan"]:
            for w in week_data["workouts"]:
                assert w["type"] not in ("tempo", "intervals", "race pace"), (
                    f"Beginner plan should not have {w['type']}"
                )


# ===========================================================================
# Critical safety: plan generation blocked
# ===========================================================================


class TestCriticalSafetyBlocksPlan:
    """When runner has critical safety issues, no plan is generated."""

    def test_chest_pain_blocks_plan_generation(self):
        """Profile with chest pain (critical) causes plan generation to be blocked."""
        config = _plan_config(weeks=10)
        profile = _healthy_runner_profile()
        profile["symptoms"] = ["chest_pain"]
        result = generate_plan(config, validate_fn=validate_workout, runner_profile=profile)
        assert result["success"] is False
        assert len(result["plan"]) == 0
        assert "Doctor's clearance" in result.get("rationale", "") or any(
            "clearance" in e.lower() for e in result.get("errors", [])
        )

    def test_without_validate_fn_critical_not_checked(self):
        """Without Module 1, planner does not block on profile (no pre-check)."""
        config = _plan_config(weeks=8)
        # No validate_fn: planner generates plan regardless of profile
        result = generate_plan(config)
        assert result["success"] is True
        assert len(result["plan"]) == 8


# ===========================================================================
# Advisory notes (medium severity)
# ===========================================================================


class TestAdvisoryNotes:
    """When Module 1 returns medium severity, advisory_notes may be populated."""

    def test_result_includes_advisory_notes_key(self):
        """Result dict has advisory_notes when using validate_fn."""
        config = _plan_config(weeks=8)
        profile = _healthy_runner_profile()
        result = generate_plan(config, validate_fn=validate_workout, runner_profile=profile)
        assert "advisory_notes" in result
        assert isinstance(result["advisory_notes"], list)

    def test_advisory_notes_when_medium_severity_possible(self):
        """If any workout would get medium severity, advisories may list reasons."""
        # Use a profile that might trigger medium (e.g. poor sleep) - optional check
        config = _plan_config(weeks=6)
        profile = _healthy_runner_profile()
        profile["sleep_quality"] = "poor"
        result = generate_plan(config, validate_fn=validate_workout, runner_profile=profile)
        assert "advisory_notes" in result
        # Plan may still succeed; we only check structure
        if result["success"]:
            assert isinstance(result["advisory_notes"], list)


# ===========================================================================
# generate_plan_detailed with Module 1
# ===========================================================================


class TestGeneratePlanDetailedIntegration:
    """generate_plan_detailed with Module 1 returns weekly_analysis consistent with plan."""

    def test_detailed_includes_weekly_analysis(self):
        """Detailed result has weekly_analysis when plan succeeds."""
        config = _plan_config(weeks=8)
        profile = _healthy_runner_profile()
        result = generate_plan_detailed(
            config,
            validate_fn=validate_workout,
            runner_profile=profile,
        )
        assert result["success"] is True
        assert "weekly_analysis" in result
        assert len(result["weekly_analysis"]) == len(result["plan"])

    def test_weekly_analysis_matches_plan_weeks(self):
        """Each weekly_analysis entry corresponds to a plan week."""
        config = _plan_config(weeks=6)
        profile = _healthy_runner_profile()
        result = generate_plan_detailed(
            config,
            validate_fn=validate_workout,
            runner_profile=profile,
        )
        assert result["success"] is True
        for i, analysis in enumerate(result["weekly_analysis"]):
            assert analysis["week"] == result["plan"][i]["week"]
            assert analysis["miles"] == result["plan"][i]["total_miles"]


# ===========================================================================
# Experience levels and terrain
# ===========================================================================


class TestExperienceAndTerrain:
    """Different experience levels and terrain options."""

    def test_intermediate_plan_with_module1(self):
        """Intermediate runner gets a plan with Module 1 validation."""
        config = _plan_config(weeks=10, experience="intermediate", current_weekly_miles=25)
        profile = _healthy_runner_profile(
            weekly_mileage=25,
            experience_level="intermediate",
        )
        result = generate_plan(config, validate_fn=validate_workout, runner_profile=profile)
        assert result["success"] is True
        assert len(result["plan"]) == 10

    def test_single_terrain_plan(self):
        """Plan with only one terrain uses that terrain for all workouts."""
        config = _plan_config(weeks=8, terrain=["treadmill"])
        profile = _healthy_runner_profile(terrain=["treadmill"])
        result = generate_plan(config, validate_fn=validate_workout, runner_profile=profile)
        assert result["success"] is True
        for week_data in result["plan"]:
            for w in week_data["workouts"]:
                assert w["terrain"] == "treadmill"

    def test_half_marathon_goal(self):
        """Pipeline supports half marathon goal."""
        config = _plan_config(weeks=10, goal="complete half marathon")
        profile = _healthy_runner_profile()
        result = generate_plan(config, validate_fn=validate_workout, runner_profile=profile)
        assert result["success"] is True


# ===========================================================================
# Error handling and edge cases
# ===========================================================================


class TestIntegrationEdgeCases:
    """Edge cases across the pipeline."""

    def test_invalid_config_returns_errors_no_plan(self):
        """Invalid planner config returns success=False and errors."""
        result = generate_plan(
            {"goal": "fly to the moon"},
            validate_fn=validate_workout,
            runner_profile=_healthy_runner_profile(),
        )
        assert result["success"] is False
        assert len(result.get("errors", [])) > 0
        assert len(result.get("plan", [])) == 0

    def test_plan_without_validate_fn_has_no_advisory_notes(self):
        """When validate_fn is not provided, advisory_notes is empty."""
        config = _plan_config(weeks=8)
        result = generate_plan(config)
        assert result["success"] is True
        assert result.get("advisory_notes", []) == []
