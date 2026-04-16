"""
Plan vs actual adherence for the pipeline.

Compares one **Module 2 plan week** (scheduled workouts + weekly miles) to **Module 3**
log entries in a recent time window, then builds a **Module 4–compatible motivation**
dict so **Module 5** can use ``adherence_percent`` and existing motivation adjustments.

This stays in ``src/pipeline`` so Module 2/3/5 packages do not depend on each other.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from src.module3_run_logger.store import RunLogStore


def fetch_module3_entries(profile: dict[str, Any], n: int = 100) -> list[dict[str, Any]]:
    """Recent raw run entries from the profile's run log (``id``, ``logged_at``, ``parsed``)."""
    path = profile.get("paths", {}).get("run_log", "data/run_log.json")
    store = RunLogStore(path)
    return store.get_recent_runs(n)


def _parse_logged_at(entry: dict[str, Any]) -> datetime | None:
    raw = entry.get("logged_at")
    if not raw or not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _entries_in_window(
    entries: list[dict[str, Any]],
    *,
    days: int,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Keep entries whose ``logged_at`` is within the last ``days`` days."""
    if now is None:
        now = datetime.now()
    cutoff = now - timedelta(days=days)
    out: list[dict[str, Any]] = []
    for e in entries:
        dt = _parse_logged_at(e)
        if dt is not None and dt >= cutoff:
            out.append(e)
    return out


def _logged_miles(entries: list[dict[str, Any]]) -> float:
    total = 0.0
    for e in entries:
        d = (e.get("parsed") or {}).get("distance")
        if d is not None:
            total += float(d)
    return total


def compute_week_adherence(
    plan_week: dict[str, Any],
    run_entries: list[dict[str, Any]],
    *,
    days_window: int = 7,
    now: datetime | None = None,
) -> dict[str, Any]:
    """
    Compare one plan week to recent logged runs.

    - **Session adherence**: ``logged_sessions / prescribed_sessions`` (capped at 100%).
    - **Volume adherence**: ``logged_miles / prescribed_miles`` (capped at 100%).
    - **adherence_percent**: average of the two (simple, interpretable).

    ``run_entries`` should be Module 3 store entries (``logged_at``, ``parsed``).
    """
    workouts = plan_week.get("workouts") or []
    prescribed_sessions = len(workouts)
    prescribed_miles = float(plan_week.get("total_miles") or 0.0)
    if prescribed_miles <= 0.0 and workouts:
        prescribed_miles = sum(float(w.get("distance") or 0) for w in workouts)

    window = _entries_in_window(run_entries, days=days_window, now=now)
    logged_sessions = len(window)
    logged_miles = _logged_miles(window)

    if prescribed_sessions <= 0:
        session_pct = 100.0
    else:
        session_pct = min(100.0, 100.0 * logged_sessions / prescribed_sessions)

    if prescribed_miles <= 0:
        mile_pct = 100.0
    else:
        mile_pct = min(100.0, 100.0 * logged_miles / prescribed_miles)

    adherence_percent = round((session_pct + mile_pct) / 2.0, 1)

    return {
        "adherence_percent": adherence_percent,
        "prescribed_sessions": prescribed_sessions,
        "logged_sessions_in_window": logged_sessions,
        "prescribed_miles": round(prescribed_miles, 2),
        "logged_miles_in_window": round(logged_miles, 2),
        "session_adherence_pct": round(session_pct, 1),
        "mile_adherence_pct": round(mile_pct, 1),
        "days_window": days_window,
    }


def _days_to_race(profile: dict[str, Any]) -> int:
    rd = (profile.get("planner") or {}).get("race_date")
    if not rd or not isinstance(rd, str):
        return 90
    try:
        race = date.fromisoformat(rd[:10])
        d = (race - date.today()).days
        return max(0, d)
    except ValueError:
        return 90


def _sentiments_for_m4(history: list[dict[str, Any]]) -> list[str]:
    """Map Module 5 history sentiments to Module 4 coarse labels."""
    out: list[str] = []
    for row in history[-5:]:
        s = str(row.get("sentiment", "neutral")).lower()
        if s in ("positive", "good"):
            out.append("good")
        elif s in ("negative", "struggled"):
            out.append("struggled")
        else:
            out.append("neutral")
    return out or ["neutral"]


def _terrains_for_m4(history: list[dict[str, Any]]) -> list[str]:
    known = {"road", "track", "treadmill", "trail"}
    out: list[str] = []
    for row in history[-5:]:
        t = str(row.get("terrain", "road")).strip().lower()
        if t == "grass":
            t = "trail"
        out.append(t if t in known else "road")
    return out if out else ["road"]


def motivation_with_plan_adherence(
    profile: dict[str, Any],
    history: list[dict[str, Any]],
    plan_week: dict[str, Any],
    *,
    base_motivation: dict[str, Any] | None = None,
    days_window: int = 7,
    run_entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Build a **Module 4–valid** motivation dict with ``adherence_percent`` from plan vs log.

    Merges ``base_motivation`` (or ``profile['motivation']``) and fills missing
    ``recent_sentiments`` / ``terrain_last_week`` from ``history`` when needed.
    """
    if run_entries is None:
        run_entries = fetch_module3_entries(profile, n=100)

    ad = compute_week_adherence(plan_week, run_entries, days_window=days_window)
    merged: dict[str, Any] = dict(base_motivation or profile.get("motivation") or {})
    merged["adherence_percent"] = ad["adherence_percent"]
    merged.setdefault("current_streak", 0)
    merged.setdefault("days_to_race", _days_to_race(profile))
    if not merged.get("recent_sentiments"):
        merged["recent_sentiments"] = _sentiments_for_m4(history)
    if not merged.get("terrain_last_week"):
        merged["terrain_last_week"] = _terrains_for_m4(history)
    return merged


__all__ = [
    "compute_week_adherence",
    "fetch_module3_entries",
    "motivation_with_plan_adherence",
]
