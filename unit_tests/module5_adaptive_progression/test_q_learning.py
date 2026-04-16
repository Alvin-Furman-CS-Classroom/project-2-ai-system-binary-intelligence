"""Unit tests for q_learning.py — Q-table operations, update rule, epsilon decay."""

import json
import math
import os
import tempfile

import pytest
from src.module5_adaptive_progression.mdp import (
    ALL_ACTIONS,
    FitnessTier,
    FatigueLevel,
    TerrainStreak,
    VolumeAdjustment,
    IntensityAdjustment,
    discretize_state,
)
from src.module5_adaptive_progression.q_learning import (
    QLearningEngine,
    DEFAULT_ALPHA,
    DEFAULT_GAMMA,
    DEFAULT_EPSILON,
    MIN_EPSILON,
    EPSILON_DECAY,
    SCHEMA_VERSION,
)
from src.module5_adaptive_progression.mdp import COLD_START_ACTION


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fresh_state():
    return discretize_state(25.0, 0.2, ["road", "trail"])

def sample_action():
    return ALL_ACTIONS[0]


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestInitialization:
    def test_default_hyperparameters(self):
        engine = QLearningEngine()
        assert engine.alpha   == DEFAULT_ALPHA
        assert engine.gamma   == DEFAULT_GAMMA
        assert engine.epsilon == DEFAULT_EPSILON

    def test_custom_hyperparameters(self):
        engine = QLearningEngine(alpha=0.1, gamma=0.8, epsilon=0.5)
        assert engine.alpha   == 0.1
        assert engine.gamma   == 0.8
        assert engine.epsilon == 0.5

    def test_empty_q_table_on_init(self):
        engine = QLearningEngine()
        assert engine._q == {}

    def test_episode_count_starts_at_zero(self):
        engine = QLearningEngine()
        assert engine.episode_count == 0


# ---------------------------------------------------------------------------
# Q-value access
# ---------------------------------------------------------------------------

class TestQValues:
    def test_unseen_state_returns_zero(self):
        engine = QLearningEngine()
        state  = fresh_state()
        action = sample_action()
        assert engine._q_value(state, action) == 0.0

    def test_set_and_get_q_value(self):
        engine = QLearningEngine()
        state  = fresh_state()
        action = sample_action()
        engine._set_q_value(state, action, 3.14)
        assert engine._q_value(state, action) == pytest.approx(3.14)

    def test_max_q_all_zeros(self):
        engine = QLearningEngine()
        state  = fresh_state()
        assert engine._max_q(state) == 0.0

    def test_max_q_after_updates(self):
        engine = QLearningEngine()
        state  = fresh_state()
        for i, action in enumerate(ALL_ACTIONS[:5]):
            engine._set_q_value(state, action, float(i))
        assert engine._max_q(state) == pytest.approx(4.0)

    def test_best_action_returns_highest_q(self):
        engine = QLearningEngine()
        state  = fresh_state()
        target_action = ALL_ACTIONS[7]
        engine._set_q_value(state, target_action, 99.0)
        assert engine._best_action(state) == target_action


# ---------------------------------------------------------------------------
# Q-learning update rule  (slide 42)
# ---------------------------------------------------------------------------

