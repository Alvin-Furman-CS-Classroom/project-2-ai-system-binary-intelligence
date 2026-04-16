"""Unit tests for input_validation.py."""

import pytest
from src.module5_adaptive_progression.input_validation import (
    validate_context,
    ValidationError,
)


def base_context(**overrides):
    ctx = {
        "workout_type":  "tempo run",
        "terrain":       "track",
        "fatigue_score": 0.3,
        "history": [
            {"distance": 5.0, "pace": 8.5, "terrain": "track", "sentiment": "positive"},
        ],
    }
    ctx.update(overrides)
    return ctx


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestValidContextAccepted:
    def test_minimal_valid_context(self):
        result = validate_context(base_context())
        assert result["workout_type"] == "tempo run"
        assert result["terrain"] == "track"
        assert result["fatigue_score"] == pytest.approx(0.3)

    def test_all_workout_types_accepted(self):
        valid_types = [
            "easy run", "tempo run", "long run", "interval",
            "recovery run", "hill workout", "fartlek", "race",
            "time trial", "cross training",
        ]
        for wt in valid_types:
            result = validate_context(base_context(workout_type=wt))
            assert result["workout_type"] == wt

    def test_all_terrains_accepted(self):
        for terrain in ("road", "track", "treadmill", "trail"):
            result = validate_context(base_context(terrain=terrain))
            assert result["terrain"] == terrain

    def test_fatigue_score_at_zero(self):
        result = validate_context(base_context(fatigue_score=0.0))
        assert result["fatigue_score"] == 0.0

    def test_fatigue_score_at_one(self):
        result = validate_context(base_context(fatigue_score=1.0))
        assert result["fatigue_score"] == 1.0

    def test_empty_history_accepted(self):
        result = validate_context(base_context(history=[]))
        assert result["history"] == []

    def test_multiple_history_entries(self):
        history = [
            {"distance": 4.0, "pace": 9.0, "terrain": "road", "sentiment": "neutral"},
            {"distance": 6.0, "pace": 8.5, "terrain": "trail", "sentiment": "positive"},
        ]
        result = validate_context(base_context(history=history))
        assert len(result["history"]) == 2

    def test_case_normalization_workout_type(self):
        result = validate_context(base_context(workout_type="TEMPO RUN"))
        assert result["workout_type"] == "tempo run"

    def test_case_normalization_terrain(self):
        result = validate_context(base_context(terrain="TRACK"))
        assert result["terrain"] == "track"

    def test_optional_q_table_path_accepted(self):
        result = validate_context(base_context(q_table_path="/tmp/qtable.json"))
        assert result["q_table_path"] == "/tmp/qtable.json"

    def test_q_table_path_defaults_to_none(self):
        result = validate_context(base_context())
        assert result["q_table_path"] is None

    def test_history_date_field_optional(self):
        history = [{"distance": 5.0, "pace": 8.0, "terrain": "road", "sentiment": "neutral"}]
        result = validate_context(base_context(history=history))
        assert result["history"][0]["date"] == ""

    def test_history_with_date_preserved(self):
        history = [{"date": "2025-03-01", "distance": 5.0, "pace": 8.0,
                    "terrain": "road", "sentiment": "positive"}]
        result = validate_context(base_context(history=history))
        assert result["history"][0]["date"] == "2025-03-01"


# ---------------------------------------------------------------------------
# Invalid context top level
# ---------------------------------------------------------------------------

class TestInvalidContextTopLevel:
    def test_non_dict_raises(self):
        with pytest.raises(ValidationError):
            validate_context("not a dict")

    def test_missing_workout_type(self):
        ctx = base_context()
        del ctx["workout_type"]
        with pytest.raises(ValidationError, match="workout_type"):
            validate_context(ctx)

    def test_missing_terrain(self):
        ctx = base_context()
        del ctx["terrain"]
        with pytest.raises(ValidationError, match="terrain"):
            validate_context(ctx)

    def test_missing_fatigue_score(self):
        ctx = base_context()
        del ctx["fatigue_score"]
        with pytest.raises(ValidationError, match="fatigue_score"):
            validate_context(ctx)

    def test_missing_history(self):
        ctx = base_context()
        del ctx["history"]
        with pytest.raises(ValidationError, match="history"):
            validate_context(ctx)

    def test_unknown_workout_type(self):
        with pytest.raises(ValidationError, match="workout_type"):
            validate_context(base_context(workout_type="swimming"))

    def test_unknown_terrain(self):
        with pytest.raises(ValidationError, match="terrain"):
            validate_context(base_context(terrain="beach"))

    def test_fatigue_score_too_low(self):
        with pytest.raises(ValidationError, match="fatigue_score"):
            validate_context(base_context(fatigue_score=-0.1))

    def test_fatigue_score_too_high(self):
        with pytest.raises(ValidationError, match="fatigue_score"):
            validate_context(base_context(fatigue_score=1.1))

    def test_fatigue_score_not_a_number(self):
        with pytest.raises(ValidationError):
            validate_context(base_context(fatigue_score="high"))

    def test_history_not_a_list(self):
        with pytest.raises(ValidationError, match="list"):
            validate_context(base_context(history="not a list"))

    def test_q_table_path_not_a_string(self):
        with pytest.raises(ValidationError):
            validate_context(base_context(q_table_path=42))


