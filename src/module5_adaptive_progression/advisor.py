"""
Module 5 - Adaptive Progression System
Progression advisor.
"""

from typing import NamedTuple

from .input_validation import validate_context
from .mdp import (
    ALL_ACTIONS,
    COLD_START_ACTION,
    discretize_state,
    compute_reward,
    VolumeAdjustment,
    IntensityAdjustment,
)
from .features import (
    VOLUME_COMPLETED_ABOVE_BASE,
    VOLUME_COMPLETED_BELOW_BASE,
    estimate_weekly_miles,
    get_terrain_sequence,
    extract_baseline,
    apply_adjustments,
    sentiment_trend,
    apply_motivation_adjustments,
    blend_confidence_with_motivation,
    select_terrain_for_session,
)
from .input_validation import normalize_sentiment_to_canonical, ValidationError
from .q_learning import QLearningEngine

_M1_HOOK_ERRORS = (TypeError, ValueError, KeyError, AttributeError, IndexError)


class _AdaptSession(NamedTuple):
    ctx: dict
    engine: QLearningEngine
    weekly_miles: float
    state: tuple
    next_distance: float
    target_pace: float
    suggested_terrain: str
    confidence: float
    sentiment_trend: str
    reasoning: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_adherence(ctx) -> float:
    """Pull adherence_percent from motivation context, default 100 if absent."""
    motivation = ctx.get("motivation")
    if motivation and "adherence_percent" in motivation:
        return float(motivation["adherence_percent"])
    return 100.0


def _build_state(ctx, weekly_miles):
    terrain_seq = get_terrain_sequence(ctx["history"])
    return discretize_state(
        weekly_miles      = weekly_miles,
        fatigue_score     = ctx["fatigue_score"],
        terrain_history   = terrain_seq,
        workout_type      = ctx["workout_type"],
        adherence_percent = _get_adherence(ctx),   # NEW
    )


def _resolve_q_table_path(ctx, q_table_path_override=None):
    return q_table_path_override if q_table_path_override is not None else ctx.get("q_table_path")


def _load_engine(ctx, q_table_path_override=None):
    path = _resolve_q_table_path(ctx, q_table_path_override)
    if path:
        engine = QLearningEngine.load_or_create(path)
    else:
        engine = QLearningEngine()
    engine.alpha   = ctx["alpha"]
    engine.gamma   = ctx["gamma"]
    engine.epsilon = ctx["epsilon"]
    return engine


def _is_flat_q(engine, state):
    return all(abs(engine._q_value(state, a)) < 1e-12 for a in ALL_ACTIONS)


def _apply_module1_safety(ctx, next_distance, target_pace, terrain):
    validate_fn = ctx.get("validate_fn")
    profile = ctx.get("runner_profile")
    if not validate_fn or not profile:
        return next_distance, target_pace, terrain, ""

    workout = {
        "type":     ctx["workout_type"],
        "distance": float(next_distance),
        "terrain":  terrain,
    }
    try:
        result = validate_fn(profile, workout)
    except _M1_HOOK_ERRORS:
        return next_distance, target_pace, terrain, ""

    if result.get("safe", True):
        return next_distance, target_pace, terrain, ""

    alt = result.get("alternative")
    if isinstance(alt, dict) and alt.get("distance") is not None:
        nd = float(alt["distance"])
        tt = str(alt.get("terrain", terrain)).strip().lower()
        note = (
            f"Module 1 safety adjustment: {result.get('reason', '')} "
            f"Applied alternative session (~{nd} mi, {tt})."
        )
        return round(nd, 2), float(target_pace), tt, note.strip()

    reason = result.get("reason", "")
    return next_distance, target_pace, terrain, f"Module 1 flagged concerns: {reason}"


def _parse_planned_action(outcome):
    raw = outcome.get("planned_action")
    if raw is None:
        return None
    if not isinstance(raw, (tuple, list)) or len(raw) != 2:
        raise ValidationError("planned_action must be a pair [volume, intensity]")
    try:
        v, i = int(raw[0]), int(raw[1])
    except (TypeError, ValueError) as exc:
        raise ValidationError("planned_action values must be integers -1, 0, or 1") from exc
    vol_map = {x.value: x for x in VolumeAdjustment}
    int_map = {x.value: x for x in IntensityAdjustment}
    if v not in vol_map or i not in int_map:
        raise ValidationError("planned_action values must be integers -1, 0, or 1")
    return vol_map[v], int_map[i]


