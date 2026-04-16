"""
Unit tests for Module 4 selector (public API).

Tests select_motivation_strategy (simple) and select_motivation_strategy_detailed,
output structure, reasoning includes payoff scores, and BR_coach language.
"""

import pytest
from src.module4_motivation_selector import (
    select_motivation_strategy,
    select_motivation_strategy_detailed,
)


def _valid_context():
    return {
        "current_streak": 18,
        "recent_sentiments": ["good", "good", "struggled"],
        "terrain_last_week": ["treadmill", "treadmill", "treadmill"],
        "adherence_percent": 85,
        "days_to_race": 45,
    }


class TestSelectMotivationStrategy:
    """Simple API returns only strategy, message_tone, reasoning."""

    def test_returns_required_keys(self):
        result = select_motivation_strategy(_valid_context())
        assert set(result.keys()) == {"strategy", "message_tone", "reasoning"}

    def test_strategy_in_valid_set(self):
        result = select_motivation_strategy(_valid_context())
        assert result["strategy"] in (
            "push_harder",
            "maintain",
            "encourage_rest",
            "encourage_variety",
        )

    def test_reasoning_non_empty(self):
        result = select_motivation_strategy(_valid_context())
        assert len(result["reasoning"]) > 0
        assert "runner" in result["reasoning"].lower() or "adherence" in result["reasoning"].lower()


class TestSelectMotivationStrategyDetailed:
    """Detailed API includes scores and inferred_state."""

    def test_returns_scores_and_inferred_state(self):
        result = select_motivation_strategy_detailed(_valid_context())
        assert "scores" in result
        assert "inferred_state" in result
        assert result["inferred_state"] in (
            "engaged",
            "mixed",
            "bored",
            "burnout_risk",
        )

    def test_scores_has_all_strategies(self):
        result = select_motivation_strategy_detailed(_valid_context())
        for s in ("push_harder", "maintain", "encourage_rest", "encourage_variety"):
            assert s in result["scores"]
            assert isinstance(result["scores"][s], (int, float))

    def test_reasoning_references_payoff_and_br_coach(self):
        """Reasoning should connect to payoff scores and BR_coach concept."""
        result = select_motivation_strategy_detailed(_valid_context())
        reasoning = result["reasoning"]
        # Should mention payoff or BR_coach when there's a second-best
        assert "payoff" in reasoning.lower() or "br_coach" in reasoning.lower()

    def test_best_strategy_matches_highest_score(self):
        result = select_motivation_strategy_detailed(_valid_context())
        best = result["strategy"]
        scores = result["scores"]
        for s, score in scores.items():
            assert score <= scores[best] or s == best
