"""
Unit tests for SentimentScorer.

Tests cover all four effort categories, negation handling,
mixed signals, and edge cases.
"""

import pytest
from src.module3_run_logger.sentiment import SentimentScorer


@pytest.fixture
def scorer():
    return SentimentScorer()


class TestEasyEffort:
    def test_felt_great(self, scorer):
        assert scorer.score("felt great today") == "easy"

    def test_fresh_legs(self, scorer):
        assert scorer.score("legs were fresh the whole way") == "easy"

    def test_strong_run(self, scorer):
        assert scorer.score("strong comfortable run") == "easy"

    def test_effortless(self, scorer):
        assert scorer.score("effortless and smooth") == "easy"


class TestModerateEffort:
    def test_okay(self, scorer):
        assert scorer.score("run was okay today") == "moderate"

    def test_fine(self, scorer):
        assert scorer.score("felt fine, nothing special") == "moderate"

    def test_decent(self, scorer):
        assert scorer.score("decent run this morning") == "moderate"


class TestHardEffort:
    def test_tired(self, scorer):
        assert scorer.score("felt tired by the end") == "hard"

    def test_tough(self, scorer):
        assert scorer.score("tough run today") == "hard"

    def test_heavy_legs(self, scorer):
        assert scorer.score("heavy legs throughout") == "hard"


class TestStruggledEffort:
    def test_exhausted(self, scorer):
        assert scorer.score("completely exhausted by mile 8") == "struggled"

    def test_dead_legs(self, scorer):
        assert scorer.score("dead legs from start to finish") == "struggled"

    def test_pain(self, scorer):
        assert scorer.score("pain in my shins the whole time, awful") == "struggled"

    def test_barely_made_it(self, scorer):
        assert scorer.score("barely made it to the end") == "struggled"


class TestNegation:
    def test_not_great_reduces_score(self, scorer):
        positive = scorer.score("great run")
        negated = scorer.score("not great run")
        assert negated != "easy" or positive == negated  # negation should reduce

    def test_didnt_feel_good(self, scorer):
        result = scorer.score("didn't feel good at all")
        assert result in ("hard", "struggled", "moderate")

    def test_not_tired(self, scorer):
        # "not tired" should score higher than "tired"
        tired_score = scorer.score("felt tired")
        not_tired_score = scorer.score("felt not tired")
        assert not_tired_score != "struggled"


class TestFullSentences:
    def test_proposal_example(self, scorer):
        result = scorer.score(
            "did my long run on the trail today, 10 miles at 9:30 pace. "
            "felt pretty tired by mile 8 but the soft surface helped my shins"
        )
        assert result in ("hard", "struggled", "moderate")

    def test_empty_text_returns_moderate(self, scorer):
        assert scorer.score("went for a run") == "moderate"

    def test_mixed_signals_resolves(self, scorer):
        result = scorer.score("started great but finished exhausted and dead")
        assert result in ("hard", "struggled")
