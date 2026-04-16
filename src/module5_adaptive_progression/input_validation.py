"""
Module 5 - Adaptive Progression System
Input validation.

Validates the context dict passed to adapt_progression / adapt_progression_detailed
and normalizes optional fields to sensible defaults.

Optional ``motivation`` uses the same shape as Module 4's context (validated via
``module4_motivation_selector.input_validation``) so coaching signals from Module 4
feed progression decisions without duplicating rules.
"""

from .mdp import VALID_TERRAINS

VALID_WORKOUT_TYPES = {
    "easy run", "tempo run", "long run", "interval", "recovery run",
    "hill workout", "fartlek", "race", "time trial", "cross training"
}
# Aliases from proposals, Module 3 effort labels, or informal text → canonical
_POSITIVE_ALIASES = frozenset({
    "positive", "good", "great", "excellent", "happy", "awesome", "strong",
})
_NEGATIVE_ALIASES = frozenset({
    "negative", "bad", "struggled", "terrible", "exhausted", "hurt", "awful",
})
_NEUTRAL_ALIASES = frozenset({
    "neutral", "ok", "fine", "moderate", "steady",
})


def normalize_sentiment_to_canonical(raw):
    """
    Map history / outcome sentiment labels to Module 5 canonical values.

    Accepts Module 3 mood labels (positive/neutral/negative) and common aliases
    (e.g. good, excellent, struggled) so proposal examples and informal data work.
    """
    if raw is None:
        return "neutral"
    s = str(raw).strip().lower()
    if s in _POSITIVE_ALIASES:
        return "positive"
    if s in _NEGATIVE_ALIASES:
        return "negative"
    if s in _NEUTRAL_ALIASES:
        return "neutral"
    return "neutral"


class ValidationError(ValueError):
    """Raised when input fails validation."""
    pass


def validate_context(context):
    """
    Validate and normalize the input context for Module 5.

    Parameters
    ----------
    context : dict

    Returns
    -------
    dict : normalized context with defaults filled in

    Raises
    ------
    ValidationError if required fields are missing or malformed.
    """
    if not isinstance(context, dict):
        raise ValidationError("context must be a dict")

    # --- Required: workout_type ---
    workout_type = context.get("workout_type")
    if workout_type is None:
        raise ValidationError("context must include 'workout_type'")
    if not isinstance(workout_type, str):
        raise ValidationError("workout_type must be a string")
    workout_type = workout_type.strip().lower()
    if workout_type not in VALID_WORKOUT_TYPES:
        raise ValidationError(
            f"Unknown workout_type '{workout_type}'. "
            f"Valid types: {sorted(VALID_WORKOUT_TYPES)}"
        )

    # --- Required: terrain ---
    terrain = context.get("terrain")
    if terrain is None:
        raise ValidationError("context must include 'terrain'")
    terrain = terrain.strip().lower()
    if terrain not in VALID_TERRAINS:
        raise ValidationError(
            f"Unknown terrain '{terrain}'. Valid terrains: {sorted(VALID_TERRAINS)}"
        )

    # --- Required: fatigue_score ---
    fatigue_score = context.get("fatigue_score")
    if fatigue_score is None:
        raise ValidationError("context must include 'fatigue_score'")
    try:
        fatigue_score = float(fatigue_score)
    except (TypeError, ValueError):
        raise ValidationError("fatigue_score must be a number")
    if not 0.0 <= fatigue_score <= 1.0:
        raise ValidationError("fatigue_score must be between 0.0 and 1.0")

    # --- Required: history ---
    history = context.get("history")
    if history is None:
        raise ValidationError("context must include 'history' (list of past runs)")
    if not isinstance(history, list):
        raise ValidationError("history must be a list")

    # Validate each history entry
    validated_history = []
    for i, entry in enumerate(history):
        validated_history.append(_validate_history_entry(entry, index=i))

    # --- Optional: q_table_path ---
    q_table_path = context.get("q_table_path")
    if q_table_path is not None and not isinstance(q_table_path, str):
        raise ValidationError("q_table_path must be a string path")

    # --- Optional: motivation (Module 4 context — same keys as select_motivation_strategy) ---
    motivation = _validate_motivation_optional(context.get("motivation"))

    # --- Optional: Q-learning hyperparameters ---
    alpha = _optional_float(context.get("alpha"), "alpha", default=0.3, min_v=0.01, max_v=1.0)
    gamma = _optional_float(context.get("gamma"), "gamma", default=0.9, min_v=0.0, max_v=1.0)
    epsilon = _optional_float(context.get("epsilon"), "epsilon", default=0.2, min_v=0.0, max_v=1.0)

    # --- Optional: Module 1 safety hook ---
    validate_fn = context.get("validate_fn")
    if validate_fn is not None and not callable(validate_fn):
        raise ValidationError("validate_fn must be callable or None")
    runner_profile = context.get("runner_profile")
    if runner_profile is not None and not isinstance(runner_profile, dict):
        raise ValidationError("runner_profile must be a dict or None")

    return {
        "workout_type":  workout_type,
        "terrain":       terrain,
        "fatigue_score": fatigue_score,
        "history":       validated_history,
        "q_table_path":  q_table_path,
        "motivation":    motivation,
        "alpha":         alpha,
        "gamma":         gamma,
        "epsilon":       epsilon,
        "validate_fn":   validate_fn,
        "runner_profile": runner_profile,
    }


