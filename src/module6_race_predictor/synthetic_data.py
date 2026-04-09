"""
Generate synthetic tabular data for training the race predictor.

Labels follow a simple physiological story: more volume, longer long runs, and
younger age → faster times; logistic noise for met_goal.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .constants import (
    CSV_COLUMNS,
    EXPERIENCE_LEVELS,
    FEATURE_COLUMNS,
    MARATHON_KM,
)


def _encode_experience(rng: np.random.Generator) -> tuple[str, int]:
    level = rng.choice(EXPERIENCE_LEVELS, p=[0.5, 0.35, 0.15])
    return level, EXPERIENCE_LEVELS.index(level)


def _encode_race_terrain(rng: np.random.Generator) -> tuple[str, int]:
    opts = ("road", "trail", "mixed")
    t = rng.choice(opts, p=[0.7, 0.15, 0.15])
    return t, opts.index(t)


def generate_row(rng: np.random.Generator) -> dict[str, float]:
    age = float(rng.integers(22, 56))
    goal_distance_km = MARATHON_KM
    goal_time_minutes = float(rng.integers(210, 361))  # 3:30 – 6:00 marathon goal
    _, exp_enc = _encode_experience(rng)
    rt_name, rt_enc = _encode_race_terrain(rng)

    weeks_of_training = float(rng.integers(8, 25))
    peak_weekly = rng.uniform(15, 55)
    avg_weekly = peak_weekly * rng.uniform(0.55, 0.95)
    longest_run = rng.uniform(6, min(peak_weekly * 0.55, 24))
    num_20 = float(rng.integers(0, 5))

    # Terrain mix in training (correlate a bit with race terrain)
    if rt_name == "trail":
        base_trail = rng.uniform(25, 60)
    else:
        base_trail = rng.uniform(5, 35)
    pct_trail = float(np.clip(base_trail + rng.normal(0, 8), 0, 85))
    pct_track = float(np.clip(rng.uniform(0, 25), 0, 100 - pct_trail))
    pct_road = float(max(0.0, 100.0 - pct_trail - pct_track))

    adherence_pct = float(np.clip(rng.normal(82, 12), 40, 100))
    days_to_race = float(rng.integers(21, 91))
    neg_rate = float(np.clip(rng.beta(2, 8), 0, 0.6))

    # --- Synthetic finish time (minutes): linear-ish + interaction noise ---
    base = (
        310.0
        + 0.55 * age
        - 1.15 * peak_weekly
        - 2.4 * longest_run
        - 4.0 * num_20
        - 0.35 * avg_weekly
        + 0.12 * goal_time_minutes
    )
    if exp_enc == 0:
        base += 8.0
    elif exp_enc == 2:
        base -= 6.0
    noise = float(rng.normal(0, 14))
    actual_finish = float(np.clip(base + noise, 145, 420))

    # Met goal: finished at or under goal + small slack
    slack = rng.uniform(1.03, 1.12)
    met_goal = 1.0 if actual_finish <= goal_time_minutes * slack else 0.0
    # Occasionally flip label for realism (missed despite good stats)
    if rng.random() < 0.04:
        met_goal = 1.0 - met_goal

    row = {
        "age": age,
        "goal_time_minutes": goal_time_minutes,
        "goal_distance_km": goal_distance_km,
        "experience_encoded": float(exp_enc),
        "race_terrain_encoded": float(rt_enc),
        "weeks_of_training": weeks_of_training,
        "avg_weekly_miles_last_12w": round(avg_weekly, 2),
        "peak_weekly_miles": round(peak_weekly, 2),
        "longest_run_miles": round(longest_run, 2),
        "num_runs_20_plus": num_20,
        "pct_miles_road": round(pct_road, 2),
        "pct_miles_trail": round(pct_trail, 2),
        "pct_miles_track": round(pct_track, 2),
        "adherence_pct": round(adherence_pct, 2),
        "days_to_race": days_to_race,
        "negative_sentiment_rate": round(neg_rate, 4),
        "actual_finish_time_minutes": round(actual_finish, 2),
        "met_goal": met_goal,
    }
    return row


def generate_dataset(
    n_rows: int = 1200,
    *,
    seed: int | None = 42,
) -> list[dict[str, float]]:
    rng = np.random.default_rng(seed)
    return [generate_row(rng) for _ in range(n_rows)]


def write_synthetic_csv(path: str | Path, n_rows: int = 1200, *, seed: int | None = 42) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_dataset(n_rows, seed=seed)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in CSV_COLUMNS})
    return path


def load_synthetic_csv(path: str | Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return X (n, n_features), y_time, y_met_goal."""
    path = Path(path)
    rows: list[list[float]] = []
    y_time: list[float] = []
    y_goal: list[float] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line in reader:
            feats = [float(line[c]) for c in FEATURE_COLUMNS]
            rows.append(feats)
            y_time.append(float(line["actual_finish_time_minutes"]))
            y_goal.append(float(line["met_goal"]))
    return np.asarray(rows, dtype=np.float64), np.asarray(y_time), np.asarray(y_goal)
