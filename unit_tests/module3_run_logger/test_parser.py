"""
Unit tests for RunLogParser.

Tests cover the full parse pipeline, output structure,
the proposal example, and error handling.
"""

import pytest
from src.module3_run_logger.parser import RunLogParser


@pytest.fixture
def parser():
    return RunLogParser(model_path="nonexistent_model.bin")


class TestOutputStructure:
    def test_returns_dict(self, parser):
        result = parser.parse("easy 5 miles on the road")
        assert isinstance(result, dict)

    def test_has_all_required_keys(self, parser):
        result = parser.parse("easy 5 miles on the road")
        for key in ("type", "distance", "pace_minutes", "terrain", "sentiment", "notes"):
            assert key in result

    def test_notes_preserves_original_text(self, parser):
        text = "easy 5 miles on the road"
        result = parser.parse(text)
        assert result["notes"] == text


class TestProposalExample:
    def test_full_example(self, parser):
        text = (
            "did my long run on the trail today, 10 miles at 9:30 pace. "
            "felt pretty tired by mile 8 but the soft surface helped my shins"
        )
        result = parser.parse(text)
        assert result["type"] == "long run"
        assert result["distance"] == 10.0
        assert abs(result["pace_minutes"] - 9.5) < 0.01
        assert result["terrain"] == "trail"
        assert result["sentiment"] in ("hard", "struggled", "moderate")


class TestVariousInputs:
    def test_easy_road_run(self, parser):
        result = parser.parse("easy 5 miles on the road, felt great")
        assert result["type"] == "easy run"
        assert result["distance"] == 5.0
        assert result["terrain"] == "road"
        assert result["sentiment"] == "easy"

    def test_treadmill_run(self, parser):
        result = parser.parse("5 miles on the treadmill, okay run")
        assert result["terrain"] == "treadmill"

    def test_tempo_run(self, parser):
        result = parser.parse("tempo run at threshold, felt strong")
        assert result["type"] == "tempo run"

    def test_interval_session(self, parser):
        result = parser.parse("track intervals today, exhausted after")
        assert result["type"] == "interval"
        assert result["sentiment"] == "struggled"

    def test_no_distance_is_none(self, parser):
        result = parser.parse("easy jog today, felt good")
        assert result["distance"] is None

    def test_no_pace_is_none(self, parser):
        result = parser.parse("ran 5 miles easy")
        assert result["pace_minutes"] is None


class TestErrorHandling:
    def test_empty_string_raises(self, parser):
        with pytest.raises(ValueError):
            parser.parse("")

    def test_whitespace_only_raises(self, parser):
        with pytest.raises(ValueError):
            parser.parse("   ")

    def test_non_string_raises(self, parser):
        with pytest.raises(ValueError):
            parser.parse(None)
