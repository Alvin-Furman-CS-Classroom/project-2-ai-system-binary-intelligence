"""Tests for plan vs log adherence (src.pipeline.adherence)."""

from datetime import datetime, timedelta

import pytest

from src.pipeline.adherence import compute_week_adherence, motivation_with_plan_adherence


def _entry(logged_at: str, distance: float) -> dict:
    return {
        "id": "run_x",
        "logged_at": logged_at,
        "parsed": {"distance": distance, "terrain": "road", "sentiment": "neutral"},
    }


class TestComputeWeekAdherence:
    def test_perfect_when_log_matches_sessions_and_miles(self):
        plan_week = {
            "week": 1,
            "total_miles": 10.0,
            "workouts": [
                {"distance": 5.0, "type": "easy run", "terrain": "road"},
                {"distance": 5.0, "type": "easy run", "terrain": "road"},
            ],
        }
        now = datetime(2026, 3, 15, 12, 0, 0)
        e1 = _entry((now - timedelta(days=1)).isoformat(), 5.0)
        e2 = _entry((now - timedelta(days=2)).isoformat(), 5.0)
        r = compute_week_adherence(plan_week, [e1, e2], days_window=7, now=now)
        assert r["adherence_percent"] == 100.0
        assert r["logged_sessions_in_window"] == 2
        assert r["prescribed_sessions"] == 2

    def test_low_when_fewer_runs_than_prescribed(self):
        plan_week = {
            "total_miles": 20.0,
            "workouts": [{"distance": 10}] * 4,
        }
        now = datetime(2026, 3, 15, 12, 0, 0)
        only = _entry((now - timedelta(days=1)).isoformat(), 5.0)
        r = compute_week_adherence(plan_week, [only], days_window=7, now=now)
        assert r["adherence_percent"] < 100.0
        assert r["logged_sessions_in_window"] == 1
        assert r["prescribed_sessions"] == 4


class TestMotivationWithPlanAdherence:
    def test_merges_adherence_into_motivation(self):
        profile = {
            "planner": {"race_date": "2026-12-01"},
            "paths": {"run_log": "data/run_log.json"},
        }
        plan_week = {"total_miles": 6.0, "workouts": [{"distance": 3}, {"distance": 3}]}
        history = [
            {"distance": 3, "pace": 10, "terrain": "road", "sentiment": "positive"},
        ]
        m = motivation_with_plan_adherence(
            profile,
            history,
            plan_week,
            base_motivation=None,
            run_entries=[],
            days_window=7,
        )
        assert "adherence_percent" in m
        assert 0 <= m["adherence_percent"] <= 100
        assert m["days_to_race"] >= 0
        assert len(m["terrain_last_week"]) >= 1
