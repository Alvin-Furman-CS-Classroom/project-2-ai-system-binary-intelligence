"""
Race readiness and finish-time prediction (Module 6).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .constants import DEFAULT_MODULE6_DATA_DIR, EXPERIENCE_LEVELS, FEATURE_COLUMNS
from .feature_builder import aggregate_history
from .input_validation import validate_runner_snapshot
from .training import ensure_training_artifacts, load_models


def _minutes_to_hms(total_minutes: float) -> str:
    total_sec = int(round(float(total_minutes) * 60.0))
    total_sec = max(0, total_sec)
    h, rem = divmod(total_sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}"


def _terrain_encoding(race_terrain: str) -> float:
    return float(("road", "trail", "mixed").index(race_terrain))


def _feature_vector(validated: dict[str, Any]) -> np.ndarray:
    exp_enc = float(EXPERIENCE_LEVELS.index(validated["experience_level"]))
    agg = aggregate_history(
        validated["history"],
        days_to_race=int(validated["days_to_race"]),
        adherence_pct=validated["adherence_percent"],
    )
    row = {
        "age": validated["age"],
        "goal_time_minutes": validated["goal_time_minutes"],
        "goal_distance_km": validated["goal_distance_km"],
        "experience_encoded": exp_enc,
        "race_terrain_encoded": _terrain_encoding(validated["race_terrain"]),
        "weeks_of_training": agg["weeks_of_training"],
        "avg_weekly_miles_last_12w": agg["avg_weekly_miles_last_12w"],
        "peak_weekly_miles": agg["peak_weekly_miles"],
        "avg_training_pace_min_per_mile": agg["avg_training_pace_min_per_mile"],
        "longest_run_miles": agg["longest_run_miles"],
        "num_runs_20_plus": agg["num_runs_20_plus"],
        "pct_miles_road": agg["pct_miles_road"],
        "pct_miles_trail": agg["pct_miles_trail"],
        "pct_miles_track": agg["pct_miles_track"],
        "adherence_pct": agg["adherence_pct"],
        "days_to_race": agg["days_to_race"],
        "negative_sentiment_rate": agg["negative_sentiment_rate"],
    }
    return np.array([[row[c] for c in FEATURE_COLUMNS]], dtype=np.float64)


def _recommendations(validated: dict[str, Any], agg: dict[str, float]) -> list[str]:
    out: list[str] = []
    rt = validated["race_terrain"]
    if rt == "road" and agg["pct_miles_road"] < 45:
        out.append("Increase road running to better match a road race surface.")
    if rt == "trail" and agg["pct_miles_trail"] < 30:
        out.append("Add trail volume so leg strength and footing match race terrain.")
    if agg["longest_run_miles"] < 16:
        out.append("Build longest run toward 18-22 miles before taper (marathon).")
    if agg["peak_weekly_miles"] < 32:
        out.append("Gradually raise peak weekly mileage to support marathon endurance.")
    if agg["adherence_pct"] < 72:
        out.append("Improve consistency versus the plan; missed sessions reduce readiness.")
    if agg["negative_sentiment_rate"] > 0.35:
        out.append("Several tough sessions in a row; consider easier weeks and recovery.")
    if not out:
        out.append("Training metrics look broadly aligned with goal; maintain gradual progression.")
    return out


def predict_race_readiness(
    runner_snapshot: dict[str, Any],
    *,
    module6_dir: str | Path | None = None,
    auto_train: bool = True,
) -> dict[str, Any]:
    """
    Predict marathon (or half) readiness and finish time from history + demographics.

    Parameters
    ----------
    runner_snapshot
        ``history``: list of run dicts (distance, pace or pace_minutes,
        terrain, optional date, sentiment).
        ``age``: int/float.
        ``goal_race``: distance (e.g. "marathon"), target_time ("4:30:00"),
        terrain (road | trail | mixed).
        Optional: experience_level, days_to_race, adherence_percent.
    module6_dir
        Folder with synthetic_race_training.csv and module6_models.pkl.
    auto_train
        If True and artifacts are missing, generates synthetic data and trains.
    """
    validated = validate_runner_snapshot(runner_snapshot)
    base = Path(module6_dir or DEFAULT_MODULE6_DATA_DIR)
    if auto_train:
        ensure_training_artifacts(base)

    bundle = load_models(base)
    finish_model = bundle["finish"]
    ready_model = bundle["readiness"]
    scaler = bundle["scaler"]
    meta = bundle["metadata"]

    # Use test-set residual std for honest confidence intervals
    resid = float(meta.get("residual_std_minutes", 12.0))

    X_raw = _feature_vector(validated)
    X_scaled = scaler.transform(X_raw)

    pred_min = float(finish_model.predict(X_scaled)[0])
    pred_min = max(120.0, min(480.0, pred_min))

    lo = max(120.0, pred_min - 1.96 * resid)
    hi = min(480.0, pred_min + 1.96 * resid)

    proba = ready_model.predict_proba(X_scaled)[0]
    readiness_score = float(proba[1])

    agg = aggregate_history(
        validated["history"],
        days_to_race=int(validated["days_to_race"]),
        adherence_pct=validated["adherence_percent"],
    )
    recs = _recommendations(validated, agg)

    return {
        "predicted_finish": _minutes_to_hms(pred_min),
        "predicted_finish_minutes": round(pred_min, 2),
        "confidence_interval": [_minutes_to_hms(lo), _minutes_to_hms(hi)],
        "confidence_interval_minutes": [round(lo, 2), round(hi, 2)],
        "readiness_score": round(readiness_score, 4),
        "recommendations": recs,
    }


__all__ = ["predict_race_readiness"]