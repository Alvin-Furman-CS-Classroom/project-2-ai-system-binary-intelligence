"""Unit tests for mdp.py — state discretization, action enumeration, reward function."""

import pytest
from src.module5_adaptive_progression.mdp import (
    discretize_state,
    FitnessTier,
    FatigueLevel,
    TerrainStreak,
    WorkoutCategory,
    AdherenceTier,
    ALL_ACTIONS,
    compute_reward,
    REWARD_INJURY_RISK,
    REWARD_FATIGUE_SPIKE,
    REWARD_VARIETY_BONUS,
    REWARD_STEP_PENALTY,
    REWARD_COMPLETED_POSITIVE,
    REWARD_COMPLETED_NEUTRAL,
    REWARD_COMPLETED_NEGATIVE,
    REWARD_HIGH_ADHERENCE,
    REWARD_LOW_ADHERENCE,
    REWARD_MIN_APPROX,
    REWARD_MAX_APPROX,
    VolumeAdjustment,
    IntensityAdjustment,
)


# ---------------------------------------------------------------------------
# FitnessTier discretization
# ---------------------------------------------------------------------------

class TestFitnessTier:
    def test_low_tier_boundary(self):
        state = discretize_state(0.0, 0.0, [])
        assert state[0] == FitnessTier.LOW

    def test_low_tier_just_below_threshold(self):
        state = discretize_state(19.9, 0.0, [])
        assert state[0] == FitnessTier.LOW

    def test_medium_tier_at_boundary(self):
        state = discretize_state(20.0, 0.0, [])
        assert state[0] == FitnessTier.MEDIUM

    def test_medium_tier_middle(self):
        state = discretize_state(30.0, 0.0, [])
        assert state[0] == FitnessTier.MEDIUM

    def test_medium_tier_upper_boundary(self):
        state = discretize_state(40.0, 0.0, [])
        assert state[0] == FitnessTier.MEDIUM

    def test_high_tier(self):
        state = discretize_state(41.0, 0.0, [])
        assert state[0] == FitnessTier.HIGH

    def test_high_tier_large_value(self):
        state = discretize_state(100.0, 0.0, [])
        assert state[0] == FitnessTier.HIGH


# ---------------------------------------------------------------------------
# FatigueLevel discretization
# ---------------------------------------------------------------------------

class TestFatigueLevel:
    def test_fresh_at_zero(self):
        state = discretize_state(0.0, 0.0, [])
        assert state[1] == FatigueLevel.FRESH

    def test_fresh_at_upper_boundary(self):
        state = discretize_state(0.0, 0.33, [])
        assert state[1] == FatigueLevel.FRESH

    def test_moderate_just_above_fresh(self):
        state = discretize_state(0.0, 0.34, [])
        assert state[1] == FatigueLevel.MODERATE

    def test_moderate_middle(self):
        state = discretize_state(0.0, 0.5, [])
        assert state[1] == FatigueLevel.MODERATE

    def test_moderate_upper_boundary(self):
        state = discretize_state(0.0, 0.66, [])
        assert state[1] == FatigueLevel.MODERATE

    def test_fatigued(self):
        state = discretize_state(0.0, 0.67, [])
        assert state[1] == FatigueLevel.FATIGUED

    def test_fatigued_at_max(self):
        state = discretize_state(0.0, 1.0, [])
        assert state[1] == FatigueLevel.FATIGUED


# ---------------------------------------------------------------------------
# TerrainStreak discretization
# ---------------------------------------------------------------------------

class TestTerrainStreak:
    def test_varied_on_empty_history(self):
        state = discretize_state(0.0, 0.0, [])
        assert state[2] == TerrainStreak.VARIED

    def test_varied_on_single_entry(self):
        state = discretize_state(0.0, 0.0, ["road"])
        assert state[2] == TerrainStreak.VARIED

    def test_same_on_two_identical(self):
        state = discretize_state(0.0, 0.0, ["road", "road"])
        assert state[2] == TerrainStreak.SAME

    def test_varied_on_two_different(self):
        state = discretize_state(0.0, 0.0, ["road", "trail"])
        assert state[2] == TerrainStreak.VARIED

    def test_same_at_end_of_longer_sequence(self):
        state = discretize_state(0.0, 0.0, ["trail", "road", "road"])
        assert state[2] == TerrainStreak.SAME

    def test_varied_at_end_of_longer_sequence(self):
        state = discretize_state(0.0, 0.0, ["road", "road", "trail"])
        assert state[2] == TerrainStreak.VARIED


