"""
Unit tests for Module 4 input validation.

Tests validation of context dict: current_streak, adherence_percent,
days_to_race, recent_sentiments, terrain_last_week. Verifies ValueError
on invalid input (negative values, unknown terrain, empty terrain list).
"""

import pytest
from src.module4_motivation_selector.input_validation import (
    validate_and_normalize_context,
    MotivationContext,
    KNOWN_TERRAINS,
    SENTIMENT_GOOD,
)


class TestValidContext:
    """Valid context passes and normalizes correctly."""

    def test_proposal_example(self):
        ctx = validate_and_normalize_context({
            "current_streak": 18,
            "recent_sentiments": ["good", "good", "struggled"],
            "terrain_last_week": ["treadmill", "treadmill", "treadmill"],
            "adherence_percent": 85,
            "days_to_race": 45,
        })
        assert ctx.current_streak == 18
        assert ctx.recent_sentiments == ["good", "good", "struggled"]
        assert ctx.terrain_last_week == ["treadmill", "treadmill", "treadmill"]
        assert ctx.adherence_percent == 85.0
        assert ctx.days_to_race == 45

    def test_excellent_sentiment_normalizes_to_good(self):
        """Module 3's 'excellent' label must normalize to 'good' (bug fix)."""
        ctx = validate_and_normalize_context({
            "current_streak": 5,
            "recent_sentiments": ["excellent", "excellent"],
            "terrain_last_week": ["road"],
            "adherence_percent": 100,
            "days_to_race": 60,
        })
        assert ctx.recent_sentiments == ["good", "good"]

    def test_positive_sentiment_normalizes_to_good(self):
        """Module 3 sentiment 'positive' maps to 'good'."""
        ctx = validate_and_normalize_context({
            "current_streak": 0,
            "recent_sentiments": ["positive"],
            "terrain_last_week": ["track"],
            "adherence_percent": 90,
            "days_to_race": 30,
        })
        assert ctx.recent_sentiments == ["good"]

    def test_easy_effort_normalizes_to_good(self):
        """Module 3 effort 'easy' maps to 'good'."""
        ctx = validate_and_normalize_context({
            "current_streak": 3,
            "recent_sentiments": ["easy", "moderate"],
            "terrain_last_week": ["road", "trail"],
            "adherence_percent": 80,
            "days_to_race": 90,
        })
        assert ctx.recent_sentiments == ["good", "neutral"]

    def test_all_valid_terrains_accepted(self):
        for terrain in KNOWN_TERRAINS:
            ctx = validate_and_normalize_context({
                "current_streak": 0,
                "recent_sentiments": ["neutral"],
                "terrain_last_week": [terrain],
                "adherence_percent": 50,
                "days_to_race": 14,
            })
            assert ctx.terrain_last_week == [terrain]


class TestNumericValidation:
    """Numeric fields raise ValueError on invalid values."""

    def test_negative_streak_raises(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            validate_and_normalize_context({
                "current_streak": -5,
                "recent_sentiments": ["good"],
                "terrain_last_week": ["road"],
                "adherence_percent": 80,
                "days_to_race": 30,
            })

    def test_streak_non_int_raises(self):
        with pytest.raises(ValueError, match="current_streak"):
            validate_and_normalize_context({
                "current_streak": "five",
                "recent_sentiments": ["good"],
                "terrain_last_week": ["road"],
                "adherence_percent": 80,
                "days_to_race": 30,
            })

    def test_adherence_out_of_range_raises(self):
        with pytest.raises(ValueError, match="0 and 100"):
            validate_and_normalize_context({
                "current_streak": 0,
                "recent_sentiments": ["good"],
                "terrain_last_week": ["road"],
                "adherence_percent": 150,
                "days_to_race": 30,
            })

    def test_adherence_negative_raises(self):
        with pytest.raises(ValueError, match="0 and 100"):
            validate_and_normalize_context({
                "current_streak": 0,
                "recent_sentiments": ["good"],
                "terrain_last_week": ["road"],
                "adherence_percent": -10,
                "days_to_race": 30,
            })

    def test_days_to_race_negative_raises(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            validate_and_normalize_context({
                "current_streak": 0,
                "recent_sentiments": ["good"],
                "terrain_last_week": ["road"],
                "adherence_percent": 80,
                "days_to_race": -7,
            })


class TestTerrainValidation:
    """Terrain must be valid and non-empty."""

    def test_unknown_terrain_raises(self):
        with pytest.raises(ValueError, match="Unknown terrain"):
            validate_and_normalize_context({
                "current_streak": 0,
                "recent_sentiments": ["good"],
                "terrain_last_week": ["moon"],
                "adherence_percent": 80,
                "days_to_race": 30,
            })

    def test_empty_terrain_list_raises(self):
        with pytest.raises(ValueError, match="at least one valid terrain"):
            validate_and_normalize_context({
                "current_streak": 0,
                "recent_sentiments": ["good"],
                "terrain_last_week": [],
                "adherence_percent": 80,
                "days_to_race": 30,
            })

    def test_all_falsy_terrain_raises(self):
        with pytest.raises(ValueError, match="at least one valid terrain"):
            validate_and_normalize_context({
                "current_streak": 0,
                "recent_sentiments": ["good"],
                "terrain_last_week": ["", None, "  "],
                "adherence_percent": 80,
                "days_to_race": 30,
            })


class TestSentimentDefaults:
    """Empty or missing sentiments get default."""

    def test_empty_sentiments_default_to_neutral(self):
        ctx = validate_and_normalize_context({
            "current_streak": 0,
            "recent_sentiments": [],
            "terrain_last_week": ["road"],
            "adherence_percent": 80,
            "days_to_race": 30,
        })
        assert ctx.recent_sentiments == ["neutral"]

    def test_missing_sentiments_default_to_neutral(self):
        ctx = validate_and_normalize_context({
            "current_streak": 0,
            "terrain_last_week": ["road"],
            "adherence_percent": 80,
            "days_to_race": 30,
        })
        assert ctx.recent_sentiments == ["neutral"]
