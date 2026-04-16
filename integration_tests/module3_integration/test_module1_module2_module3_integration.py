"""
Integration tests: Module 1 (safety validator) + Module 2 (plan generator) + Module 3 (run logger).

These tests verify that the full pipeline works: plan generation with Module 1
validation, then run logging via natural language (Module 3), and that parsed
runs align with plan semantics and can be validated by Module 1.

Run from repo root: pytest integration_tests/module3_integration/ -v
Or: PYTHONPATH=. pytest integration_tests/ -v
"""
from __future__ import annotations

from datetime import date, timedelta

from src.module1_safety_validator import validate_workout
from src.module2_plan_generator import generate_plan
from src.module3_run_logger import parse_run, log_run, get_run_history
from src.module3_run_logger.store import RunLogStore


# ---------------------------------------------------------------------------
# Shared fixtures: config, runner profile, temp store
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
) -> dict:
    """Runner profile that passes Module 1 for normal workouts."""
    return {
        "weekly_mileage": weekly_mileage,
        "experience_level": experience_level,
        "injuries": [],
        "symptoms": [],
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


def _parsed_to_workout(parsed: dict) -> dict:
    """Convert Module 3 parsed run to Module 1 workout shape (type, distance, terrain)."""
    return {
        "type": parsed["type"],
        "distance": parsed["distance"] if parsed.get("distance") is not None else 0,
        "terrain": parsed["terrain"],
    }


# ===========================================================================
# Full pipeline: M1 + M2 + M3 — plan then “log” planned workout as NL
# ===========================================================================


class TestPlanToRunLogPipeline:
    """Generate plan (M1+M2), then parse natural-language descriptions of planned workouts (M3)."""

    def test_plan_workout_described_in_nl_parses_to_same_type_terrain(self):
        """A planned workout described in natural language parses to matching type and terrain."""
        config = _plan_config(weeks=8)
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
        # Pick first week, first long run workout
        week_one = result["plan"][0]
        long_run_workout = next(
            w for w in week_one["workouts"] if w["type"] == "long run"
        )
        # Describe it in natural language as a runner might log it
        nl = (
            f"did my long run today, {long_run_workout['distance']} miles "
            f"on the {long_run_workout['terrain']}. felt good."
        )
        parsed = parse_run(nl)
        assert parsed["type"] == "long run"
        assert parsed["terrain"] == long_run_workout["terrain"]
        assert parsed["distance"] == long_run_workout["distance"]

    def test_easy_run_from_plan_parses_correctly(self):
        """An easy run from the plan, logged in NL, parses to easy run type and correct terrain."""
        config = _plan_config(weeks=6)
        profile = _healthy_runner_profile()
        result = generate_plan(
            config,
            validate_fn=validate_workout,
            runner_profile=profile,
        )
        assert result["success"] is True
        week_one = result["plan"][0]
        easy_workout = next(
            w for w in week_one["workouts"] if w["type"] == "easy run"
        )
        # Use NL that clearly signals "easy run" (avoid "recovery" which parses as recovery run)
        nl = f"easy {easy_workout['distance']} miles on {easy_workout['terrain']}, felt good."
        parsed = parse_run(nl)
        assert parsed["type"] == "easy run"
        assert parsed["terrain"] == easy_workout["terrain"]
        assert parsed["distance"] == easy_workout["distance"]

    def test_plan_with_treadmill_terrain_logged_in_nl_parses_and_validates(self):
        """Plan with treadmill-only terrain; NL description parses and is validated safe by M1."""
        config = _plan_config(weeks=6, terrain=["treadmill"])
        profile = _healthy_runner_profile(terrain=["treadmill"])
        result = generate_plan(
            config,
            validate_fn=validate_workout,
            runner_profile=profile,
        )
        assert result["success"] is True
        week_one = result["plan"][0]
        w = next(w for w in week_one["workouts"] if w["type"] == "easy run")
        nl = f"easy {w['distance']} miles on treadmill, felt fine"
        parsed = parse_run(nl)
        assert parsed["type"] == "easy run"
        assert parsed["terrain"] == "treadmill"
        workout = _parsed_to_workout(parsed)
        validation = validate_workout(profile, workout)
        assert validation.get("safe") is True


# ===========================================================================
# M1 + M3: Parsed run validated by Module 1
# ===========================================================================


class TestParsedRunValidatedByModule1:
    """Runs parsed by Module 3 can be passed to Module 1 for safety validation."""

    def test_parsed_easy_run_is_safe_for_healthy_profile(self):
        """A parsed 'easy run' description is validated safe by Module 1 for a healthy profile."""
        nl = "easy 5 miles on the road, felt great"
        parsed = parse_run(nl)
        workout = _parsed_to_workout(parsed)
        profile = _healthy_runner_profile(weekly_mileage=20, terrain=["road"])
        validation = validate_workout(profile, workout)
        assert validation.get("safe") is True

    def test_parsed_long_run_validated_by_module1(self):
        """A parsed long run is validated by Module 1 when within profile limits."""
        nl = "long run 10 miles on track, a bit tired at the end"
        parsed = parse_run(nl)
        workout = _parsed_to_workout(parsed)
        profile = _healthy_runner_profile(
            weekly_mileage=35,
            experience_level="intermediate",
            terrain=["road", "track"],
        )
        validation = validate_workout(profile, workout)
        assert validation.get("safe") is True

    def test_parsed_workout_terrain_must_be_in_profile_for_safety(self):
        """When parsed terrain is not in profile's available_terrain, Module 1 can flag it."""
        nl = "easy 4 miles on the trail"
        parsed = parse_run(nl)
        workout = _parsed_to_workout(parsed)
        # Profile only allows road and track
        profile = _healthy_runner_profile(terrain=["road", "track"])
        validation = validate_workout(profile, workout)
        # Module 1 may mark unsafe or suggest alternative when terrain not available
        assert "safe" in validation
        assert "reason" in validation

    def test_parsed_run_with_no_distance_still_validates_with_module1(self):
        """When M3 returns distance None, _parsed_to_workout uses 0; M1 still validates type/terrain."""
        nl = "easy run on the road"
        parsed = parse_run(nl)
        workout = _parsed_to_workout(parsed)
        assert workout["type"] == "easy run"
        assert workout["terrain"] == "road"
        # distance is 0 when parsed had None (so M1 receives valid number)
        assert isinstance(workout["distance"], (int, float))
        profile = _healthy_runner_profile(terrain=["road"])
        validation = validate_workout(profile, workout)
        assert "safe" in validation
        assert "reason" in validation


# ===========================================================================
# M2 + M3: Log runs (parse + store), retrieve history
# ===========================================================================


class TestPlanAndLogRunsWithModule3:
    """Generate plan (M1+M2), log runs via Module 3 (parse + store), assert history consistent."""

    def test_log_run_returns_id_and_history_includes_run(self, tmp_path):
        """log_run parses, persists, returns run ID; get_run_history returns the run."""
        store_path = str(tmp_path / "run_log.json")
        nl = "easy 5 miles on road, felt good"
        run_id = log_run(nl, store_path=store_path)
        assert run_id.startswith("run_")
        history = get_run_history(n=5, store_path=store_path)
        assert len(history) == 1
        assert history[0]["id"] == run_id
        assert history[0]["parsed"]["type"] == "easy run"
        assert history[0]["parsed"]["terrain"] == "road"
        assert history[0]["parsed"]["distance"] == 5.0

    def test_multiple_logged_runs_retrieved_in_order(self, tmp_path):
        """Multiple log_run calls; get_run_history returns them most recent last."""
        store_path = str(tmp_path / "run_log.json")
        log_run("easy 3 miles on track", store_path=store_path)
        log_run("long run 8 miles on road", store_path=store_path)
        log_run("recovery 4 miles treadmill", store_path=store_path)
        history = get_run_history(n=10, store_path=store_path)
        assert len(history) == 3
        assert history[0]["parsed"]["distance"] == 3.0
        assert history[1]["parsed"]["distance"] == 8.0
        assert history[2]["parsed"]["distance"] == 4.0

    def test_plan_then_log_planned_workout_stored_correctly(self, tmp_path):
        """Full pipeline: generate plan, describe one workout in NL, log it; stored entry matches plan."""
        config = _plan_config(weeks=8)
        profile = _healthy_runner_profile()
        result = generate_plan(
            config,
            validate_fn=validate_workout,
            runner_profile=profile,
        )
        assert result["success"] is True
        week_one = result["plan"][0]
        w = next(w for w in week_one["workouts"] if w["type"] == "long run")

        store_path = str(tmp_path / "run_log.json")
        nl = f"long run {w['distance']} miles on {w['terrain']}, felt okay"
        run_id = log_run(nl, store_path=store_path)
        history = get_run_history(n=1, store_path=store_path)
        assert len(history) == 1
        entry = history[0]
        assert entry["id"] == run_id
        assert entry["parsed"]["type"] == w["type"]
        assert entry["parsed"]["terrain"] == w["terrain"]
        assert entry["parsed"]["distance"] == w["distance"]

    def test_get_run_history_n_exceeds_runs_returns_all(self, tmp_path):
        """get_run_history(n) when n is larger than stored runs returns all runs (most recent last)."""
        store_path = str(tmp_path / "run_log.json")
        log_run("easy 2 miles road", store_path=store_path)
        log_run("long 7 miles track", store_path=store_path)
        history = get_run_history(n=100, store_path=store_path)
        assert len(history) == 2
        assert history[-1]["parsed"]["distance"] == 7.0


# ===========================================================================
# M3 independent of M2: run logging works when plan generation is blocked
# ===========================================================================


class TestModule3WhenPlanBlocked:
    """Module 3 (parse_run, log_run) works even when Module 2 cannot produce a plan."""

    def test_parse_and_log_work_when_plan_generation_blocked_by_critical_safety(self, tmp_path):
        """Critical profile blocks plan (M1+M2); M3 parse_run and log_run still work."""
        config = _plan_config(weeks=8)
        profile = _healthy_runner_profile()
        profile["symptoms"] = ["chest_pain"]
        result = generate_plan(
            config,
            validate_fn=validate_workout,
            runner_profile=profile,
        )
        assert result["success"] is False
        assert len(result.get("plan", [])) == 0

        # M3 does not depend on having a plan
        parsed = parse_run("easy 5 miles on road, felt good")
        assert parsed["type"] == "easy run"
        assert parsed["distance"] == 5.0
        run_id = log_run("easy 5 miles on road", store_path=str(tmp_path / "run_log.json"))
        assert run_id.startswith("run_")


# ===========================================================================
# All three modules: consistency and safety
# ===========================================================================


class TestAllThreeModulesConsistency:
    """End-to-end consistency across M1, M2, and M3."""

    def test_workout_from_plan_validated_safe_then_parsed_matches(self):
        """Plan workout is safe (M1), described in NL, parsed (M3) matches and is still safe (M1)."""
        config = _plan_config(weeks=8)
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
        week_one = result["plan"][0]
        for workout in week_one["workouts"]:
            # Already validated by M1 during plan generation
            nl = (
                f"{workout['type']} {workout['distance']} miles "
                f"on {workout['terrain']}"
            )
            parsed = parse_run(nl)
            assert parsed["type"] == workout["type"]
            assert parsed["terrain"] == workout["terrain"]
            assert parsed["distance"] == workout["distance"]
            # Parsed workout should still be safe for the same profile
            as_workout = _parsed_to_workout(parsed)
            validation = validate_workout(profile, as_workout)
            assert validation.get("safe") is True, (
                f"Parsed workout {as_workout} failed M1: {validation.get('reason')}"
            )

    def test_run_log_store_isolated_per_path(self, tmp_path):
        """Each store path is independent; clearing one does not affect another."""
        path_a = str(tmp_path / "a.json")
        path_b = str(tmp_path / "b.json")
        store_a = RunLogStore(path_a)
        store_b = RunLogStore(path_b)
        store_a.save_run("easy 3 miles", {"type": "easy run", "distance": 3.0, "terrain": "road"})
        store_b.save_run("long 6 miles", {"type": "long run", "distance": 6.0, "terrain": "track"})
        assert len(store_a.get_runs()) == 1
        assert len(store_b.get_runs()) == 1
        store_b.clear()
        assert len(store_a.get_runs()) == 1
        assert len(store_b.get_runs()) == 0
