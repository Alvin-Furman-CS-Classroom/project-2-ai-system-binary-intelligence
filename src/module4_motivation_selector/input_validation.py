from __future__ import annotations

from dataclasses import dataclass
from typing import List


SENTIMENT_GOOD = {
    "great",
    "good",
    "awesome",
    "strong",
    "happy",
    "positive",
    "excellent",
    "easy",  # Module 3 effort level
}
SENTIMENT_NEUTRAL = {"ok", "fine", "neutral", "steady", "moderate"}  # Module 3 effort
SENTIMENT_STRUGGLED = {
    "bad",
    "tired",
    "exhausted",
    "hurt",
    "struggled",
    "terrible",
    "negative",
    "hard",  # Module 3 effort
}

# For consistency with other modules, we only accept these canonical terrain types.
KNOWN_TERRAINS = {"road", "track", "treadmill", "trail"}


@dataclass
class MotivationContext:
    current_streak: int
    recent_sentiments: List[str]
    terrain_last_week: List[str]
    adherence_percent: float
    days_to_race: int


def _normalize_sentiment(value: str) -> str:
    """Map raw sentiment strings into coarse buckets."""
    if not value:
        return "neutral"

    v = value.strip().lower()
    if v in SENTIMENT_GOOD:
        return "good"
    if v in SENTIMENT_STRUGGLED:
        return "struggled"
    if v in SENTIMENT_NEUTRAL:
        return "neutral"
    # Fallback: simple keyword checks
    if any(k in v for k in ("great", "good", "strong", "awesome")):
        return "good"
    if any(k in v for k in ("tired", "hurt", "injury", "terrible", "awful")):
        return "struggled"
    return "neutral"


def validate_and_normalize_context(raw: dict) -> MotivationContext:
    """Validate and normalize the raw context dict into MotivationContext.

    Missing values are filled with conservative defaults.
    """
    if raw is None:
        raw = {}

    # Basic numeric validation: follow the pattern from other modules and
    # raise on clearly invalid data rather than silently clamping.
    current_streak_raw = raw.get("current_streak", 0)
    try:
        current_streak = int(current_streak_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"current_streak must be an int, got {current_streak_raw!r}") from exc
    if current_streak < 0:
        raise ValueError("current_streak cannot be negative")

    adherence_raw = raw.get("adherence_percent", 0.0)
    try:
        adherence_percent = float(adherence_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"adherence_percent must be a number, got {adherence_raw!r}") from exc
    if not 0.0 <= adherence_percent <= 100.0:
        raise ValueError("adherence_percent must be between 0 and 100")

    days_raw = raw.get("days_to_race", 0)
    try:
        days_to_race = int(days_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"days_to_race must be an int, got {days_raw!r}") from exc
    if days_to_race < 0:
        raise ValueError("days_to_race cannot be negative")

    recent_sentiments_raw = raw.get("recent_sentiments") or []
    if not isinstance(recent_sentiments_raw, list):
        recent_sentiments_raw = [str(recent_sentiments_raw)]
    recent_sentiments = [
        _normalize_sentiment(str(s)) for s in recent_sentiments_raw
    ]
    if not recent_sentiments:
        recent_sentiments = ["neutral"]

    terrain_last_week_raw = raw.get("terrain_last_week") or []
    if not isinstance(terrain_last_week_raw, list):
        terrain_last_week_raw = [str(terrain_last_week_raw)]
    terrain_last_week = []
    for t in terrain_last_week_raw:
        if not t:
            continue
        terrain = str(t).strip().lower()
        if not terrain:
            continue
        if terrain not in KNOWN_TERRAINS:
            raise ValueError(
                f"Unknown terrain '{terrain}'. Expected one of {sorted(KNOWN_TERRAINS)}."
            )
        terrain_last_week.append(terrain)
    if not terrain_last_week:
        raise ValueError(
            "terrain_last_week must contain at least one valid terrain entry."
        )

    return MotivationContext(
        current_streak=current_streak,
        recent_sentiments=recent_sentiments,
        terrain_last_week=terrain_last_week,
        adherence_percent=adherence_percent,
        days_to_race=days_to_race,
    )