def _optional_float(raw, name, default, min_v, max_v):
    if raw is None:
        return default
    try:
        v = float(raw)
    except (TypeError, ValueError):
        raise ValidationError(f"{name} must be a number") from None
    if not min_v <= v <= max_v:
        raise ValidationError(f"{name} must be between {min_v} and {max_v}")
    return v


def _validate_motivation_optional(motivation):
    """
    If present, validate using Module 4's rules (streak, sentiments, terrain, etc.).
    Returns a plain dict of normalized fields, or None.
    """
    if motivation is None:
        return None
    if not isinstance(motivation, dict):
        raise ValidationError("motivation must be a dict or None")

    from src.module4_motivation_selector.input_validation import (
        validate_and_normalize_context as validate_m4_context,
    )

    try:
        mc = validate_m4_context(motivation)
    except ValueError as exc:
        raise ValidationError(f"Invalid motivation (Module 4 context): {exc}") from exc
    return {
        "current_streak": int(mc.current_streak),
        "recent_sentiments": list(mc.recent_sentiments),
        "terrain_last_week": list(mc.terrain_last_week),
        "adherence_percent": float(mc.adherence_percent),
        "days_to_race": int(mc.days_to_race),
    }


def _validate_history_entry(entry, index):
    """Validate and normalize a single history dict."""
    if not isinstance(entry, dict):
        raise ValidationError(f"history[{index}] must be a dict")

    required = ["distance", "pace", "terrain", "sentiment"]
    for field in required:
        if field not in entry:
            raise ValidationError(
                f"history[{index}] is missing required field '{field}'"
            )

    try:
        distance = float(entry["distance"])
    except (TypeError, ValueError):
        raise ValidationError(f"history[{index}].distance must be a number")
    if distance <= 0:
        raise ValidationError(f"history[{index}].distance must be positive")

    try:
        pace = float(entry["pace"])
    except (TypeError, ValueError):
        raise ValidationError(f"history[{index}].pace must be a number")
    if pace <= 0:
        raise ValidationError(f"history[{index}].pace must be positive (min/mile)")

    terrain = str(entry["terrain"]).strip().lower()
    if terrain not in VALID_TERRAINS:
        raise ValidationError(
            f"history[{index}].terrain '{terrain}' is invalid. "
            f"Valid: {sorted(VALID_TERRAINS)}"
        )

    sentiment = normalize_sentiment_to_canonical(entry["sentiment"])

    return {
        "date":      entry.get("date", ""),
        "distance":  distance,
        "pace":      pace,
        "terrain":   terrain,
        "sentiment": sentiment,
    }