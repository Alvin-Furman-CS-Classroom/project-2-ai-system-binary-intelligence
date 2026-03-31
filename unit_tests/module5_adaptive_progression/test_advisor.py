"""Unit tests for advisor.py — adapt_progression, adapt_progression_detailed, train_on_run."""

import os
import tempfile

import pytest
from src.module5_adaptive_progression.advisor import (
    adapt_progression,
    adapt_progression_detailed,
    train_on_run,
)
from src.module5_adaptive_progression.input_validation import ValidationError
from src.module5_adaptive_progression.mdp import VALID_TERRAINS


def base_context(**overrides):
    ctx = {
        "workout_type":  "easy run",
        "terrain":       "road",
        "fatigue_score": 0.25,
        "history": [
            {"date": "2025-01-01", "distance": 5.0, "pace": 9.5,
             "terrain": "road", "sentiment": "positive"},
            {"date": "2025-01-03", "distance": 5.0, "pace": 9.4,
             "terrain": "trail", "sentiment": "positive"},
        ],
    }
    ctx.update(overrides)
    return ctx


# ---------------------------------------------------------------------------
# adapt_progression — output shape and types
# ---------------------------------------------------------------------------

class TestAdaptProgressionOutputShape:
    def test_returns_dict(self):
        result = adapt_progression(base_context())
        assert isinstance(result, dict)

    def test_required_keys_present(self):
        result = adapt_progression(base_context())
        for key in ("next_distance", "target_pace", "suggested_terrain",
                    "confidence", "reasoning"):
            assert key in result, f"Missing key: {key}"

    def test_next_distance_is_positive_float(self):
        result = adapt_progression(base_context())
        assert isinstance(result["next_distance"], float)
        assert result["next_distance"] > 0

    def test_target_pace_is_positive_float(self):
        result = adapt_progression(base_context())
        assert isinstance(result["target_pace"], float)
        assert result["target_pace"] > 0

    def test_suggested_terrain_is_valid(self):
        result = adapt_progression(base_context())
        assert result["suggested_terrain"] in VALID_TERRAINS

    def test_confidence_in_range(self):
        result = adapt_progression(base_context())
        assert 0.0 <= result["confidence"] <= 1.0

    def test_reasoning_is_non_empty_string(self):
        result = adapt_progression(base_context())
        assert isinstance(result["reasoning"], str)
        assert len(result["reasoning"]) > 10

    def test_new_agent_has_zero_confidence(self):
        result = adapt_progression(base_context())
        assert result["confidence"] == 0.0


# ---------------------------------------------------------------------------
# adapt_progression — behavior with different inputs
# ---------------------------------------------------------------------------

class TestAdaptProgressionBehavior:
    def test_empty_history_still_returns_result(self):
        result = adapt_progression(base_context(history=[]))
        assert result["next_distance"] > 0
        assert result["target_pace"] > 0

    def test_high_fatigue_does_not_crash(self):
        result = adapt_progression(base_context(fatigue_score=0.9))
        assert isinstance(result, dict)

    def test_different_workout_types_handled(self):
        for wt in ("tempo run", "long run", "interval", "recovery run"):
            result = adapt_progression(base_context(workout_type=wt))
            assert result["next_distance"] > 0

    def test_all_terrains_as_input(self):
        for terrain in VALID_TERRAINS:
            result = adapt_progression(base_context(terrain=terrain))
            assert result["suggested_terrain"] in VALID_TERRAINS

    def test_invalid_context_raises(self):
        with pytest.raises(ValidationError):
            adapt_progression({"workout_type": "yoga"})


# ---------------------------------------------------------------------------
# adapt_progression_detailed — additional keys
# ---------------------------------------------------------------------------

