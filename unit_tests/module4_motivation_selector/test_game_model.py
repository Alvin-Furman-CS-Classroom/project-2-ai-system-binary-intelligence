"""
Unit tests for Module 4 game model.

Tests runner state inference, strategy scoring, best response selection,
overreaching (high struggle + high adherence → burnout_risk), and race
proximity for bored state.
"""

import pytest
from src.module4_motivation_selector.game_model import (
    infer_runner_state,
    compute_strategy_scores,
    StrategyScores,
    COACH_STRATEGIES,
    RUNNER_STATES,
)
from src.module4_motivation_selector.input_validation import (
    MotivationContext,
    validate_and_normalize_context,
)


def _ctx(
    current_streak: int = 0,
    recent_sentiments: list | None = None,
    terrain_last_week: list | None = None,
    adherence_percent: float = 80.0,
    days_to_race: int = 45,
) -> MotivationContext:
    return validate_and_normalize_context({
        "current_streak": current_streak,
        "recent_sentiments": recent_sentiments or ["neutral"],
        "terrain_last_week": terrain_last_week or ["road"],
        "adherence_percent": adherence_percent,
        "days_to_race": days_to_race,
    })


class TestInferRunnerState:
    """Runner state inference from context."""

    def test_engaged_good_sentiments_high_adherence(self):
        ctx = _ctx(recent_sentiments=["good", "good"], adherence_percent=95)
        assert infer_runner_state(ctx) == "engaged"

    def test_burnout_risk_struggled_low_adherence(self):
        ctx = _ctx(recent_sentiments=["struggled", "struggled"], adherence_percent=50)
        assert infer_runner_state(ctx) == "burnout_risk"

    def test_burnout_risk_overreaching_high_struggle_high_adherence(self):
        """Overreaching: high struggle count + high adherence → burnout_risk."""
        ctx = _ctx(
            recent_sentiments=["struggled", "struggled", "struggled"],
            adherence_percent=95,
        )
        assert infer_runner_state(ctx) == "burnout_risk"

    def test_bored_monotonous_terrain(self):
        ctx = _ctx(
            recent_sentiments=["neutral", "neutral"],
            terrain_last_week=["treadmill", "treadmill", "treadmill"],
            adherence_percent=85,
        )
        assert infer_runner_state(ctx) == "bored"

    def test_frazzled_default(self):
        ctx = _ctx(recent_sentiments=["good", "struggled"], adherence_percent=75)
        assert infer_runner_state(ctx) == "frazzled"


class TestStrategyScores:
    """Payoff scores and best response."""

    def test_best_strategy_returns_highest_score(self):
        scores = StrategyScores(scores={
            "push_harder": 1.0,
            "maintain": 3.0,
            "encourage_rest": 2.0,
            "encourage_variety": 2.5,
        })
        assert scores.best_strategy() == "maintain"

    def test_tie_break_by_order(self):
        scores = StrategyScores(scores={
            "push_harder": 2.0,
            "maintain": 2.0,
            "encourage_rest": 2.0,
            "encourage_variety": 2.0,
        })
        assert scores.best_strategy() == "push_harder"

    def test_engaged_favors_push_harder(self):
        ctx = _ctx(recent_sentiments=["good", "good"], adherence_percent=95)
        result = compute_strategy_scores(ctx)
        assert result.scores["push_harder"] > result.scores["encourage_rest"]

    def test_burnout_risk_favors_encourage_rest(self):
        ctx = _ctx(
            recent_sentiments=["struggled", "struggled"],
            adherence_percent=95,
        )
        result = compute_strategy_scores(ctx)
        assert result.scores["encourage_rest"] > result.scores["push_harder"]
        assert result.scores["push_harder"] < 0

    def test_bored_favors_encourage_variety(self):
        ctx = _ctx(
            recent_sentiments=["neutral", "neutral"],
            terrain_last_week=["treadmill", "treadmill", "treadmill"],
            adherence_percent=85,
        )
        result = compute_strategy_scores(ctx)
        assert result.scores["encourage_variety"] >= result.scores["maintain"]


class TestRaceProximityBored:
    """Bored runner near race day: maintain preferred over variety."""

    def test_bored_7_days_to_race_maintain_over_variety(self):
        """Bored state with 7 days to race should favor maintain over encourage_variety."""
        ctx = _ctx(
            recent_sentiments=["neutral", "neutral"],
            terrain_last_week=["treadmill", "treadmill", "treadmill"],
            adherence_percent=85,
            days_to_race=7,
        )
        result = compute_strategy_scores(ctx)
        # maintain gets +1.0, encourage_variety gets -0.5 when bored and days<=14
        assert result.scores["maintain"] > result.scores["encourage_variety"]
