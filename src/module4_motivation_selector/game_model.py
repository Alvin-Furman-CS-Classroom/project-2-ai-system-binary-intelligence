from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .input_validation import MotivationContext


COACH_STRATEGIES = ("push_harder", "maintain", "encourage_rest", "encourage_variety")

RUNNER_STATES = ("engaged", "mixed", "default", "bored", "burnout_risk")


@dataclass
class StrategyScores:
    scores: Dict[str, float]

    def best_strategy(self) -> str:
        """Return the coach's best response given runner behavior.

        In course notation, this is BR_coach(s_runner) = argmax_a u_coach(a, s_runner),
        where u_coach is the coach's payoff for choosing action a against the
        modeled runner state s_runner. Ties are broken deterministically by the
        fixed order in COACH_STRATEGIES.
        """
        best = COACH_STRATEGIES[0]
        best_score = self.scores.get(best, float("-inf"))
        for s in COACH_STRATEGIES[1:]:
            score = self.scores.get(s, float("-inf"))
            if score > best_score:
                best, best_score = s, score
        return best


def infer_runner_state(context: MotivationContext) -> str:
    """Infer a coarse runner state from context."""
    sentiments = context.recent_sentiments
    struggled_count = sum(1 for s in sentiments if s == "struggled")
    good_count = sum(1 for s in sentiments if s == "good")

    terrain: List[str] = context.terrain_last_week
    unique_terrain = set(terrain)
    monotonous_terrain = len(unique_terrain) <= 1 and len(terrain) >= 3

    low_adherence = context.adherence_percent < 70.0
    high_adherence = context.adherence_percent >= 90.0

    # Overreaching / burnout risk: multiple struggled runs plus either
    # low adherence (falling off plan) OR very high adherence
    # (continuing to push despite struggles).
    if struggled_count >= 2 and (low_adherence or high_adherence):
        return "burnout_risk"
    if monotonous_terrain and not low_adherence:
        return "bored"
    if good_count >= 2 and high_adherence:
        return "engaged"

    if good_count >= 1 and struggled_count >= 1:
        return "mixed"

    return "default"


def compute_strategy_scores(context: MotivationContext) -> StrategyScores:
    """Compute payoff-like scores for each coach strategy.

    Scores balance short-term fitness gain against burnout and motivation.
    """
    state = infer_runner_state(context)
    scores: Dict[str, float] = {s: 0.0 for s in COACH_STRATEGIES}

    # Base preferences by runner state.
    if state == "engaged":
        scores["push_harder"] += 3.0
        scores["maintain"] += 2.0
        scores["encourage_rest"] += 0.5
        scores["encourage_variety"] += 1.5
    elif state == "mixed":
        scores["maintain"] += 2.5
        scores["encourage_rest"] += 2.0
        scores["encourage_variety"] += 1.5
        scores["push_harder"] -= 1.5
    elif state == "default":
        scores["maintain"] += 2.5
        scores["encourage_rest"] += 2.0
        scores["encourage_variety"] += 1.5
        scores["push_harder"] -= 2.0
    elif state == "bored":
        scores["encourage_variety"] += 3.0
        scores["maintain"] += 1.0
        scores["push_harder"] += 1.0
        scores["encourage_rest"] += 0.5
    elif state == "burnout_risk":
        scores["encourage_rest"] += 3.5
        scores["maintain"] += 1.0
        scores["push_harder"] -= 3.0
        scores["encourage_variety"] += 1.0

    # Streak and adherence modifiers: longer streak and high adherence
    # slightly favor maintain/push, but not if burnout_risk.
    if state != "burnout_risk":
        if context.current_streak >= 14:
            scores["maintain"] += 0.5
            if context.adherence_percent >= 85.0:
                scores["push_harder"] += 0.5

    # Race proximity: closer to race increases value of maintaining or
    # slightly pushing if not burned out.
    days = context.days_to_race
    if days <= 21 and state in {"engaged", "mixed", "default"}:
        scores["maintain"] += 1.0
        scores["push_harder"] += 0.5
        scores["encourage_rest"] += 0.5
    elif days <= 14 and state == "bored":
        # Very close to race: prefer maintaining current structure rather than
        # introducing big terrain changes just for variety.
        scores["maintain"] += 2.0
        scores["encourage_variety"] -= 1.5
    elif days >= 60 and state in {"mixed", "default", "burnout_risk"}:
        scores["encourage_rest"] += 1.0

    # Terrain monotony: increase value of variety.
    unique_terrain = set(context.terrain_last_week)
    if len(unique_terrain) <= 1 and len(context.terrain_last_week) >= 3:
        scores["encourage_variety"] += 1.0

    return StrategyScores(scores=scores)