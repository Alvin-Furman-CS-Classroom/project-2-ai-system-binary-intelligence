"""
Module 4: Motivation Strategy Selector using a normal-form game-theoretic model.

Public API:
    select_motivation_strategy          - Main entry: choose a coaching strategy.
    select_motivation_strategy_detailed - Same with per-strategy scores.

Inputs (context dict):
    current_streak: int
    recent_sentiments: list[str]
    terrain_last_week: list[str]
    adherence_percent: float | int
    days_to_race: int

Outputs:
    strategy: str           # coach's best response BR_coach to the modeled runner state
    message_tone: str
    reasoning: str          # explanation referencing payoffs and trade-offs
"""

from .selector import (
    select_motivation_strategy,
    select_motivation_strategy_detailed,
)

__all__ = [
    "select_motivation_strategy",
    "select_motivation_strategy_detailed",
]

