"""
state.py — RunnerState dataclass and builder from Module 1 + Module 3 outputs.

This is the data layer for Module 4. It defines what we know about the runner
at a given moment, and how to construct that from existing module outputs.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RunnerState:
    """
    Snapshot of the runner's current physical and motivational state.

    All fields are normalized to [0.0, 1.0] ranges except avg_sentiment
    which is [-1.0, 1.0] to match Module 3's sentiment output.
    """
    fatigue_level: float        # 0.0 (fresh) → 1.0 (exhausted)
    adherence_rate: float       # 0.0 → 1.0, how often runner follows plan
    avg_sentiment: float        # -1.0 (negative) → 1.0 (positive), from M3
    avg_effort: float           # 0.0 → 1.0, recent perceived effort from M3
    is_safe_to_push: bool       # True if M1 validate_workout returned safe
    days_since_rest: int        # consecutive training days without a rest day

    def __post_init__(self):
        self.fatigue_level  = max(0.0, min(1.0, self.fatigue_level))
        self.adherence_rate = max(0.0, min(1.0, self.adherence_rate))
        self.avg_sentiment  = max(-1.0, min(1.0, self.avg_sentiment))
        self.avg_effort     = max(0.0, min(1.0, self.avg_effort))
        self.days_since_rest = max(0, self.days_since_rest)

    def is_overtraining_risk(self) -> bool:
        """True when multiple overtraining signals are present."""
        return (
            self.fatigue_level > 0.7
            and self.avg_effort > 0.8
            and self.days_since_rest >= 5
        )

    def to_dict(self) -> dict:
        return {
            "fatigue_level":    round(self.fatigue_level, 3),
            "adherence_rate":   round(self.adherence_rate, 3),
            "avg_sentiment":    round(self.avg_sentiment, 3),
            "avg_effort":       round(self.avg_effort, 3),
            "is_safe_to_push":  self.is_safe_to_push,
            "days_since_rest":  self.days_since_rest,
        }


def build_runner_state(
    runner_profile: dict,
    run_history: list,
    safety_result: dict,
) -> RunnerState:
    """
    Build a RunnerState by combining outputs from Module 1 and Module 3.

    Args:
        runner_profile:  the shared profile dict used across the system
        run_history:     list of parsed run dicts from M3 get_run_history()
        safety_result:   dict from M1 validate_workout()

    Returns:
        RunnerState ready for payoff computation
    """
    # --- Fatigue: base from days trained this week ---
    days_trained = runner_profile.get("days_trained_this_week", 3)
    fatigue_level = min(1.0, days_trained / 7.0)

    # Adjust upward based on recent effort from M3 logs
    recent_runs = run_history[-5:] if run_history else []
    efforts = [r.get("effort", 0.5) for r in recent_runs if r.get("effort") is not None]
    avg_effort = sum(efforts) / len(efforts) if efforts else 0.5
    fatigue_level = min(1.0, fatigue_level + avg_effort * 0.2)

    # --- Sentiment: average of recent M3 logs ---
    sentiments = [r.get("sentiment", 0.0) for r in recent_runs]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

    # --- Adherence: from profile (M3 can update this over time) ---
    adherence_rate = runner_profile.get("adherence_rate", 0.7)

    # --- Safety: directly from M1 output ---
    is_safe_to_push = safety_result.get("safe", False)

    # --- Days since rest ---
    days_since_rest = runner_profile.get("days_trained_this_week", days_trained)

    return RunnerState(
        fatigue_level=fatigue_level,
        adherence_rate=adherence_rate,
        avg_sentiment=avg_sentiment,
        avg_effort=avg_effort,
        is_safe_to_push=is_safe_to_push,
        days_since_rest=days_since_rest,
    )