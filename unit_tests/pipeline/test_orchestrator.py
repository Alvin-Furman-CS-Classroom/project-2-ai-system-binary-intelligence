"""Tests for src.pipeline (orchestrator + runner profile helpers)."""

from pathlib import Path

import pytest

from src.pipeline import (
    DEFAULT_Q_TABLE_PATH,
    PROFILE_SCHEMA_VERSION,
    apply_module5_to_plan_workout,
    build_module5_context,
    load_runner_profile,
    m3_run_entries_to_m5_history,
    module1_runner_from_profile,
    pipeline_predict_race_readiness,
    planner_config_from_profile,
    save_runner_profile,
)


def _minimal_profile():
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "name": "Test",
        "paths": {"run_log": "data/run_log.json"},
        "planner": {
            "goal": "complete marathon",
            "race_date": "2025-12-01",
            "days_per_week": 4,
            "current_weekly_miles": 15,
            "experience": "beginner",
            "available_terrain": ["road", "trail"],
        },
        "progression_defaults": {
            "fatigue_score": 0.25,
            "next_workout_type": "easy run",
            "default_terrain": "road",
        },
        "module1_runner": {
            "experience_level": "beginner",
            "weekly_mileage": 15,
            "injuries": [],
            "symptoms": [],
            "pain_level": "none",
            "cleared_by_doctor": True,
            "fully_recovered": True,
            "sleep_quality": "good",
            "hydrated": True,
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "hard_workout_yesterday": False,
            "available_terrain": ["road", "trail"],
            "weather": "normal",
            "proper_footwear": True,
            "race_date": "2025-12-01",
        },
    }


class TestM3ToM5History:
    def test_maps_parsed_fields(self):
        entries = [
            {
                "id": "run_001",
                "logged_at": "2026-02-25T20:54:38.657552",
                "parsed": {
                    "type": "easy run",
                    "distance": 5.0,
                    "pace_minutes": 9.5,
                    "terrain": "road",
                    "sentiment": "positive",
                },
            }
        ]
        h = m3_run_entries_to_m5_history(entries)
        assert len(h) == 1
        assert h[0]["distance"] == 5.0
        assert h[0]["pace"] == 9.5
        assert h[0]["terrain"] == "road"
        assert h[0]["sentiment"] == "positive"
        assert h[0]["date"] == "2026-02-25"

    def test_grass_terrain_maps_to_trail(self):
        entries = [
            {
                "logged_at": "2026-02-25T12:00:00",
                "parsed": {"distance": 3.0, "pace_minutes": 10.0, "terrain": "grass", "sentiment": "neutral"},
            }
        ]
        h = m3_run_entries_to_m5_history(entries)
        assert h[0]["terrain"] == "trail"

    def test_null_distance_uses_placeholder(self):
        entries = [
            {
                "logged_at": "2026-02-25T12:00:00",
                "parsed": {"distance": None, "pace_minutes": 10.0, "terrain": "track", "sentiment": "neutral"},
            }
        ]
        h = m3_run_entries_to_m5_history(entries)
        assert h[0]["distance"] == 3.0


class TestProfileHelpers:
    def test_planner_config_round_trip(self):
        p = _minimal_profile()
        cfg = planner_config_from_profile(p)
        assert cfg["race_date"] == "2025-12-01"
        assert cfg["current_weekly_miles"] == 15

    def test_module1_runner_from_profile(self):
        p = _minimal_profile()
        m1 = module1_runner_from_profile(p)
        assert m1["experience_level"] == "beginner"
        assert m1["weekly_mileage"] == 15

    def test_module1_fallback_without_block(self):
        p = _minimal_profile()
        del p["module1_runner"]
        m1 = module1_runner_from_profile(p)
        assert m1["experience_level"] == "beginner"


class TestBuildModule5Context:
    def test_build_with_explicit_history(self):
        p = _minimal_profile()
        hist = [
            {"distance": 4.0, "pace": 9.0, "terrain": "road", "sentiment": "positive", "date": "2026-01-01"}
        ]
        ctx = build_module5_context(p, history=hist)
        assert ctx["history"] == hist
        assert ctx["fatigue_score"] == 0.25
        assert ctx["q_table_path"] == DEFAULT_Q_TABLE_PATH

    def test_paths_q_table_overrides_default(self):
        p = _minimal_profile()
        p["paths"]["q_table"] = "custom/q.json"
        ctx = build_module5_context(p, history=[])
        assert ctx["q_table_path"] == "custom/q.json"


class TestLoadSaveProfile:
    def test_save_load_round_trip(self, tmp_path):
        path = tmp_path / "rp.json"
        data = _minimal_profile()
        save_runner_profile(data, path)
        loaded = load_runner_profile(path)
        assert loaded["name"] == "Test"
        assert loaded["schema_version"] == PROFILE_SCHEMA_VERSION


class TestRepoProfileFile:
    """Smoke: committed template loads if present."""

    def test_default_runner_profile_json_exists(self):
        root = Path(__file__).resolve().parents[2]
        p = root / "data" / "runner_profile.json"
        if not p.exists():
            pytest.skip("data/runner_profile.json not in workspace")
        data = load_runner_profile(p)
        assert data["schema_version"] == PROFILE_SCHEMA_VERSION


class TestPipelinePredictRaceReadiness:
    def test_smoke_empty_history_isolated_module6_dir(self, tmp_path):
        p = _minimal_profile()
        p["age"] = 31
        p["race_goal"] = {"target_time": "4:20:00", "terrain": "road", "distance": "marathon"}
        out = pipeline_predict_race_readiness(
            p,
            history=[],
            module6_dir=tmp_path,
            auto_train=True,
        )
        assert "predicted_finish" in out
        assert "confidence_interval" in out
        assert "readiness_score" in out
        assert isinstance(out["recommendations"], list)


class TestApplyModule5ToPlan:
    def test_patches_distance_terrain_and_recalculates_week(self):
        plan = [
            {
                "week": 1,
                "total_miles": 10.0,
                "workouts": [
                    {"type": "easy run", "distance": 5.0, "terrain": "road"},
                    {"type": "easy run", "distance": 5.0, "terrain": "road"},
                ],
            }
        ]
        rec = {
            "next_distance": 6.6,
            "target_pace": 9.0,
            "suggested_terrain": "trail",
            "reasoning": "adapted",
        }
        new_plan = apply_module5_to_plan_workout(plan, 0, 0, rec)
        assert new_plan[0]["workouts"][0]["distance"] == 6.6
        assert new_plan[0]["workouts"][0]["terrain"] == "trail"
        assert new_plan[0]["total_miles"] == pytest.approx(11.6)
        # Original plan unchanged
        assert plan[0]["workouts"][0]["distance"] == 5.0
