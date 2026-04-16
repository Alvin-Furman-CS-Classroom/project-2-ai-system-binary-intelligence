"""
Module 5 - Adaptive Progression System
Feature extraction from validated run history.
"""

from datetime import datetime
from statistics import mean

RECENT_WINDOW = 7

def _parse_run_date(entry) -> datetime | None:
    raw = entry.get("date") or entry.get("Date")
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw[:10], fmt)
        except ValueError:
            continue
    return None


def estimate_weekly_miles(history):
    if not history:
        return 0.0
    recent = history[-RECENT_WINDOW:]
    total_distance = sum(float(r["distance"]) for r in recent)
    dates = [_parse_run_date(r) for r in recent]
    dates = [d for d in dates if d is not None]
    if len(dates) >= 2:
        span_days = max(1.0, (max(dates) - min(dates)).days + 1.0)
        return total_distance / span_days * 7.0
    return total_distance


def get_terrain_sequence(history):
    return [r["terrain"] for r in history]


DISTANCE_INCREASE_FACTOR = 1.10
DISTANCE_DECREASE_FACTOR = 0.90
PACE_FASTER_FACTOR        = 0.97
PACE_SLOWER_FACTOR        = 1.05

VOLUME_COMPLETED_ABOVE_BASE = 1.05
VOLUME_COMPLETED_BELOW_BASE = 0.95


def apply_adjustments(base_distance, base_pace, volume_adj, intensity_adj):
    from .mdp import VolumeAdjustment, IntensityAdjustment

    if volume_adj == VolumeAdjustment.INCREASE:
        next_distance = round(float(base_distance) * DISTANCE_INCREASE_FACTOR, 2)
    elif volume_adj == VolumeAdjustment.DECREASE:
        next_distance = round(float(base_distance) * DISTANCE_DECREASE_FACTOR, 2)
    else:
        next_distance = round(float(base_distance), 2)

    if intensity_adj == IntensityAdjustment.HARDER:
        next_pace = round(float(base_pace) * PACE_FASTER_FACTOR, 2)
    elif intensity_adj == IntensityAdjustment.EASIER:
        next_pace = round(float(base_pace) * PACE_SLOWER_FACTOR, 2)
    else:
        next_pace = round(float(base_pace), 2)

    return next_distance, next_pace


def extract_baseline(history):
    if not history:
        return 3.0, 10.0
    last = history[-1]
    return last["distance"], last["pace"]


def recent_sentiments(history, n=3):
    return [r["sentiment"] for r in history[-n:]]


def sentiment_trend(history):
    sents = recent_sentiments(history, n=5)
    if len(sents) < 2:
        return "insufficient_data"
    mapping = {"positive": 1, "neutral": 0, "negative": -1}
    scores = [mapping.get(s, 0) for s in sents]
    first_half  = mean(scores[:len(scores)//2]) if len(scores) >= 2 else 0
    second_half = mean(scores[len(scores)//2:]) if len(scores) >= 2 else 0
    diff = second_half - first_half
    if diff > 0.3:
        return "improving"
    if diff < -0.3:
        return "declining"
    return "stable"


def apply_motivation_adjustments(
    next_distance,
    target_pace,
    suggested_terrain,
    motivation,
    base_distance,
):
    """
    Refine Q-learning outputs using Module 4 coaching context.

    NOTE: the old hard-coded adherence volume trim (nd *= 0.93) has been
    removed. Adherence is now encoded in the MDP state and reward signal,
    so the Q-table learns appropriate volume adjustments on its own.
    The remaining adjustments here handle signals the Q-table cannot see:
    race proximity, recent struggle streaks, and terrain monotony.
    """
    if not motivation:
        return next_distance, target_pace, suggested_terrain, ""

    from .mdp import VALID_TERRAINS

    notes = []
    nd = float(next_distance)
    tp = float(target_pace)
    st = suggested_terrain

    adhere = motivation["adherence_percent"]
    days   = motivation["days_to_race"]
    streak = motivation["current_streak"]
    recent = motivation["recent_sentiments"]
    terr_last = motivation["terrain_last_week"]

    # REMOVED: nd *= 0.93 when adhere < 70
    # Adherence now drives reward and state — the Q-table handles this.

    if days <= 21 and streak >= 10:
        nd = min(nd, float(base_distance) * 1.08)
        notes.append(
            "Race window: capping volume increase to prioritise freshness (Module 4 signal)."
        )

    struggled = sum(1 for s in recent if s == "struggled")
    if struggled >= 2:
        tp *= 1.05
        notes.append(
            "Recent tough sessions; easing target pace slightly (Module 4 signal)."
        )

    if len(terr_last) >= 3 and len(set(terr_last)) == 1 and terr_last[0] == st:
        alternates = [t for t in sorted(VALID_TERRAINS) if t != terr_last[0]]
        if alternates:
            st = alternates[0]
            notes.append(
                "Monotonous terrain pattern; suggesting surface variety (Module 4 signal)."
            )

    return round(nd, 2), round(tp, 2), st, " ".join(notes)


def blend_confidence_with_motivation(confidence, motivation):
    """
    Down-weight confidence when adherence is low.

    The Q-table's recommendations for a low-adherence runner are less
    reliable because the training data from skipped sessions is missing.
    """
    if not motivation:
        return confidence
    adhere = motivation["adherence_percent"] / 100.0
    return min(1.0, float(confidence) * (0.5 + 0.5 * adhere))


def select_terrain_for_session(history, default_terrain: str, motivation=None) -> str:
    from .mdp import VALID_TERRAINS

    terrains = sorted(VALID_TERRAINS)
    default_terrain = str(default_terrain).strip().lower()
    if default_terrain not in VALID_TERRAINS:
        default_terrain = "road"

    if motivation and len(motivation.get("terrain_last_week", [])) >= 3:
        tlw = motivation["terrain_last_week"]
        if len(set(tlw)) == 1:
            alternates = [t for t in terrains if t != tlw[0]]
            if alternates:
                return alternates[0]

    seq = get_terrain_sequence(history)
    if len(seq) >= 2 and seq[-1] == seq[-2]:
        last = seq[-1]
        alternates = [t for t in terrains if t != last]
        return alternates[0] if alternates else default_terrain

    return default_terrain