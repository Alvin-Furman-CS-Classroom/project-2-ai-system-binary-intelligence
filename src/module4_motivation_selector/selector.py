from __future__ import annotations

from typing import Dict, Tuple

from .game_model import COACH_STRATEGIES, compute_strategy_scores, infer_runner_state
from .input_validation import MotivationContext, validate_and_normalize_context


def _message_tone_for(strategy: str, state: str) -> str:
    if strategy == "push_harder":
        return "motivating" if state == "engaged" else "cautious"
    if strategy == "encourage_rest":
        return "supportive"
    if strategy == "encourage_variety":
        return "motivating"
    return "neutral"


def _reasoning_for(
    strategy: str,
    state: str,
    context: MotivationContext,
    best_and_second_best: Tuple[str, str] | None = None,
    scores: Dict[str, float] | None = None,
) -> str:
    sentiments = ", ".join(context.recent_sentiments)
    terrain = ", ".join(context.terrain_last_week) or "mixed surfaces"
    base = []

    base.append(
        f"Recent sentiments ({sentiments}) and adherence "
        f"around {int(context.adherence_percent)}% suggest the runner is {state}."
    )
    base.append(
        f"Current streak is {context.current_streak} day(s) with terrain last week on {terrain}."
    )
    if context.days_to_race > 0:
        base.append(f"There are {context.days_to_race} day(s) until race day.")

    if strategy == "encourage_variety":
        base.append(
            "Monotonous terrain can cause mental fatigue; suggesting a different surface "
            "can improve engagement while keeping training on track."
        )
    elif strategy == "encourage_rest":
        base.append(
            "Signs of fatigue or low adherence make a short recovery focus valuable to "
            "protect long-term consistency."
        )
    elif strategy == "push_harder":
        base.append(
            "Strong adherence and mostly positive sentiments support a small increase in "
            "challenge to stimulate progress."
        )
    elif strategy == "maintain":
        base.append(
            "Maintaining the current load balances fitness gains with motivation and injury risk."
        )

    if best_and_second_best is not None and scores is not None:
        best, second = best_and_second_best
        if second and second in COACH_STRATEGIES and second != best:
            best_score = scores.get(best, 0.0)
            second_score = scores.get(second, 0.0)
            base.append(
                f"'{best}' achieved payoff {best_score:.2f} versus {second_score:.2f} "
                f"for the next-best '{second}', illustrating BR_coach as the "
                "highest-utility response to the current runner state."
            )

    return " ".join(base)


def select_motivation_strategy(context: Dict) -> Dict:
    """Select a motivation/coaching strategy for the runner.

    Args:
        context: Dict with keys:
            - current_streak: int
            - recent_sentiments: list[str]
            - terrain_last_week: list[str]
            - adherence_percent: float | int
            - days_to_race: int

    Returns:
        Dict with:
            - strategy: str
            - message_tone: str
            - reasoning: str
    """
    detailed = select_motivation_strategy_detailed(context)
    return {
        "strategy": detailed["strategy"],
        "message_tone": detailed["message_tone"],
        "reasoning": detailed["reasoning"],
    }


def select_motivation_strategy_detailed(context: Dict) -> Dict:
    """Detailed variant exposing internal scores for inspection.

    Returns:
        Dict with:
            - strategy: str
            - message_tone: str
            - reasoning: str
            - scores: mapping of strategy -> score
            - inferred_state: str
    """
    normalized: MotivationContext = validate_and_normalize_context(context)
    scores = compute_strategy_scores(normalized)
    best = scores.best_strategy()

    # For explanation, also find second-best strategy (if any).
    sorted_strategies = sorted(
        COACH_STRATEGIES,
        key=lambda s: scores.scores.get(s, float("-inf")),
        reverse=True,
    )
    second_best = sorted_strategies[1] if len(sorted_strategies) > 1 else ""

    state = infer_runner_state(normalized)
    tone = _message_tone_for(best, state)
    reasoning = _reasoning_for(
        best,
        state,
        normalized,
        (best, second_best),
        scores.scores,
    )

    return {
        "strategy": best,
        "message_tone": tone,
        "reasoning": reasoning,
        "scores": scores.scores,
        "inferred_state": state,
    }