# ---------------------------------------------------------------------------
# Action space
# ---------------------------------------------------------------------------

class TestActionSpace:
    def test_action_count(self):
        # 3 volume * 3 intensity (terrain chosen by rules, not Q)
        assert len(ALL_ACTIONS) == 9

    def test_all_actions_are_tuples(self):
        for action in ALL_ACTIONS:
            assert isinstance(action, tuple)
            assert len(action) == 2

    def test_all_volume_adjustments_present(self):
        vols = {a[0] for a in ALL_ACTIONS}
        assert vols == set(VolumeAdjustment)

    def test_all_intensity_adjustments_present(self):
        intensities = {a[1] for a in ALL_ACTIONS}
        assert intensities == set(IntensityAdjustment)

    def test_no_duplicate_actions(self):
        assert len(ALL_ACTIONS) == len(set(ALL_ACTIONS))


class TestWorkoutCategoryInState:
    def test_default_workout_type_maps_to_easy(self):
        state = discretize_state(10.0, 0.2, ["road"])
        assert state[3] == WorkoutCategory.EASY

    def test_tempo_maps_to_quality(self):
        state = discretize_state(10.0, 0.2, ["road"], workout_type="tempo run")
        assert state[3] == WorkoutCategory.QUALITY

    def test_long_run_category(self):
        state = discretize_state(10.0, 0.2, ["road"], workout_type="long run")
        assert state[3] == WorkoutCategory.LONG


# ---------------------------------------------------------------------------
# AdherenceTier (5th state component; default adherence_percent=100 → HIGH)
# ---------------------------------------------------------------------------

class TestAdherenceTierInState:
    def test_default_adherence_is_high_tier(self):
        state = discretize_state(10.0, 0.2, ["road"])
        assert len(state) == 5
        assert state[4] == AdherenceTier.HIGH

    def test_high_tier_at_85_boundary(self):
        state = discretize_state(10.0, 0.2, ["road"], adherence_percent=85.0)
        assert state[4] == AdherenceTier.HIGH

    def test_medium_tier(self):
        state = discretize_state(10.0, 0.2, ["road"], adherence_percent=70.0)
        assert state[4] == AdherenceTier.MEDIUM

    def test_medium_tier_at_60_boundary(self):
        state = discretize_state(10.0, 0.2, ["road"], adherence_percent=60.0)
        assert state[4] == AdherenceTier.MEDIUM

    def test_low_tier_below_60(self):
        state = discretize_state(10.0, 0.2, ["road"], adherence_percent=59.9)
        assert state[4] == AdherenceTier.LOW


# ---------------------------------------------------------------------------
# Reward function
# ---------------------------------------------------------------------------

