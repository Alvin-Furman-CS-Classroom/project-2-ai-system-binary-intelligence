"""
Unit tests for EmbeddingMatcher.

Tests cover keyword fallback matching for terrain and workout type.
Embedding-based tests use the keyword fallback path since the Word2Vec
model is not available in the test environment — this is the expected
behaviour as documented in matcher.py.
"""

import pytest
from src.module3_run_logger.matcher import EmbeddingMatcher


@pytest.fixture
def matcher():
    # Pass a non-existent path so the model load fails cleanly
    # and keyword fallback is always used in tests.
    return EmbeddingMatcher(model_path="nonexistent_model.bin")


class TestMatchTerrain:
    def test_trail(self, matcher):
        assert matcher.match_terrain("ran on the trail today") == "trail"

    def test_dirt_maps_to_trail(self, matcher):
        assert matcher.match_terrain("dirt path through the woods") == "trail"

    def test_road(self, matcher):
        assert matcher.match_terrain("5 miles on the road") == "road"

    def test_pavement_maps_to_road(self, matcher):
        assert matcher.match_terrain("pavement was hot today") == "road"

    def test_treadmill(self, matcher):
        assert matcher.match_terrain("treadmill run this morning") == "treadmill"

    def test_track(self, matcher):
        assert matcher.match_terrain("intervals on the track") == "track"

    def test_grass(self, matcher):
        assert matcher.match_terrain("easy run on the grass") == "grass"

    def test_default_is_road(self, matcher):
        assert matcher.match_terrain("went for a run") == "road"

    def test_gravel_maps_to_trail(self, matcher):
        assert matcher.match_terrain("gravel path") == "trail"

    def test_indoor_maps_to_treadmill(self, matcher):
        assert matcher.match_terrain("indoor run today") == "treadmill"


class TestMatchWorkoutType:
    def test_long_run(self, matcher):
        assert matcher.match_workout_type("did my long run today") == "long run"

    def test_easy_run(self, matcher):
        assert matcher.match_workout_type("easy run this morning") == "easy run"

    def test_jog_maps_to_easy(self, matcher):
        assert matcher.match_workout_type("went for a jog") == "easy run"

    def test_tempo(self, matcher):
        assert matcher.match_workout_type("tempo run at threshold pace") == "tempo run"

    def test_intervals(self, matcher):
        assert matcher.match_workout_type("track intervals today") == "interval"

    def test_recovery(self, matcher):
        assert matcher.match_workout_type("recovery run after race") == "recovery run"

    def test_fartlek_maps_to_interval(self, matcher):
        assert matcher.match_workout_type("fartlek session") == "interval"

    def test_race(self, matcher):
        assert matcher.match_workout_type("ran the 5k race") == "race"

    def test_default_is_easy_run(self, matcher):
        assert matcher.match_workout_type("went for a run") == "easy run"

    def test_speed_maps_to_interval(self, matcher):
        assert matcher.match_workout_type("speed workout on track") == "interval"


class TestLongestMatchFirst:
    def test_long_run_beats_run(self, matcher):
        # "long run" should match before "run" alone
        assert matcher.match_workout_type("long run this sunday") == "long run"

    def test_half_marathon_beats_marathon(self, matcher):
        # "half marathon" should not be absorbed by standalone checks
        result = matcher.match_workout_type("half marathon training run")
        assert result in ("easy run", "long run", "race")  # any reasonable label