def _infer_action_from_outcome(outcome, base_dist):
    dist_after = float(outcome.get("distance_completed", base_dist))
    if dist_after > base_dist * VOLUME_COMPLETED_ABOVE_BASE:
        vol = VolumeAdjustment.INCREASE
    elif dist_after < base_dist * VOLUME_COMPLETED_BELOW_BASE:
        vol = VolumeAdjustment.DECREASE
    else:
        vol = VolumeAdjustment.HOLD

    sentiment_after = normalize_sentiment_to_canonical(outcome.get("sentiment", "neutral"))
    if sentiment_after == "positive":
        intensity = IntensityAdjustment.HARDER
    elif sentiment_after == "negative":
        intensity = IntensityAdjustment.EASIER
    else:
        intensity = IntensityAdjustment.HOLD
    return vol, intensity


def _build_reasoning(
    vol, intensity, terrain, state, weekly_miles, fatigue_score,
    trend, base_distance, next_distance, target_pace, confidence,
    adherence_percent=100.0,
    motivation_note="", cold_start_note="",
):
    fitness_tier  = state[0].value
    fatigue_level = state[1].value
    streak        = state[2].value
    workout_cat   = state[3].value if len(state) > 3 else "easy"
    adherence_tier = state[4].value if len(state) > 4 else "high"  # NEW

    parts = []

    if cold_start_note:
        parts.append(cold_start_note)

    # NEW: surface adherence tier prominently in reasoning
    if adherence_tier == "low":
        parts.append(
            f"Plan adherence is low ({adherence_percent:.0f}%) — "
            "recommending a more achievable session to rebuild consistency. "
            "Completing easier sessions is more valuable than skipping harder ones."
        )
    elif adherence_tier == "medium":
        parts.append(
            f"Plan adherence is moderate ({adherence_percent:.0f}%) — "
            "holding volume steady to prioritise completion over progression."
        )
    else:
        parts.append(
            f"Plan adherence is strong ({adherence_percent:.0f}%) — "
            "progression adjustments are based on full training load."
        )

    if vol == VolumeAdjustment.INCREASE:
        parts.append(
            f"Recent weekly mileage ({weekly_miles:.1f} mi) and sentiment trend "
            f"({trend}) support a ~10% distance increase."
        )
    elif vol == VolumeAdjustment.DECREASE:
        parts.append(
            f"Fatigue level is {fatigue_level}; reducing volume to manage recovery load."
        )
    else:
        parts.append("Volume held steady to consolidate current fitness gains.")

    if intensity == IntensityAdjustment.HARDER:
        parts.append("Positive adaptation signals support a modest pace increase.")
    elif intensity == IntensityAdjustment.EASIER:
        parts.append("Backing off pace to prioritise aerobic base and reduce injury risk.")
    else:
        parts.append("Target pace unchanged.")

    if streak == "same":
        parts.append(
            f"Switched terrain to {terrain} after same-terrain streak."
        )
    else:
        parts.append(f"Terrain: {terrain}.")

    parts.append(f"Workout category: {workout_cat}; fitness tier: {fitness_tier}.")

    if confidence < 0.3:
        parts.append(
            "Note: limited training history — recommendation will sharpen as more runs are logged."
        )

    if motivation_note:
        parts.append(motivation_note)

    return " ".join(parts)


def _compute_adapt_session(ctx, engine) -> _AdaptSession:
    weekly = estimate_weekly_miles(ctx["history"])
    state  = _build_state(ctx, weekly)
    action = engine.select_action(state, force_exploit=True)
    vol, intensity = action

    base_distance, base_pace = extract_baseline(ctx["history"])
    next_distance, target_pace = apply_adjustments(
        base_distance, base_pace, vol, intensity
    )

    terrain    = select_terrain_for_session(ctx["history"], ctx["terrain"], ctx.get("motivation"))
    confidence = engine.confidence(state)
    trend      = sentiment_trend(ctx["history"])
    adherence  = _get_adherence(ctx)   # NEW

    cold_note = ""
    if _is_flat_q(engine, state):
        cold_note = (
            "Q-table is still flat for this state (cold start); using conservative "
            f"default action {COLD_START_ACTION[0].name}/{COLD_START_ACTION[1].name}. "
        )

    motivation_note = ""
    if ctx.get("motivation"):
        next_distance, target_pace, terrain, motivation_note = apply_motivation_adjustments(
            next_distance, target_pace, terrain, ctx["motivation"], base_distance,
        )
        confidence = blend_confidence_with_motivation(confidence, ctx["motivation"])

    next_distance, target_pace, terrain, m1_note = _apply_module1_safety(
        ctx, next_distance, target_pace, terrain
    )

    reasoning = _build_reasoning(
        vol, intensity, terrain, state, weekly, ctx["fatigue_score"],
        trend, base_distance, next_distance, target_pace, confidence,
        adherence_percent=adherence,                                    # NEW
        motivation_note=motivation_note + (" " + m1_note if m1_note else ""),
        cold_start_note=cold_note,
    )

    return _AdaptSession(
        ctx=ctx, engine=engine, weekly_miles=weekly, state=state,
        next_distance=next_distance, target_pace=target_pace,
        suggested_terrain=terrain, confidence=confidence,
        sentiment_trend=trend, reasoning=reasoning,
    )


