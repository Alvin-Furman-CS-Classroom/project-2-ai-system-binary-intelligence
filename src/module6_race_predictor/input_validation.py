"""Validate runner snapshot for predict_race_readiness."""

from __future__ import annotations

import re
from typing import Any

from .constants import HALF_MARATHON_KM, MARATHON_KM, EXPERIENCE_LEVELS


class ValidationError(ValueError):
    pass


def _parse_time_to_minutes(s: str) -> float:
    s = str(s).strip()
    if not s:
        return 270.0
    parts = s.split(":")
    try:
        if len(parts) == 3:
            h, m, sec = int(parts[0]), int(parts[1]), int(parts[2])
            return h * 60 + m + sec / 60.0
        if len(parts) == 2:
            h, m = int(parts[0]), int(parts[1])
            return h * 60 + m
    except ValueError as exc:
        raise ValidationError(f"Could not parse target_time {s!r}") from exc
    raise ValidationError(f"target_time must be like '4:30:00' or '4:30', got {s!r}")


def _goal_distance_km(distance: Any) -> float:
    if isinstance(distance, (int, float)):
        return float(distance)
    d = str(distance or "marathon").strip().lower()
    if "half" in d:
        return HALF_MARATHON_KM
    if "marathon" in d or d in ("42", "42.2", "42k"):
        return MARATHON_KM
    m = re.match(r"^(\d+(?:\.\d+)?)\s*km$", d)
    if m:
        return float(m.group(1))
    raise ValidationError(f"Unknown goal distance: {distance!r}")


def validate_runner_snapshot(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValidationError("Input must be a dict")

    history = raw.get("history")
    if history is None:
        history = []
    if not isinstance(history, list):
        raise ValidationError("history must be a list")
    for i, row in enumerate(history):
        if not isinstance(row, dict):
            raise ValidationError(f"history[{i}] must be a dict")

    age = raw.get("age")
    if age is None:
        raise ValidationError("age is required")
    age_f = float(age)
    if not 16 <= age_f <= 80:
        raise ValidationError("age must be between 16 and 80")

    experience = str(raw.get("experience_level", "beginner")).strip().lower()
    if experience not in EXPERIENCE_LEVELS:
        raise ValidationError(
            f"experience_level must be one of {EXPERIENCE_LEVELS}, got {experience!r}"
        )

    goal = raw.get("goal_race")
    if not isinstance(goal, dict):
        raise ValidationError("goal_race must be a dict")

    gdist = _goal_distance_km(goal.get("distance", "marathon"))
    target_raw = goal.get("target_time")
    if target_raw is None:
        goal_minutes = 270.0
    else:
        goal_minutes = _parse_time_to_minutes(str(target_raw))

    race_terrain = str(goal.get("terrain", "road")).strip().lower()
    if race_terrain not in ("road", "trail", "mixed"):
        race_terrain = "road"

    days_to_race = raw.get("days_to_race", 56)
    try:
        days_to_race_f = float(days_to_race)
    except (TypeError, ValueError) as exc:
        raise ValidationError("days_to_race must be a number") from exc
    if not 1 <= days_to_race_f <= 400:
        raise ValidationError("days_to_race must be between 1 and 400")

    adherence = raw.get("adherence_percent", 85.0)
    try:
        adherence_f = float(adherence)
    except (TypeError, ValueError) as exc:
        raise ValidationError("adherence_percent must be a number") from exc
    adherence_f = max(0.0, min(100.0, adherence_f))

    return {
        "history": history,
        "age": age_f,
        "experience_level": experience,
        "goal_distance_km": gdist,
        "goal_time_minutes": goal_minutes,
        "race_terrain": race_terrain,
        "days_to_race": days_to_race_f,
        "adherence_percent": adherence_f,
    }