class TestRewardFunction:
    def _reward(self, sentiment="neutral", fatigue_before=0.2, fatigue_after=0.3,
                terrain_before="road", terrain_after="road"):
        return compute_reward(sentiment, fatigue_before, fatigue_after,
                              terrain_before, terrain_after)

    def test_positive_sentiment_gives_high_reward(self):
        r = self._reward(sentiment="positive")
        assert r > 0

    def test_negative_sentiment_gives_low_reward(self):
        r_neg = self._reward(sentiment="negative")
        r_pos = self._reward(sentiment="positive")
        assert r_neg < r_pos

    def test_neutral_sentiment_between_pos_and_neg(self):
        r_pos = self._reward(sentiment="positive")
        r_neu = self._reward(sentiment="neutral")
        r_neg = self._reward(sentiment="negative")
        assert r_neg < r_neu < r_pos

    def test_injury_risk_penalty_applied(self):
        r_safe    = self._reward(fatigue_after=0.4)
        r_risky   = self._reward(fatigue_after=0.90)
        assert r_risky < r_safe
        # Should include the injury risk penalty
        assert r_risky <= r_safe + REWARD_INJURY_RISK

    def test_fatigue_spike_penalty_applied(self):
        r_normal = self._reward(fatigue_before=0.2, fatigue_after=0.3)
        r_spike  = self._reward(fatigue_before=0.2, fatigue_after=0.6)
        assert r_spike < r_normal

    def test_variety_bonus_applied(self):
        r_same    = self._reward(terrain_before="road", terrain_after="road")
        r_variety = self._reward(terrain_before="road", terrain_after="trail")
        assert r_variety == r_same + REWARD_VARIETY_BONUS

    def test_step_penalty_always_present(self):
        r = self._reward(sentiment="positive", fatigue_before=0.0,
                         fatigue_after=0.0, terrain_before="road", terrain_after="trail")
        # positive + variety bonus + step penalty
        expected = (REWARD_STEP_PENALTY + REWARD_COMPLETED_POSITIVE + REWARD_VARIETY_BONUS)
        assert abs(r - expected) < 1e-6

    def test_injury_and_spike_do_not_double_penalize(self):
        # fatigue_after > 0.85 triggers injury risk, not fatigue spike
        r = self._reward(fatigue_before=0.2, fatigue_after=0.90)
        # Should have injury risk penalty, NOT additional spike penalty
        # because fatigue_after > 0.85 takes precedence
        assert r == pytest.approx(
            REWARD_STEP_PENALTY + REWARD_COMPLETED_NEUTRAL + REWARD_INJURY_RISK,
            abs=1e-4,
        )

    def test_case_insensitive_sentiment(self):
        r_lower = compute_reward("positive", 0.2, 0.3, "road", "road")
        r_upper = compute_reward("POSITIVE", 0.2, 0.3, "road", "road")
        assert r_lower == r_upper

    def test_none_terrain_before_no_bonus(self):
        # When terrain_before is None we cannot award variety bonus
        r = compute_reward("neutral", 0.2, 0.3, None, "road")
        assert r == pytest.approx(REWARD_STEP_PENALTY + REWARD_COMPLETED_NEUTRAL, abs=1e-6)

    def test_high_adherence_adds_bonus(self):
        base = compute_reward("neutral", 0.2, 0.3, "road", "road", adherence_percent=None)
        high = compute_reward("neutral", 0.2, 0.3, "road", "road", adherence_percent=90.0)
        assert high == pytest.approx(base + REWARD_HIGH_ADHERENCE, abs=1e-6)

    def test_low_adherence_adds_penalty(self):
        base = compute_reward("neutral", 0.2, 0.3, "road", "road", adherence_percent=None)
        low = compute_reward("neutral", 0.2, 0.3, "road", "road", adherence_percent=50.0)
        assert low == pytest.approx(base + REWARD_LOW_ADHERENCE, abs=1e-6)

    def test_mid_adherence_no_primary_shift(self):
        base = compute_reward("neutral", 0.2, 0.3, "road", "road", adherence_percent=None)
        mid = compute_reward("neutral", 0.2, 0.3, "road", "road", adherence_percent=70.0)
        assert mid == pytest.approx(base, abs=1e-6)


class TestRewardBounds:
    """Sanity check for reward shaping range (used by integration / debugging)."""

    def test_reward_stays_within_approx_bounds(self):
        motivation = {
            "adherence_percent": 100.0,
            "recent_sentiments": [],
            "days_to_race": 100,
        }
        for sent in ("positive", "neutral", "negative"):
            for fb, fa in [(0.1, 0.2), (0.2, 0.9), (0.2, 0.5)]:
                for tb, ta in [("road", "road"), ("road", "trail"), (None, "trail")]:
                    r = compute_reward(sent, fb, fa, tb, ta, motivation=motivation)
                    assert REWARD_MIN_APPROX <= r <= REWARD_MAX_APPROX