class TestUpdateRule:
    def test_update_from_zero(self):
        """Q(s,a) += alpha * [r + gamma*max_Q(s') - Q(s,a)]"""
        engine = QLearningEngine(alpha=0.5, gamma=0.9)
        state  = fresh_state()
        action = sample_action()
        next_state = discretize_state(30.0, 0.1, ["road"])

        new_q = engine.update(state, action, reward=10.0, next_state=next_state)
        # current_q=0, target=10+0.9*0=10, error=10, update=0+0.5*10=5
        assert new_q == pytest.approx(5.0)

    def test_update_moves_toward_target(self):
        engine = QLearningEngine(alpha=0.5, gamma=0.9)
        state  = fresh_state()
        action = sample_action()
        # Seed a high next-state value
        next_state = discretize_state(30.0, 0.1, ["road"])
        engine._set_q_value(next_state, ALL_ACTIONS[1], 20.0)

        new_q = engine.update(state, action, reward=5.0, next_state=next_state)
        target = 5.0 + 0.9 * 20.0  # 23
        expected = 0.0 + 0.5 * (target - 0.0)  # 11.5
        assert new_q == pytest.approx(expected)

    def test_negative_reward_decreases_q(self):
        engine = QLearningEngine(alpha=0.5, gamma=0.9)
        state  = fresh_state()
        action = sample_action()
        next_state = discretize_state(20.0, 0.8, ["road", "road"])
        new_q = engine.update(state, action, reward=-8.0, next_state=next_state)
        assert new_q < 0

    def test_update_stored_in_table(self):
        engine = QLearningEngine(alpha=0.5, gamma=0.0)
        state  = fresh_state()
        action = sample_action()
        next_state = fresh_state()
        engine.update(state, action, reward=4.0, next_state=next_state)
        # gamma=0: new_q = 0 + 0.5*(4 - 0) = 2
        assert engine._q_value(state, action) == pytest.approx(2.0)

    def test_successive_updates_converge(self):
        """After many updates with consistent reward the value should stabilize."""
        engine = QLearningEngine(alpha=0.1, gamma=0.0)
        state  = fresh_state()
        action = sample_action()
        next_state = fresh_state()
        for _ in range(200):
            engine.update(state, action, reward=5.0, next_state=next_state)
        # Should converge near 5
        assert engine._q_value(state, action) == pytest.approx(5.0, abs=0.1)


# ---------------------------------------------------------------------------
# Action selection
# ---------------------------------------------------------------------------

class TestActionSelection:
    def test_exploit_returns_best_action(self):
        engine = QLearningEngine()
        state  = fresh_state()
        best   = ALL_ACTIONS[3]
        engine._set_q_value(state, best, 50.0)
        assert engine.select_action(state, force_exploit=True) == best

    def test_exploit_flag_ignores_epsilon(self):
        engine = QLearningEngine(epsilon=1.0)  # would always explore
        state  = fresh_state()
        best   = ALL_ACTIONS[2]
        engine._set_q_value(state, best, 100.0)
        # force_exploit overrides epsilon
        assert engine.select_action(state, force_exploit=True) == best

    def test_explore_returns_valid_action(self):
        engine = QLearningEngine(epsilon=1.0)
        state  = fresh_state()
        action = engine.select_action(state)
        assert action in ALL_ACTIONS

    def test_epsilon_zero_always_exploits(self):
        engine = QLearningEngine(epsilon=0.0)
        state  = fresh_state()
        best   = ALL_ACTIONS[5]
        engine._set_q_value(state, best, 30.0)
        results = {engine.select_action(state) for _ in range(20)}
        assert results == {best}

    def test_exploit_cold_start_prefers_hold_hold(self):
        engine = QLearningEngine()
        state  = fresh_state()
        assert engine.select_action(state, force_exploit=True) == COLD_START_ACTION


# ---------------------------------------------------------------------------
# Epsilon decay
# ---------------------------------------------------------------------------

class TestEpsilonDecay:
    def test_epsilon_decreases_after_episode(self):
        engine = QLearningEngine(epsilon=0.5)
        engine.end_episode()
        assert engine.epsilon < 0.5

    def test_epsilon_not_below_minimum(self):
        engine = QLearningEngine(epsilon=MIN_EPSILON)
        for _ in range(100):
            engine.end_episode()
        assert engine.epsilon >= MIN_EPSILON

    def test_episode_count_increments(self):
        engine = QLearningEngine()
        for i in range(5):
            engine.end_episode()
            assert engine.episode_count == i + 1

    def test_decay_formula(self):
        epsilon_start = 0.4
        engine = QLearningEngine(epsilon=epsilon_start)
        engine.end_episode()
        expected = max(MIN_EPSILON, epsilon_start * EPSILON_DECAY)
        assert engine.epsilon == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

