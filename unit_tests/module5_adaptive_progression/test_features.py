"""Unit tests for features.py — mileage estimation, apply_adjustments, sentiment_trend."""

import pytest
from src.module5_adaptive_progression.features import (
    estimate_weekly_miles,
    get_terrain_sequence,
    apply_adjustments,
    apply_motivation_adjustments,
    extract_baseline,
    recent_sentiments,
    sentiment_trend,
)
from src.module5_adaptive_progression.mdp import VolumeAdjustment, IntensityAdjustment


def make_run(distance=5.0, pace=9.0, terrain="road", sentiment="neutral"):
    return {"distance": distance, "pace": pace, "terrain": terrain, "sentiment": sentiment}


# ---------------------------------------------------------------------------
# estimate_weekly_miles
# ---------------------------------------------------------------------------

class TestEstimateWeeklyMiles:
    def test_empty_history_returns_zero(self):
        assert estimate_weekly_miles([]) == 0.0

    def test_single_run(self):
        assert estimate_weekly_miles([make_run(distance=6.0)]) == pytest.approx(6.0)

    def test_multiple_runs_summed(self):
        runs = [make_run(distance=d) for d in [4, 5, 6, 5, 4]]
        assert estimate_weekly_miles(runs) == pytest.approx(24.0)

    def test_uses_only_last_seven_runs(self):
        # 10 runs, last 7 each have distance 3
        runs = [make_run(distance=100)] * 3 + [make_run(distance=3)] * 7
        result = estimate_weekly_miles(runs)
        assert result == pytest.approx(21.0)


# ---------------------------------------------------------------------------
# get_terrain_sequence
# ---------------------------------------------------------------------------

class TestGetTerrainSequence:
    def test_empty_history(self):
        assert get_terrain_sequence([]) == []

    def test_sequence_preserved(self):
        runs = [make_run(terrain=t) for t in ["road", "trail", "track"]]
        assert get_terrain_sequence(runs) == ["road", "trail", "track"]


# ---------------------------------------------------------------------------
# apply_adjustments
# ---------------------------------------------------------------------------

class TestApplyAdjustments:
    def test_increase_volume(self):
        d, p = apply_adjustments(10.0, 9.0, VolumeAdjustment.INCREASE, IntensityAdjustment.HOLD)
        assert d == pytest.approx(11.0, rel=0.01)
        assert p == pytest.approx(9.0)

    def test_decrease_volume(self):
        d, p = apply_adjustments(10.0, 9.0, VolumeAdjustment.DECREASE, IntensityAdjustment.HOLD)
        assert d == pytest.approx(9.0, rel=0.01)

    def test_hold_volume(self):
        d, p = apply_adjustments(10.0, 9.0, VolumeAdjustment.HOLD, IntensityAdjustment.HOLD)
        assert d == pytest.approx(10.0)

    def test_harder_intensity(self):
        d, p = apply_adjustments(10.0, 9.0, VolumeAdjustment.HOLD, IntensityAdjustment.HARDER)
        assert p < 9.0   # faster pace = smaller value

    def test_easier_intensity(self):
        d, p = apply_adjustments(10.0, 9.0, VolumeAdjustment.HOLD, IntensityAdjustment.EASIER)
        assert p > 9.0   # slower pace = larger value

    def test_hold_intensity(self):
        d, p = apply_adjustments(10.0, 9.0, VolumeAdjustment.HOLD, IntensityAdjustment.HOLD)
        assert p == pytest.approx(9.0)

    def test_combined_increase_harder(self):
        d, p = apply_adjustments(10.0, 8.0, VolumeAdjustment.INCREASE, IntensityAdjustment.HARDER)
        assert d > 10.0
        assert p < 8.0

    def test_combined_decrease_easier(self):
        d, p = apply_adjustments(10.0, 9.0, VolumeAdjustment.DECREASE, IntensityAdjustment.EASIER)
        assert d < 10.0
        assert p > 9.0

    def test_return_values_are_floats(self):
        d, p = apply_adjustments(5, 9, VolumeAdjustment.HOLD, IntensityAdjustment.HOLD)
        assert isinstance(d, float)
        assert isinstance(p, float)


# ---------------------------------------------------------------------------
# extract_baseline
# ---------------------------------------------------------------------------

class TestExtractBaseline:
    def test_empty_history_returns_default(self):
        d, p = extract_baseline([])
        assert d > 0
        assert p > 0

    def test_uses_last_run(self):
        runs = [make_run(distance=4.0, pace=9.0), make_run(distance=7.0, pace=8.0)]
        d, p = extract_baseline(runs)
        assert d == pytest.approx(7.0)
        assert p == pytest.approx(8.0)


# ---------------------------------------------------------------------------
# recent_sentiments
# ---------------------------------------------------------------------------

class TestRecentSentiments:
    def test_returns_last_n(self):
        runs = [make_run(sentiment=s) for s in ["negative", "neutral", "positive", "positive"]]
        result = recent_sentiments(runs, n=3)
        assert result == ["neutral", "positive", "positive"]

    def test_empty_history(self):
        assert recent_sentiments([]) == []

    def test_fewer_runs_than_n(self):
        runs = [make_run(sentiment="positive")]
        result = recent_sentiments(runs, n=5)
        assert result == ["positive"]


# ---------------------------------------------------------------------------
# sentiment_trend
# ---------------------------------------------------------------------------

class TestSentimentTrend:
    def test_insufficient_data(self):
        assert sentiment_trend([make_run(sentiment="positive")]) == "insufficient_data"

    def test_empty_history(self):
        assert sentiment_trend([]) == "insufficient_data"

    def test_improving_trend(self):
        runs = [
            make_run(sentiment="negative"),
            make_run(sentiment="negative"),
            make_run(sentiment="positive"),
            make_run(sentiment="positive"),
            make_run(sentiment="positive"),
        ]
        assert sentiment_trend(runs) == "improving"

    def test_declining_trend(self):
        runs = [
            make_run(sentiment="positive"),
            make_run(sentiment="positive"),
            make_run(sentiment="negative"),
            make_run(sentiment="negative"),
            make_run(sentiment="negative"),
        ]
        assert sentiment_trend(runs) == "declining"

    def test_stable_trend(self):
        runs = [make_run(sentiment="neutral") for _ in range(5)]
        assert sentiment_trend(runs) == "stable"


# ---------------------------------------------------------------------------
# apply_motivation_adjustments — adherence no longer hard-trims volume (Q/Reward path)
# ---------------------------------------------------------------------------

class TestApplyMotivationAdjustments:
    def test_low_adherence_does_not_apply_legacy_volume_trim(self):
        """Previously nd *= 0.93 for low adherence; volume is now learned via state/reward."""
        motivation = {
            "adherence_percent": 40.0,
            "days_to_race": 120,
            "current_streak": 2,
            "recent_sentiments": ["good", "good", "neutral"],
            "terrain_last_week": ["road", "trail", "track"],
        }
        nd, tp, terrain, note = apply_motivation_adjustments(
            10.0, 9.0, "road", motivation, base_distance=10.0,
        )
        assert nd == pytest.approx(10.0)
        assert tp == pytest.approx(9.0)
        assert terrain == "road"
        assert note == ""
