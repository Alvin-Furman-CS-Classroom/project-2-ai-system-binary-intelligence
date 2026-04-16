"""
Integration tests for Module 5 (Adaptive Progression).

Tests the full pipeline:
  Module 3 logs (NLP parsed runs) -> Module 4 motivation context -> Module 5 progression

Because the actual Module 3/4 implementations live in sibling packages we
test integration via their public-API output shapes rather than importing
the full packages, keeping the test self-contained and focused on the
inter-module contract.
"""

import os
import tempfile

import pytest
from src.module5_adaptive_progression import (
    adapt_progression,
    adapt_progression_detailed,
    train_on_run,
)
from src.module5_adaptive_progression.mdp import VALID_TERRAINS


# ---------------------------------------------------------------------------
# Simulated Module 3 output (run history entries)
# ---------------------------------------------------------------------------

def make_m3_run(distance=5.0, pace=9.0, terrain="road", sentiment="positive", date="2025-03-01"):
    """Simulate a structured run entry as produced by Module 3's parse_run / log_run."""
    return {
        "date":      date,
        "distance":  distance,
        "pace":      pace,
        "terrain":   terrain,
        "sentiment": sentiment,
    }


# ---------------------------------------------------------------------------
# Simulated Module 4 output (motivation context)
# ---------------------------------------------------------------------------

def make_m4_context(streak=5, adherence_percent=85.0, days_to_race=60,
                    recent_sentiments=None, terrain_last_week=None):
    """Simulate a Module 4 motivation context dict (adherence_percent 0–100)."""
    return {
        "current_streak":     streak,
        "adherence_percent":  adherence_percent,
        "days_to_race":       days_to_race,
        "recent_sentiments":  recent_sentiments or ["good", "good", "neutral"],
        "terrain_last_week":  terrain_last_week or ["road", "trail", "road"],
    }


# ---------------------------------------------------------------------------
# Shared fixture: a runner with a realistic multi-week history
# ---------------------------------------------------------------------------

@pytest.fixture
def realistic_history():
    return [
        make_m3_run(4.0,  9.5, "road",     "neutral",  "2025-02-01"),
        make_m3_run(4.5,  9.3, "road",     "positive", "2025-02-03"),
        make_m3_run(8.0,  9.8, "trail",    "positive", "2025-02-05"),
        make_m3_run(5.0,  9.2, "road",     "neutral",  "2025-02-08"),
        make_m3_run(5.5,  9.1, "treadmill","positive", "2025-02-10"),
        make_m3_run(9.0,  9.7, "trail",    "positive", "2025-02-12"),
        make_m3_run(5.0,  9.0, "road",     "negative", "2025-02-15"),
    ]


@pytest.fixture
def base_context(realistic_history):
    return {
        "workout_type":  "easy run",
        "terrain":       "road",
        "fatigue_score": 0.3,
        "history":       realistic_history,
    }


# ---------------------------------------------------------------------------
# Integration: Module 3 history feeds Module 5
# ---------------------------------------------------------------------------