class TestAdaptProgressionDetailed:
    def test_returns_all_base_keys(self):
        result = adapt_progression_detailed(base_context())
        for key in ("next_distance", "target_pace", "suggested_terrain",
                    "confidence", "reasoning"):
            assert key in result

    def test_returns_state(self):
        result = adapt_progression_detailed(base_context())
        assert "state" in result
        assert isinstance(result["state"], tuple)
        assert len(result["state"]) == 5

    def test_returns_episode_count(self):
        result = adapt_progression_detailed(base_context())
        assert "episode_count" in result
        assert result["episode_count"] == 0  # fresh engine

    def test_returns_epsilon(self):
        result = adapt_progression_detailed(base_context())
        assert "epsilon" in result
        assert 0 < result["epsilon"] <= 1.0

    def test_returns_q_values_dict(self):
        result = adapt_progression_detailed(base_context())
        assert "q_values" in result
        assert isinstance(result["q_values"], dict)
        assert len(result["q_values"]) == 9  # 3×3 volume × intensity

    def test_returns_sentiment_trend(self):
        result = adapt_progression_detailed(base_context())
        assert "sentiment_trend" in result
        assert result["sentiment_trend"] in ("improving", "declining", "stable", "insufficient_data")

    def test_returns_weekly_miles(self):
        result = adapt_progression_detailed(base_context())
        assert "weekly_miles" in result
        assert result["weekly_miles"] >= 0.0

    def test_state_values_are_strings(self):
        result = adapt_progression_detailed(base_context())
        for v in result["state"]:
            assert isinstance(v, str)


# ---------------------------------------------------------------------------
# train_on_run
# ---------------------------------------------------------------------------

class TestTrainOnRun:
    def base_outcome(self, **overrides):
        outcome = {
            "sentiment":          "positive",
            "fatigue_score_after": 0.35,
            "terrain":            "road",
            "distance_completed":  5.0,
        }
        outcome.update(overrides)
        return outcome

    def test_returns_dict(self):
        result = train_on_run(base_context(), self.base_outcome())
        assert isinstance(result, dict)

    def test_required_keys(self):
        result = train_on_run(base_context(), self.base_outcome())
        for key in ("q_update", "reward", "episode_count", "action", "next_state"):
            assert key in result

    def test_episode_count_increments(self):
        result = train_on_run(base_context(), self.base_outcome())
        assert result["episode_count"] == 1

    def test_positive_outcome_gives_positive_reward(self):
        result = train_on_run(base_context(), self.base_outcome(sentiment="positive"))
        assert result["reward"] > 0

    def test_fatigue_spike_gives_negative_reward(self):
        # Neutral sentiment, no terrain change vs last history entry → injury penalty dominates
        # (positive + variety + high-adherence bonus can otherwise offset −8 to a small positive).
        result = train_on_run(
            base_context(fatigue_score=0.2),
            self.base_outcome(
                sentiment="neutral",
                fatigue_score_after=0.95,
                terrain="trail",
            ),
        )
        assert result["reward"] < 0

    def test_persists_to_file_when_path_given(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            # First training call
            train_on_run(base_context(), self.base_outcome(), q_table_path=path)
            assert os.path.exists(path)
            # Second call should load and continue from first
            result = train_on_run(base_context(), self.base_outcome(), q_table_path=path)
            assert result["episode_count"] == 2
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_invalid_context_raises(self):
        with pytest.raises(ValidationError):
            train_on_run({}, self.base_outcome())

    def test_distance_completed_not_required(self):
        outcome = {"sentiment": "neutral", "fatigue_score_after": 0.4, "terrain": "road"}
        result = train_on_run(base_context(), outcome)
        assert "q_update" in result

    def test_planned_action_overrides_inference(self):
        ctx = base_context()
        out = {
            "sentiment": "negative",
            "fatigue_score_after": 0.4,
            "terrain": "road",
            "distance_completed": 10.0,
            "planned_action": (0, 0),  # HOLD, HOLD — differs from sentiment-based inference
        }
        result = train_on_run(ctx, out)
        assert result["action"] == (0, 0)

    def test_terrain_variety_in_outcome_reflected(self):
        # Running trail after a road run should yield variety reward
        ctx = base_context(terrain="road", history=[
            {"distance": 5.0, "pace": 9.0, "terrain": "road", "sentiment": "positive"},
        ])
        outcome = self.base_outcome(terrain="trail")
        result = train_on_run(ctx, outcome)
        # Reward should include variety bonus
        assert result["reward"] > 0
