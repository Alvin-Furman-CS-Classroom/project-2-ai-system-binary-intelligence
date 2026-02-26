"""
Unit tests for TokenExtractor.

Tests cover distance extraction (miles, km, named distances),
pace extraction (MM:SS formats), and edge cases.
"""

import pytest
from src.module3_run_logger.extractor import TokenExtractor


@pytest.fixture
def ex():
    return TokenExtractor()


class TestExtractDistance:
    def test_miles_integer(self, ex):
        assert ex.extract_distance("ran 10 miles today") == 10.0

    def test_miles_decimal(self, ex):
        assert ex.extract_distance("10.5 miles on the road") == 10.5

    def test_miles_abbreviation(self, ex):
        assert ex.extract_distance("5 mi easy run") == 5.0

    def test_km_converts_to_miles(self, ex):
        result = ex.extract_distance("ran 10 km")
        assert abs(result - 6.21) < 0.01

    def test_named_marathon(self, ex):
        assert ex.extract_distance("completed the marathon today") == 26.2

    def test_named_half_marathon(self, ex):
        assert ex.extract_distance("half marathon done") == 13.1

    def test_named_5k(self, ex):
        assert ex.extract_distance("ran a 5k race") == 3.1

    def test_named_10k(self, ex):
        assert ex.extract_distance("10k this morning") == 6.2

    def test_no_distance_returns_none(self, ex):
        assert ex.extract_distance("went for a run today") is None

    def test_distance_in_longer_sentence(self, ex):
        assert ex.extract_distance(
            "did my long run on the trail today, 10 miles at 9:30 pace"
        ) == 10.0

    def test_named_distance_takes_priority_over_numeric(self, ex):
        # "marathon" in text should return 26.2 even with other numbers
        assert ex.extract_distance("10 week marathon plan") == 26.2


class TestExtractPace:
    def test_pace_with_pace_word(self, ex):
        assert ex.extract_pace("ran at 9:30 pace") == pytest.approx(9.5, abs=0.01)

    def test_pace_per_mile(self, ex):
        assert ex.extract_pace("8:00/mile") == pytest.approx(8.0, abs=0.01)

    def test_pace_per_km(self, ex):
        result = ex.extract_pace("5:00/km")
        assert result == pytest.approx(5.0, abs=0.01)

    def test_pace_30_seconds(self, ex):
        assert ex.extract_pace("10:30 pace") == pytest.approx(10.5, abs=0.01)

    def test_pace_45_seconds(self, ex):
        assert ex.extract_pace("7:45 pace") == pytest.approx(7.75, abs=0.01)

    def test_no_pace_returns_none(self, ex):
        assert ex.extract_pace("easy run today") is None

    def test_invalid_seconds_returns_none(self, ex):
        assert ex.extract_pace("9:75 pace") is None

    def test_pace_in_full_sentence(self, ex):
        result = ex.extract_pace(
            "did my long run on the trail today, 10 miles at 9:30 pace"
        )
        assert result == pytest.approx(9.5, abs=0.01)


class TestExtractNotes:
    def test_strips_whitespace(self, ex):
        assert ex.extract_notes("  hello world  ") == "hello world"

    def test_preserves_full_text(self, ex):
        text = "felt pretty tired by mile 8 but the soft surface helped my shins"
        assert ex.extract_notes(text) == text