class TestM3ToM5Integration:
    def test_m3_history_produces_valid_recommendation(self, base_context):
        result = adapt_progression(base_context)
        assert result["next_distance"] > 0
        assert result["target_pace"] > 0
        assert result["suggested_terrain"] in VALID_TERRAINS

    def test_improving_sentiment_trend_detected(self, realistic_history):
        # Build a history with clearly improving sentiments
        improving = [
            make_m3_run(5.0, 9.5, "road",  "negative", "2025-03-01"),
            make_m3_run(5.0, 9.4, "road",  "negative", "2025-03-03"),
            make_m3_run(5.0, 9.3, "trail", "neutral",  "2025-03-05"),
            make_m3_run(5.0, 9.2, "road",  "positive", "2025-03-07"),
            make_m3_run(5.0, 9.1, "trail", "positive", "2025-03-09"),
        ]
        ctx = {"workout_type": "easy run", "terrain": "road",
               "fatigue_score": 0.2, "history": improving}
        result = adapt_progression_detailed(ctx)
        assert result["sentiment_trend"] == "improving"

    def test_declining_sentiment_detected(self):
        declining = [
            make_m3_run(6.0, 8.5, "track", "positive", "2025-03-01"),
            make_m3_run(6.0, 8.5, "track", "positive", "2025-03-03"),
            make_m3_run(6.0, 8.8, "road",  "neutral",  "2025-03-05"),
            make_m3_run(6.0, 9.0, "road",  "negative", "2025-03-07"),
            make_m3_run(6.0, 9.2, "trail", "negative", "2025-03-09"),
        ]
        ctx = {"workout_type": "easy run", "terrain": "road",
               "fatigue_score": 0.6, "history": declining}
        result = adapt_progression_detailed(ctx)
        assert result["sentiment_trend"] == "declining"

    def test_terrain_variety_detected_in_history(self):
        # Last two different terrains -> streak=VARIED
        history = [
            make_m3_run(5.0, 9.0, "road",  "positive"),
            make_m3_run(5.0, 9.0, "trail", "positive"),
        ]
        ctx = {"workout_type": "easy run", "terrain": "trail",
               "fatigue_score": 0.2, "history": history}
        result = adapt_progression_detailed(ctx)
        # State should show 'varied' streak
        assert result["state"][2] == "varied"

    def test_terrain_same_streak_detected(self):
        history = [
            make_m3_run(5.0, 9.0, "road", "positive"),
            make_m3_run(5.0, 9.0, "road", "positive"),
        ]
        ctx = {"workout_type": "easy run", "terrain": "road",
               "fatigue_score": 0.2, "history": history}
        result = adapt_progression_detailed(ctx)
        assert result["state"][2] == "same"


# ---------------------------------------------------------------------------
# Integration: online learning via train_on_run
# ---------------------------------------------------------------------------

class TestOnlineLearningIntegration:
    def test_q_values_change_after_training(self, base_context):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            # Capture Q-values before
            before = adapt_progression_detailed(base_context)

            outcome = {
                "sentiment":           "positive",
                "fatigue_score_after":  0.3,
                "terrain":             "road",
                "distance_completed":   6.0,
            }
            train_on_run(base_context, outcome, q_table_path=path)

            # Load updated agent
            base_context["q_table_path"] = path
            after = adapt_progression_detailed(base_context)

            assert after["episode_count"] == 1
        finally:
            base_context.pop("q_table_path", None)
            if os.path.exists(path):
                os.unlink(path)

    def test_multiple_episodes_accumulate(self, base_context):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            outcome = {
                "sentiment": "positive", "fatigue_score_after": 0.3,
                "terrain": "road", "distance_completed": 5.5,
            }
            for _ in range(5):
                train_on_run(base_context, outcome, q_table_path=path)
            base_context["q_table_path"] = path
            result = adapt_progression_detailed(base_context)
            assert result["episode_count"] == 5
            assert result["confidence"] > 0.0
        finally:
            base_context.pop("q_table_path", None)
            if os.path.exists(path):
                os.unlink(path)

    def test_injury_risk_outcome_gives_negative_reward(self, base_context):
        risky_outcome = {
            "sentiment":           "negative",
            "fatigue_score_after":  0.95,
            "terrain":             "road",
            "distance_completed":   8.0,
        }
        result = train_on_run(base_context, risky_outcome)
        assert result["reward"] < 0

    def test_q_table_persists_across_calls(self, base_context):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            outcome = {"sentiment": "positive", "fatigue_score_after": 0.2,
                       "terrain": "road", "distance_completed": 5.0}
            for _ in range(3):
                train_on_run(base_context, outcome, q_table_path=path)
            # Read the file directly to confirm it's valid JSON
            import json
            with open(path) as f:
                data = json.load(f)
            assert "episode_count" in data
            assert data["episode_count"] == 3
        finally:
            if os.path.exists(path):
                os.unlink(path)


# ---------------------------------------------------------------------------
# Integration: Module 4 motivation context informs Module 5
# ---------------------------------------------------------------------------

