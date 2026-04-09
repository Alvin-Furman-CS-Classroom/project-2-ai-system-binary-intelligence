"""
Aggregate Module 3–style run history into numeric features for Module 6.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from .constants import TERRAIN_TYPES


def _parse_date(s: str | None) -> datetime | None:
    if not s or not isinstance(s, str):
        return None
    s = s.strip()[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _pace_minutes(row: dict[str, Any]) -> float:
    if "pace_minutes" in row and row["pace_minutes"] is not None:
        return float(row["pace_minutes"])
    if "pace" in row and row["pace"] is not None:
        return float(row["pace"])
    return 10.0


def _distance(row: dict[str, Any]) -> float:
    d = row.get("distance")
    return float(d) if d is not None else 0.0


def _terrain(row: dict[str, Any]) -> str:
    t = str(row.get("terrain") or "road").strip().lower()
    if t == "grass":
        return "trail"
    return t if t in TERRAIN_TYPES else "road"


def _is_negative_sentiment(row: dict[str, Any]) -> bool:
    s = str(row.get("sentiment") or "neutral").strip().lower()
    if s in ("negative", "struggled", "bad", "terrible", "exhausted", "hurt", "awful"):
        return True
    return False


def aggregate_history(
    history: list[dict[str, Any]],
    *,
    weeks_window: int = 12,
    days_to_race: int = 56,
    adherence_pct: float = 85.0,
) -> dict[str, float]:
    """
    Turn a list of run dicts (Module 3 parse shape or Module 5 history shape)
    into aggregate training features (excluding age, goal, experience — caller merges).
    """
    if not history:
        return {
            "weeks_of_training": 0.0,
            "avg_weekly_miles_last_12w": 0.0,
            "peak_weekly_miles": 0.0,
            "longest_run_miles": 0.0,
            "num_runs_20_plus": 0.0,
            "pct_miles_road": 33.0,
            "pct_miles_trail": 34.0,
            "pct_miles_track": 33.0,
            "adherence_pct": float(adherence_pct),
            "days_to_race": float(days_to_race),
            "negative_sentiment_rate": 0.0,
        }

    # Sort by date when present
    indexed = [(i, r) for i, r in enumerate(history)]
    indexed.sort(key=lambda x: (_parse_date(x[1].get("date")) or datetime.min, x[0]))
    runs = [r for _, r in indexed]
    dates = [_parse_date(r.get("date")) for r in runs]

    # Last `weeks_window` "pseudo-weeks": chunk by calendar week from last date
    last_dt = max((d for d in dates if d is not None), default=None)
    if last_dt is None:
        recent = runs[-min(len(runs), weeks_window * 4) :]
    else:
        recent = []
        for r, d in zip(runs, dates):
            if d is None:
                recent.append(r)
                continue
            weeks_ago = (last_dt - d).days // 7
            if weeks_ago < weeks_window:
                recent.append(r)
        if not recent:
            recent = runs[-min(len(runs), weeks_window * 4) :]

    miles_by_week: defaultdict[int, float] = defaultdict(float)
    for r in recent:
        d = _parse_date(r.get("date"))
        if d is None or last_dt is None:
            wk = 0
        else:
            wk = (last_dt - d).days // 7
        miles_by_week[wk] += _distance(r)

    weekly_totals = list(miles_by_week.values()) if miles_by_week else [sum(_distance(r) for r in recent)]
    avg_weekly = sum(weekly_totals) / max(1, len(weekly_totals))
    peak_weekly = max(weekly_totals) if weekly_totals else 0.0
    longest = max((_distance(r) for r in runs), default=0.0)
    n20 = sum(1 for r in runs if _distance(r) >= 19.5)

    terrain_miles: defaultdict[str, float] = defaultdict(float)
    for r in runs:
        terrain_miles[_terrain(r)] += _distance(r)
    total_dist = sum(terrain_miles.values()) or 1.0
    pct_road = 100.0 * terrain_miles["road"] / total_dist
    pct_trail = 100.0 * terrain_miles["trail"] / total_dist
    pct_track = 100.0 * (terrain_miles["track"] + terrain_miles["treadmill"]) / total_dist

    neg = sum(1 for r in runs if _is_negative_sentiment(r))
    neg_rate = neg / max(1, len(runs))

    # Approximate weeks of training from span of dates
    first_dt = min((d for d in dates if d is not None), default=None)
    if first_dt and last_dt:
        span_weeks = max(1, (last_dt - first_dt).days // 7 + 1)
    else:
        span_weeks = min(weeks_window, max(1, len(runs) // 3))

    return {
        "weeks_of_training": float(span_weeks),
        "avg_weekly_miles_last_12w": round(avg_weekly, 2),
        "peak_weekly_miles": round(peak_weekly, 2),
        "longest_run_miles": round(longest, 2),
        "num_runs_20_plus": float(min(n20, 10)),
        "pct_miles_road": round(pct_road, 2),
        "pct_miles_trail": round(pct_trail, 2),
        "pct_miles_track": round(pct_track, 2),
        "adherence_pct": float(adherence_pct),
        "days_to_race": float(days_to_race),
        "negative_sentiment_rate": round(neg_rate, 4),
    }