def _snapshot_q_values(engine, state) -> dict:
    return {str(a): round(engine._q_value(state, a), 4) for a in ALL_ACTIONS}


def _simple_recommendation_dict(s: _AdaptSession) -> dict:
    return {
        "next_distance":      s.next_distance,
        "target_pace":        s.target_pace,
        "suggested_terrain":  s.suggested_terrain,
        "confidence":         round(s.confidence, 2),
        "reasoning":          s.reasoning,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def adapt_progression(context):
    ctx    = validate_context(context)
    engine = _load_engine(ctx)
    return _simple_recommendation_dict(_compute_adapt_session(ctx, engine))


def adapt_progression_detailed(context):
    ctx    = validate_context(context)
    engine = _load_engine(ctx)
    s      = _compute_adapt_session(ctx, engine)
    q_values = _snapshot_q_values(s.engine, s.state)

    out = {
        **_simple_recommendation_dict(s),
        "state":           tuple(x.value if hasattr(x, "value") else x for x in s.state),
        "episode_count":   s.engine.episode_count,
        "epsilon":         round(s.engine.epsilon, 4),
        "q_values":        q_values,
        "sentiment_trend": s.sentiment_trend,
        "weekly_miles":    round(s.weekly_miles, 2),
        "adherence_percent": _get_adherence(ctx),   # NEW — surface in detailed output
    }
    if ctx.get("motivation") is not None:
        out["motivation"] = ctx["motivation"]
    return out


def train_on_run(context, outcome, q_table_path=None):
    ctx    = validate_context(context)
    path   = _resolve_q_table_path(ctx, q_table_path)
    engine = _load_engine(ctx, path)

    weekly    = estimate_weekly_miles(ctx["history"])
    state     = _build_state(ctx, weekly)   # now includes adherence in state
    adherence = _get_adherence(ctx)         # NEW

    base_dist, _ = extract_baseline(ctx["history"])
    planned = _parse_planned_action(outcome)
    if planned is not None:
        action = planned
    else:
        action = _infer_action_from_outcome(outcome, base_dist)

    terrain_after   = str(outcome.get("terrain", ctx["terrain"])).lower()
    fatigue_before  = ctx["fatigue_score"]
    fatigue_after   = float(outcome.get("fatigue_score_after", fatigue_before))
    sentiment_after = normalize_sentiment_to_canonical(outcome.get("sentiment", "neutral"))
    terrain_before  = ctx["history"][-1]["terrain"] if ctx["history"] else ctx["terrain"]

    reward = compute_reward(
        sentiment             = sentiment_after,
        fatigue_score_before  = fatigue_before,
        fatigue_score_after   = fatigue_after,
        terrain_before        = terrain_before,
        terrain_after         = terrain_after,
        adherence_percent     = adherence,      # NEW — adherence now primary reward signal
        motivation            = ctx.get("motivation"),
    )

    next_terrain_seq = get_terrain_sequence(ctx["history"]) + [terrain_after]
    dist_after  = float(outcome.get("distance_completed", base_dist))
    next_weekly = weekly + dist_after

    next_state = discretize_state(
        weekly_miles      = next_weekly,
        fatigue_score     = fatigue_after,
        terrain_history   = next_terrain_seq,
        workout_type      = ctx["workout_type"],
        adherence_percent = adherence,          # NEW — carry adherence into next state
    )

    new_q = engine.update(state, action, reward, next_state)
    engine.end_episode()

    if path:
        engine.save(path)

    return {
        "q_update":          round(new_q, 4),
        "reward":            round(reward, 4),
        "episode_count":     engine.episode_count,
        "action":            (action[0].value, action[1].value),
        "next_state":        tuple(s.value if hasattr(s, "value") else s for s in next_state),
        "adherence_percent": adherence,         # NEW — surface in return dict
    }