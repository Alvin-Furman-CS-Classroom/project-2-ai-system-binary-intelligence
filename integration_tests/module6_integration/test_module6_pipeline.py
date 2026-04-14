"""
Integration: profile-shaped dict -> pipeline_predict_race_readiness -> Module 6 outputs.

Uses an isolated ``tmp_path`` for ``data/module6`` artifacts (CSV + pickle).
"""

from pathlib import Path

from src.pipeline import (
    PROFILE_SCHEMA_VERSION,
    pipeline_predict_race_readiness,
)


def _minimal_profile():
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "name": "Integration",
        "paths": {"run_log": "data/run_log.json"},
        "planner": {
            "goal": "complete marathon",
            "race_date": "2025-12-01",
            "days_per_week": 4,
            "current_weekly_miles": 20,
            "experience": "intermediate",
            "available_terrain": ["road", "trail"],
        },
        "progression_defaults": {
            "fatigue_score": 0.25,
            "next_workout_type": "easy run",
            "default_terrain": "road",
        },
        "module1_runner": {
            "experience_level": "intermediate",
            "weekly_mileage": 20,
            "injuries": [],
            "symptoms": [],
            "pain_level": "none",
            "cleared_by_doctor": True,
            "fully_recovered": True,
            "sleep_quality": "good",
            "hydrated": True,
            "rest_days_this_week": 2,
            "days_trained_this_week": 3,
            "proper_footwear": True,
            "weather": "normal",
        },
    }


def test_pipeline_predict_race_readiness_builds_snapshot_and_returns_keys(tmp_path: Path):
    p = _minimal_profile()
    p["age"] = 33
    p["race_goal"] = {
        "target_time": "4:10:00",
        "terrain": "road",
        "distance": "marathon",
    }
    out = pipeline_predict_race_readiness(
        p,
        history=[
            {
                "date": "2026-02-01",
                "distance": 7.0,
                "pace": 8.8,
                "terrain": "road",
                "sentiment": "positive",
            },
        ],
        module6_dir=tmp_path,
        auto_train=True,
    )
    assert set(out.keys()) >= {
        "predicted_finish",
        "confidence_interval",
        "readiness_score",
        "recommendations",
    }
    assert isinstance(out["recommendations"], list)
