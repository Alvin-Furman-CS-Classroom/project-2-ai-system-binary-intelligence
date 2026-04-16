"""
Module 5 - Adaptive Progression System
Q-learning engine.

Implements the epsilon-greedy Q-learning update rule from the course slides:
    Q(s, a) <- Q(s, a) + alpha * [r + gamma * max_a' Q(s', a') - Q(s, a)]

The Q-table is a dict-of-dicts keyed by (state, action) pairs so it grows
only as the runner explores states, avoiding a full pre-allocation.

Action space is **volume × intensity** only (9 actions); terrain is chosen
by rules in ``features.select_terrain_for_session``.

**Schema version 3:** MDP state gained a 5th component (adherence tier). Older
saved Q-tables (v1 or v2) are cleared on load so indices stay consistent with
``ALL_ACTIONS``.
"""

import json
import random
from pathlib import Path

from .mdp import ALL_ACTIONS, COLD_START_ACTION

# ---------------------------------------------------------------------------
# Default hyperparameters (override via context: alpha, gamma, epsilon)
# ---------------------------------------------------------------------------
DEFAULT_ALPHA   = 0.3
DEFAULT_GAMMA   = 0.9
DEFAULT_EPSILON = 0.2
MIN_EPSILON     = 0.05
EPSILON_DECAY   = 0.98

SCHEMA_VERSION = 3


class QLearningEngine:
    """
    Tabular Q-learning agent for training progression.

    Each Long Run runner has their own QLearningEngine instance (persisted
    to a JSON file so learning accumulates across app sessions).
    """

    def __init__(
        self,
        alpha=DEFAULT_ALPHA,
        gamma=DEFAULT_GAMMA,
        epsilon=DEFAULT_EPSILON,
        q_table=None,
        episode_count=0,
    ):
        self.alpha   = float(alpha)
        self.gamma   = float(gamma)
        self.epsilon = float(epsilon)
        self.episode_count = episode_count
        self._q: dict = q_table if q_table is not None else {}

    @staticmethod
    def _state_key(state):
        """Convert a state tuple (enums) to a JSON-safe string key."""
        return str(tuple(s.value if hasattr(s, "value") else s for s in state))

    @staticmethod
    def _action_index(action):
        """Return the integer index of an action in ALL_ACTIONS."""
        return ALL_ACTIONS.index(action)

    def _q_value(self, state, action):
        sk = self._state_key(state)
        ai = self._action_index(action)
        return self._q.get(sk, {}).get(str(ai), 0.0)

    def _set_q_value(self, state, action, value):
        sk = self._state_key(state)
        ai = str(self._action_index(action))
        if sk not in self._q:
            self._q[sk] = {}
        self._q[sk][ai] = value

    def _all_q_zero(self, state):
        return all(abs(self._q_value(state, a)) < 1e-12 for a in ALL_ACTIONS)

    def _max_q(self, state):
        """max_a Q(state, a) — used in Bellman target."""
        return max(self._q_value(state, a) for a in ALL_ACTIONS)

    def _best_action(self, state):
        """argmax_a Q(state, a) with deterministic tie-break: prefer earlier in ALL_ACTIONS."""
        best_a = ALL_ACTIONS[0]
        best_q = self._q_value(state, best_a)
        for a in ALL_ACTIONS[1:]:
            q = self._q_value(state, a)
            if q > best_q:
                best_q, best_a = q, a
        return best_a

    def update(self, state, action, reward, next_state):
        """Apply one Q-learning update step."""
        current_q = self._q_value(state, action)
        target = reward + self.gamma * self._max_q(next_state)
        error = target - current_q
        new_q = current_q + self.alpha * error
        self._set_q_value(state, action, new_q)
        return new_q

    def select_action(self, state, force_exploit=False):
        """
        Epsilon-greedy.  Cold start: if exploiting and all Q are ~0, return
        COLD_START_ACTION (HOLD, HOLD) instead of an arbitrary argmax tie.
        """
        if not force_exploit and random.random() < self.epsilon:
            return random.choice(ALL_ACTIONS)
        if force_exploit and self._all_q_zero(state):
            return COLD_START_ACTION
        return self._best_action(state)

    def end_episode(self):
        self.episode_count += 1
        self.epsilon = max(MIN_EPSILON, self.epsilon * EPSILON_DECAY)

    def confidence(self, state):
        sk = self._state_key(state)
        if sk not in self._q:
            return 0.0
        q_entries = self._q[sk]
        if not q_entries:
            return 0.0

        coverage = len(q_entries) / len(ALL_ACTIONS)
        values = [abs(v) for v in q_entries.values()]
        magnitude = min(1.0, max(values) / 10.0)

        return round(min(1.0, (coverage + magnitude) / 2.0), 4)

    def to_dict(self):
        return {
            "schema_version": SCHEMA_VERSION,
            "alpha":         self.alpha,
            "gamma":         self.gamma,
            "epsilon":       self.epsilon,
            "episode_count": self.episode_count,
            "q_table":       self._q,
        }

    @classmethod
    def from_dict(cls, data):
        schema = data.get("schema_version", 1)
        q_table = data.get("q_table", {})
        # v1: 36 actions; v2: 4-tuple state keys; v3: 5-tuple state — all incompatible with current engine
        if schema < SCHEMA_VERSION:
            q_table = {}
        return cls(
            alpha         = data.get("alpha", DEFAULT_ALPHA),
            gamma         = data.get("gamma", DEFAULT_GAMMA),
            epsilon       = data.get("epsilon", DEFAULT_EPSILON),
            q_table       = q_table,
            episode_count = data.get("episode_count", 0),
        )

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path):
        with open(path) as f:
            return cls.from_dict(json.load(f))

    @classmethod
    def load_or_create(cls, path):
        p = Path(path)
        if p.exists() and p.stat().st_size > 0:
            return cls.load(path)
        return cls()