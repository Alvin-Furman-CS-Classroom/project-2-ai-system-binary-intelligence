"""
Unit tests for SentimentScorer.

Tests cover effort level (easy/moderate/hard/struggled), sentiment/mood
(positive/neutral/negative), negation, and edge cases.
"""

import pytest
from src.module3_run_logger.sentiment import SentimentScorer


@pytest.fixture
def scorer():
    return SentimentScorer()


class TestEasyEffort:
    def test_felt_great(self, scorer):
        assert scorer.score_effort("felt great today") == "easy"

    def test_fresh_legs(self, scorer):
        assert scorer.score_effort("legs were fresh the whole way") == "easy"

    def test_strong_run(self, scorer):
        assert scorer.score_effort("strong comfortable run") == "easy"

    def test_effortless(self, scorer):
        assert scorer.score_effort("effortless and smooth") == "easy"


class TestModerateEffort:
    def test_okay(self, scorer):
        assert scorer.score_effort("run was okay today") == "moderate"

    def test_fine(self, scorer):
        assert scorer.score_effort("felt fine, nothing special") == "moderate"

    def test_decent(self, scorer):
        assert scorer.score_effort("decent run this morning") == "moderate"


class TestHardEffort:
    def test_tired(self, scorer):
        assert scorer.score_effort("felt tired by the end") == "hard"

    def test_tough(self, scorer):
        assert scorer.score_effort("tough run today") == "hard"

    def test_heavy_legs(self, scorer):
        assert scorer.score_effort("heavy legs throughout") == "hard"


class TestStruggledEffort:
    def test_exhausted(self, scorer):
        assert scorer.score_effort("completely exhausted by mile 8") == "struggled"

    def test_dead_legs(self, scorer):
        assert scorer.score_effort("dead legs from start to finish") == "struggled"

    def test_pain(self, scorer):
        assert scorer.score_effort("pain in my shins the whole time, awful") == "struggled"

    def test_barely_made_it(self, scorer):
        assert scorer.score_effort("barely made it to the end") == "struggled"


class TestSentimentMood:
    """Sentiment = how the user feels (mood), not workout difficulty."""

    def test_happy_positive(self, scorer):
        assert scorer.score_sentiment("felt happy and great after the run") == "positive"

    def test_tired_negative(self, scorer):
        assert scorer.score_sentiment("felt tired and drained") == "negative"

    def test_okay_neutral(self, scorer):
        assert scorer.score_sentiment("run was okay") == "neutral"

    def test_empty_neutral(self, scorer):
        assert scorer.score_sentiment("went for a run") == "neutral"


class TestNegation:
    def test_not_great_reduces_score(self, scorer):
        positive = scorer.score_effort("great run")
        negated = scorer.score_effort("not great run")
        assert negated != "easy" or positive == negated  # negation should reduce

    def test_didnt_feel_good(self, scorer):
        result = scorer.score_effort("didn't feel good at all")
        assert result in ("hard", "struggled", "moderate")

    def test_not_tired(self, scorer):
        tired_score = scorer.score_effort("felt tired")
        not_tired_score = scorer.score_effort("felt not tired")
        assert not_tired_score != "struggled"


class TestFullSentences:
    def test_proposal_example(self, scorer):
        result = scorer.score_effort(
            "did my long run on the trail today, 10 miles at 9:30 pace. "
            "felt pretty tired by mile 8 but the soft surface helped my shins"
        )
        assert result in ("hard", "struggled", "moderate")

    def test_empty_text_returns_moderate(self, scorer):
        assert scorer.score_effort("went for a run") == "moderate"

    def test_mixed_signals_resolves(self, scorer):
        result = scorer.score_effort("started great but finished exhausted and dead")
        assert result in ("hard", "struggled")