class TestConfidence:
    def test_zero_confidence_on_unseen_state(self):
        engine = QLearningEngine()
        state  = fresh_state()
        assert engine.confidence(state) == 0.0

    def test_higher_confidence_with_more_signal(self):
        engine = QLearningEngine()
        state  = fresh_state()
        engine._set_q_value(state, ALL_ACTIONS[0], -5.0)
        engine._set_q_value(state, ALL_ACTIONS[1],  5.0)
        assert engine.confidence(state) > 0.0

    def test_confidence_bounded_at_one(self):
        engine = QLearningEngine()
        state  = fresh_state()
        engine._set_q_value(state, ALL_ACTIONS[0], -100.0)
        engine._set_q_value(state, ALL_ACTIONS[1],  100.0)
        assert engine.confidence(state) <= 1.0


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_to_dict_contains_required_keys(self):
        engine = QLearningEngine()
        d = engine.to_dict()
        for key in ("alpha", "gamma", "epsilon", "episode_count", "q_table", "schema_version"):
            assert key in d
        assert d["schema_version"] == SCHEMA_VERSION

    def test_v1_payload_resets_q_table(self):
        """Old 36-action tables are incompatible; load should start fresh."""
        legacy = {
            "schema_version": 1,
            "alpha": 0.3,
            "gamma": 0.9,
            "epsilon": 0.2,
            "episode_count": 0,
            "q_table": {"('low', 'fresh', 'varied')": {"0": 1.0}},
        }
        eng = QLearningEngine.from_dict(legacy)
        assert eng._q == {}

    def test_v2_payload_resets_q_table(self):
        """v2 used 4-tuple state keys; v3 adds adherence — stale JSON must not reuse old Q entries."""
        legacy_v2 = {
            "schema_version": 2,
            "alpha": 0.3,
            "gamma": 0.9,
            "epsilon": 0.2,
            "episode_count": 99,
            "q_table": {
                "('low', 'fresh', 'varied', 'easy')": {"0": 2.5, "1": -1.0},
            },
        }
        eng = QLearningEngine.from_dict(legacy_v2)
        assert eng._q == {}

    def test_from_dict_restores_hyperparameters(self):
        original = QLearningEngine(alpha=0.15, gamma=0.85, epsilon=0.12)
        restored = QLearningEngine.from_dict(original.to_dict())
        assert restored.alpha   == pytest.approx(0.15)
        assert restored.gamma   == pytest.approx(0.85)
        assert restored.epsilon == pytest.approx(0.12)

    def test_from_dict_restores_q_values(self):
        engine = QLearningEngine()
        state  = fresh_state()
        engine._set_q_value(state, ALL_ACTIONS[0], 7.77)
        restored = QLearningEngine.from_dict(engine.to_dict())
        assert restored._q_value(state, ALL_ACTIONS[0]) == pytest.approx(7.77)

    def test_save_and_load(self):
        engine = QLearningEngine(alpha=0.2)
        state  = fresh_state()
        engine._set_q_value(state, ALL_ACTIONS[2], 3.33)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            engine.save(path)
            loaded = QLearningEngine.load(path)
            assert loaded.alpha == pytest.approx(0.2)
            assert loaded._q_value(state, ALL_ACTIONS[2]) == pytest.approx(3.33)
        finally:
            os.unlink(path)

    def test_load_or_create_returns_new_when_no_file(self):
        engine = QLearningEngine.load_or_create("/tmp/nonexistent_qtable_12345.json")
        assert engine.episode_count == 0

    def test_load_or_create_loads_existing_file(self):
        original = QLearningEngine(epsilon=0.07)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            original.save(path)
            loaded = QLearningEngine.load_or_create(path)
            assert loaded.epsilon == pytest.approx(0.07)
        finally:
            os.unlink(path)