# ---------------------------------------------------------------------------
# Invalid history entries
# ---------------------------------------------------------------------------

class TestInvalidHistoryEntries:
    def _bad_history(self, **field_overrides):
        entry = {"distance": 5.0, "pace": 8.5, "terrain": "track", "sentiment": "positive"}
        entry.update(field_overrides)
        return [entry]

    def test_history_entry_not_a_dict(self):
        with pytest.raises(ValidationError):
            validate_context(base_context(history=["not a dict"]))

    def test_missing_distance(self):
        history = [{"pace": 8.5, "terrain": "track", "sentiment": "positive"}]
        with pytest.raises(ValidationError, match="distance"):
            validate_context(base_context(history=history))

    def test_missing_pace(self):
        history = [{"distance": 5.0, "terrain": "track", "sentiment": "positive"}]
        with pytest.raises(ValidationError, match="pace"):
            validate_context(base_context(history=history))

    def test_missing_terrain_in_history(self):
        history = [{"distance": 5.0, "pace": 8.5, "sentiment": "positive"}]
        with pytest.raises(ValidationError, match="terrain"):
            validate_context(base_context(history=history))

    def test_missing_sentiment(self):
        history = [{"distance": 5.0, "pace": 8.5, "terrain": "track"}]
        with pytest.raises(ValidationError, match="sentiment"):
            validate_context(base_context(history=history))

    def test_negative_distance(self):
        with pytest.raises(ValidationError, match="distance"):
            validate_context(base_context(history=self._bad_history(distance=-1.0)))

    def test_zero_distance(self):
        with pytest.raises(ValidationError, match="distance"):
            validate_context(base_context(history=self._bad_history(distance=0.0)))

    def test_negative_pace(self):
        with pytest.raises(ValidationError, match="pace"):
            validate_context(base_context(history=self._bad_history(pace=-5.0)))

    def test_invalid_terrain_in_history(self):
        with pytest.raises(ValidationError, match="terrain"):
            validate_context(base_context(history=self._bad_history(terrain="moon")))

    def test_informal_sentiment_mapped_to_canonical(self):
        history = [{"distance": 5.0, "pace": 8.5, "terrain": "track", "sentiment": "exhausted"}]
        result = validate_context(base_context(history=history))
        assert result["history"][0]["sentiment"] == "negative"

    def test_good_and_excellent_map_to_positive(self):
        h = [
            {"distance": 5.0, "pace": 8.5, "terrain": "track", "sentiment": "good"},
            {"distance": 5.0, "pace": 8.5, "terrain": "road", "sentiment": "excellent"},
        ]
        result = validate_context(base_context(history=h))
        assert result["history"][0]["sentiment"] == "positive"
        assert result["history"][1]["sentiment"] == "positive"

    def test_unknown_sentiment_defaults_to_neutral(self):
        history = [{"distance": 5.0, "pace": 8.5, "terrain": "track", "sentiment": "asdf_unknown"}]
        result = validate_context(base_context(history=history))
        assert result["history"][0]["sentiment"] == "neutral"


class TestMotivationOptional:
    """Optional Module 4 motivation dict (validated by Module 4 rules)."""

    def test_motivation_none_omitted(self):
        r = validate_context(base_context())
        assert r.get("motivation") is None

    def test_valid_motivation_normalized(self):
        ctx = base_context(
            motivation={
                "current_streak": 10,
                "recent_sentiments": ["good", "neutral"],
                "terrain_last_week": ["road", "trail"],
                "adherence_percent": 88,
                "days_to_race": 45,
            },
        )
        r = validate_context(ctx)
        assert r["motivation"]["adherence_percent"] == 88.0
        assert r["motivation"]["recent_sentiments"][0] == "good"

    def test_invalid_motivation_raises(self):
        with pytest.raises(ValidationError):
            validate_context(
                base_context(
                    motivation={
                        "current_streak": 0,
                        "recent_sentiments": ["good"],
                        "terrain_last_week": ["moon"],
                        "adherence_percent": 80,
                        "days_to_race": 30,
                    },
                )
            )


class TestOptionalQLearningAndSafety:
    def test_hyperparameters_defaults(self):
        r = validate_context(base_context())
        assert r["alpha"] == pytest.approx(0.3)
        assert r["gamma"] == pytest.approx(0.9)
        assert r["epsilon"] == pytest.approx(0.2)

    def test_hyperparameters_custom(self):
        r = validate_context(base_context(alpha=0.2, gamma=0.95, epsilon=0.1))
        assert r["alpha"] == pytest.approx(0.2)
        assert r["gamma"] == pytest.approx(0.95)
        assert r["epsilon"] == pytest.approx(0.1)

    def test_validate_fn_must_be_callable(self):
        with pytest.raises(ValidationError, match="validate_fn"):
            validate_context(base_context(validate_fn="not a function"))

    def test_runner_profile_must_be_dict(self):
        with pytest.raises(ValidationError, match="runner_profile"):
            validate_context(base_context(runner_profile="x"))
