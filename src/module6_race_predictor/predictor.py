"""
Race readiness and finish-time prediction (Module 6).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .constants import DEFAULT_MODULE6_DATA_DIR, EXPERIENCE_LEVELS, FEATURE_COLUMNS, MARATHON_KM
from .feature_builder import aggregate_history
from .input_validation import validate_runner_snapshot
from .training import ensure_training_artifacts, load_models

# Helper functions for predictor logic, e.g. feature vector construction, recommendations,
def _minutes_to_hms(total_minutes: float) -> str:
    total_sec = int(round(float(total_minutes) * 60.0))
    total_sec = max(0, total_sec)
    h, rem = divmod(total_sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}"

# Main predictor function: predict_race_readiness
def _terrain_encoding(race_terrain: str) -> float:
    return float(("road", "trail", "mixed").index(race_terrain))

# feature_vector: convert validated input into numeric feature vector for model input
def _feature_vector(validated: dict[str, Any]) -> np.ndarray:
    exp_enc = float(EXPERIENCE_LEVELS.index(validated["experience_level"]))
    agg = aggregate_history(
        validated["history"],
        days_to_race=int(validated["days_to_race"]),
        adherence_pct=validated["adherence_percent"],
    )
    row = {
        "age": validated["age"],
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

# Distance thresholds for recommendations
_LONG_RUN_TARGETS = {
    "5k":           (3.5,  5.0,  "4-5 miles"),
    "10k":          (5.0,  8.0,  "6-8 miles"),
    "half_marathon":(10.0, 13.0, "10-13 miles"),
    "marathon":     (16.0, 22.0, "18-22 miles"),
}
_PEAK_WEEKLY_TARGETS = {
    "5k":           15,
    "10k":          22,
    "half_marathon": 30,
    "marathon":     40,
}

def _dist_label(gdist_km: float) -> str:
    if gdist_km <= 6:    return "5k"
    if gdist_km <= 12:   return "10k"
    if gdist_km <= 25:   return "half_marathon"
    return "marathon"


def _readiness_penalty(validated: dict[str, Any], agg: dict[str, float]) -> float:
    """
    Rule-based multiplier (0–1) applied on top of the ML score.
    Prevents the model from giving high readiness to runners who are missing
    critical training milestones that the synthetic data doesn't fully capture
    (e.g. a beginner with no 20-mile runs attempting a marathon).
    """
    gdist = validated["goal_distance_km"]
    label = _dist_label(gdist)
    penalty = 1.0

    # Long-run deficit
    min_lr, _, _ = _LONG_RUN_TARGETS[label]
    lr = agg["longest_run_miles"]
    if lr < min_lr * 0.60:
        penalty *= 0.65   # very under-done
    elif lr < min_lr * 0.80:
        penalty *= 0.80
    elif lr < min_lr:
        penalty *= 0.90

    # Volume deficit
    min_pw = _PEAK_WEEKLY_TARGETS[label]
    if agg["peak_weekly_miles"] < min_pw * 0.50:
        penalty *= 0.75
    elif agg["peak_weekly_miles"] < min_pw * 0.70:
        penalty *= 0.88

    # Adherence
    adh = agg["adherence_pct"]
    if adh < 60:
        penalty *= 0.75
    elif adh < 72:
        penalty *= 0.88

    # Sustained negative sentiment
    if agg["negative_sentiment_rate"] > 0.45:
        penalty *= 0.88

    return penalty


def _recommendations(validated: dict[str, Any], agg: dict[str, float]) -> list[str]:
    out: list[str] = []
    rt = validated["race_terrain"]
    gdist = validated["goal_distance_km"]
    label = _dist_label(gdist)

    # Terrain match
    if rt == "road" and agg["pct_miles_road"] < 45:
        out.append("Increase road running to better match your race surface.")
    if rt == "trail" and agg["pct_miles_trail"] < 30:
        out.append("Add trail volume so leg strength and footing match race terrain.")

    # Long-run check (distance-specific)
    min_lr, _, target_str = _LONG_RUN_TARGETS[label]
    if agg["longest_run_miles"] < min_lr:
        out.append(f"Build your longest run toward {target_str} before taper.")

    # Weekly mileage (distance-specific)
    min_pw = _PEAK_WEEKLY_TARGETS[label]
    if agg["peak_weekly_miles"] < min_pw * 0.75:
        out.append(f"Gradually raise peak weekly mileage toward {min_pw} miles to support race endurance.")

    # Adherence
    if agg["adherence_pct"] < 72:
        out.append("Improve consistency versus the plan; missed sessions reduce readiness.")

    # Sentiment
    if agg["negative_sentiment_rate"] > 0.35:
        out.append("Several tough sessions recently; consider an easier week and extra recovery.")

    if not out:
        out.append("Training metrics look broadly aligned with your goal; maintain gradual progression.")
    return out

#Predict race readiness based on input snapshot, using trained models and returning predictions + recommendations
def predict_race_readiness( runner_snapshot: dict[str, Any],*, module6_dir: str | Path | None = None, auto_train: bool = True,) -> dict[str, Any]:
 
    #runner snapshot: runner's training history, demographics, and goal
    validated = validate_runner_snapshot(runner_snapshot)
    """
    {
        "history": history,
        "age": age_f,
        "experience_level": experience,
        "goal_distance_km": gdist,
        "goal_time_minutes": goal_minutes,
        "race_terrain": race_terrain,
        "days_to_race": days_to_race_f,
        "adherence_percent": adherence_f,
    }
    """
    #get model artifacts, load models, and prepare feature vector
    base = Path(module6_dir or DEFAULT_MODULE6_DATA_DIR)
    if auto_train:
        ensure_training_artifacts(base)

    bundle = load_models(base)
    finish_model = bundle["finish"]
    ready_model = bundle["readiness"]
    scaler = bundle["scaler"]
    meta = bundle["metadata"]

    # Use test-set residual std for honest confidence intervals.
    # Scale it by distance_factor so short-race CIs are appropriately narrow.
    gdist = validated["goal_distance_km"]
    distance_factor = gdist / MARATHON_KM
    resid_base = float(meta.get("residual_std_minutes", 12.0))
    resid = resid_base * distance_factor

    X_raw = _feature_vector(validated)
    X_scaled = scaler.transform(X_raw)

    pred_min = float(finish_model.predict(X_scaled)[0])

    # Clip to physically plausible range for this distance.
    clip_lo = max(10.0, gdist * 2.5)
    clip_hi = max(clip_lo + 30.0, gdist * 12.0)
    pred_min = max(clip_lo, min(clip_hi, pred_min))

    lo = max(clip_lo, pred_min - 1.96 * resid)
    hi = min(clip_hi, pred_min + 1.96 * resid)

    proba = ready_model.predict_proba(X_scaled)[0]
    readiness_score = float(proba[1])

    agg = aggregate_history(
        validated["history"],
        days_to_race=int(validated["days_to_race"]),
        adherence_pct=validated["adherence_percent"],
    )

    # Apply rule-based penalty for missed training milestones that the ML
    # model can't fully capture from the synthetic data alone.
    readiness_score = readiness_score * _readiness_penalty(validated, agg)

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