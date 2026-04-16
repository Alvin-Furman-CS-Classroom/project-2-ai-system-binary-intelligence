"""Tests for aggregate_history and pace features."""

from src.module6_race_predictor.feature_builder import aggregate_history


def test_empty_history_includes_default_pace():
    agg = aggregate_history([], days_to_race=40, adherence_pct=80.0)
    assert agg["avg_training_pace_min_per_mile"] == 10.0


def test_weighted_average_pace_from_history():
    history = [
        {"date": "2026-01-01", "distance": 4.0, "pace": 10.0, "terrain": "road"},
        {"date": "2026-01-02", "distance": 6.0, "pace": 8.0, "terrain": "road"},
    ]
    agg = aggregate_history(history, days_to_race=50, adherence_pct=90.0)
    # (4*10 + 6*8) / 10 = 8.8
    assert abs(agg["avg_training_pace_min_per_mile"] - 8.8) < 0.01


def test_aggregate_includes_pace_with_single_run():
    agg = aggregate_history(
        [
            {
                "date": "2026-01-01",
                "distance": 5.0,
                "pace": 9.0,
                "terrain": "road",
                "sentiment": "positive",
            }
        ],
        days_to_race=30,
        adherence_pct=85.0,
    )
    assert agg["avg_training_pace_min_per_mile"] == 9.0


def test_runs_without_dates_use_fallback_window():
    """No parseable dates → recent window falls back to last N runs."""
    hist = [
        {"distance": 3.0, "pace": 10.0, "terrain": "road"},
        {"distance": 4.0, "pace": 9.5, "terrain": "road"},
    ]
    agg = aggregate_history(hist, days_to_race=50, adherence_pct=80.0)
    assert agg["avg_weekly_miles_last_12w"] >= 0.0
    assert agg["longest_run_miles"] == 4.0


def test_grass_terrain_maps_to_trail_for_percentages():
    hist = [
        {"date": "2026-01-01", "distance": 5.0, "pace": 9.0, "terrain": "grass"},
    ]
    agg = aggregate_history(hist, days_to_race=40, adherence_pct=85.0)
    assert agg["pct_miles_trail"] >= agg["pct_miles_road"]


def test_treadmill_miles_count_as_track_bucket():
    hist = [
        {"date": "2026-01-01", "distance": 4.0, "pace": 9.0, "terrain": "treadmill"},
    ]
    agg = aggregate_history(hist, days_to_race=30, adherence_pct=85.0)
    assert agg["pct_miles_track"] > 0.0