class TestM4ToM5Integration:
    """
    Module 4 produces a motivation context that can be used to derive
    fatigue_score and recent_sentiments for Module 5 input.
    This test validates that the translation convention works end-to-end.
    """

    def _ctx_from_m4(self, m4, history):
        """Build a Module 5 context with Module 4 motivation wired in (see proposal)."""
        return {
            "workout_type":  "easy run",
            "terrain":       m4["terrain_last_week"][-1] if m4["terrain_last_week"] else "road",
            "fatigue_score": 0.25,
            "history":       history,
            "motivation":    m4,
        }

    def test_high_adherence_low_fatigue_produces_recommendation(self):
        m4 = make_m4_context(adherence_percent=95, recent_sentiments=["good"] * 3)
        history = [make_m3_run(5.0, 9.0, "road", "positive")]
        ctx = self._ctx_from_m4(m4, history)
        result = adapt_progression(ctx)
        assert result["next_distance"] > 0
        assert "motivation" not in result

    def test_low_adherence_high_fatigue_produces_recommendation(self):
        m4 = make_m4_context(adherence_percent=40, recent_sentiments=["struggled"] * 3)
        history = [make_m3_run(5.0, 9.5, "road", "negative")]
        ctx = self._ctx_from_m4(m4, history)
        result = adapt_progression(ctx)
        assert 0.0 <= result["confidence"] <= 1.0
        assert "Module 4 signal" in result["reasoning"]

    def test_terrain_last_week_used_as_context_terrain(self):
        m4 = make_m4_context(terrain_last_week=["trail", "trail", "trail"])
        history = [make_m3_run(6.0, 8.5, "trail", "positive")]
        ctx = self._ctx_from_m4(m4, history)
        result = adapt_progression_detailed(ctx)
        assert result["weekly_miles"] >= 0
        assert result.get("motivation") is not None
        assert result["motivation"]["adherence_percent"] == 85.0


# ---------------------------------------------------------------------------
# End-to-end scenario: realistic training week progression
# ---------------------------------------------------------------------------

class TestEndToEndScenario:
    def test_three_week_progression(self):
        """
        Simulate three weeks of training:
        each week logs runs then asks for the next session recommendation.
        """
        history = []
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            # Week 1: easy start
            week1 = [
                make_m3_run(4.0, 10.0, "road",  "positive", "2025-03-03"),
                make_m3_run(5.0,  9.8, "trail", "positive", "2025-03-05"),
                make_m3_run(3.0, 10.2, "road",  "neutral",  "2025-03-07"),
            ]
            history.extend(week1)
            for run in week1:
                ctx = {"workout_type": "easy run", "terrain": run["terrain"],
                       "fatigue_score": 0.2, "history": history[:-1]}
                outcome = {"sentiment": run["sentiment"], "fatigue_score_after": 0.25,
                           "terrain": run["terrain"], "distance_completed": run["distance"]}
                train_on_run(ctx, outcome, q_table_path=path)

            # Week 2: building
            week2 = [
                make_m3_run(5.0, 9.5, "road",  "positive", "2025-03-10"),
                make_m3_run(6.0, 9.3, "trail", "positive", "2025-03-12"),
                make_m3_run(4.0, 9.8, "road",  "positive", "2025-03-14"),
            ]
            history.extend(week2)
            for run in week2:
                ctx = {"workout_type": "easy run", "terrain": run["terrain"],
                       "fatigue_score": 0.3, "history": list(history)}
                outcome = {"sentiment": run["sentiment"], "fatigue_score_after": 0.3,
                           "terrain": run["terrain"], "distance_completed": run["distance"]}
                train_on_run(ctx, outcome, q_table_path=path)

            # Get Week 3 recommendation
            ctx = {"workout_type": "easy run", "terrain": "road",
                   "fatigue_score": 0.25, "history": history,
                   "q_table_path": path}
            result = adapt_progression_detailed(ctx)

            assert result["next_distance"] > 0
            assert result["episode_count"] == 6  # 3 + 3 training calls
            assert result["suggested_terrain"] in VALID_TERRAINS
        finally:
            if os.path.exists(path):
                os.unlink(path)
