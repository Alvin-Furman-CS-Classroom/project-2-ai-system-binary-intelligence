"""
Generate synthetic tabular data for training the race predictor.

This version supports multiple race distances:
- 5K
- 10K
- Half marathon
- Marathon

The generated training features and labels are distance-aware so the model
does not learn marathon-only behavior.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

try:
    from .constants import (
        CSV_COLUMNS,
        EXPERIENCE_LEVELS,
        FEATURE_COLUMNS,
        HALF_MARATHON_KM,
        MARATHON_KM,
        SYNTHETIC_ADHERENCE_CLIP,
        SYNTHETIC_ADHERENCE_MEAN,
        SYNTHETIC_ADHERENCE_STD,
        SYNTHETIC_AGE_RANGE,
        SYNTHETIC_DAYS_TO_RACE_RANGE,
        SYNTHETIC_EXPERIENCE_FINISH_OFFSET_ADVANCED,
        SYNTHETIC_EXPERIENCE_FINISH_OFFSET_BEGINNER,
        SYNTHETIC_EXPERIENCE_WEIGHTS,
        SYNTHETIC_FINISH_COEFF_AGE,
        SYNTHETIC_FINISH_COEFF_AVG_WEEKLY,
        SYNTHETIC_FINISH_COEFF_INTERCEPT,
        SYNTHETIC_FINISH_COEFF_LONGEST_RUN,
        SYNTHETIC_FINISH_COEFF_NUM_20,
        SYNTHETIC_FINISH_COEFF_PACE,
        SYNTHETIC_FINISH_COEFF_PEAK_WEEKLY,
        SYNTHETIC_FINISH_NOISE_STD,
        SYNTHETIC_MET_GOAL_LABEL_FLIP_PROB,
        SYNTHETIC_MET_GOAL_SLACK_RANGE,
        SYNTHETIC_NEG_SENTIMENT_BETA_AB,
        SYNTHETIC_NEG_SENTIMENT_CLIP,
        SYNTHETIC_PACE_ADVANCED_OFFSET,
        SYNTHETIC_PACE_BASE_INTERCEPT,
        SYNTHETIC_PACE_BEGINNER_OFFSET,
        SYNTHETIC_PACE_CLIP_MIN_MAX,
        SYNTHETIC_PACE_NOISE_STD,
        SYNTHETIC_PACE_PER_PEAK_MILE,
        SYNTHETIC_TERRAIN_WEIGHTS,
        SYNTHETIC_TRACK_CAP,
        SYNTHETIC_TRAIL_BASE_RANGE_OTHER,
        SYNTHETIC_TRAIL_BASE_RANGE_TRAIL,
        SYNTHETIC_TRAIL_JITTER_SIGMA,
    )
except ImportError:
    from constants import (  # type: ignore[no-redef]
        CSV_COLUMNS,
        EXPERIENCE_LEVELS,
        FEATURE_COLUMNS,
        HALF_MARATHON_KM,
        MARATHON_KM,
        SYNTHETIC_ADHERENCE_CLIP,
        SYNTHETIC_ADHERENCE_MEAN,
        SYNTHETIC_ADHERENCE_STD,
        SYNTHETIC_AGE_RANGE,
        SYNTHETIC_DAYS_TO_RACE_RANGE,
        SYNTHETIC_EXPERIENCE_FINISH_OFFSET_ADVANCED,
        SYNTHETIC_EXPERIENCE_FINISH_OFFSET_BEGINNER,
        SYNTHETIC_EXPERIENCE_WEIGHTS,
        SYNTHETIC_FINISH_COEFF_AGE,
        SYNTHETIC_FINISH_COEFF_AVG_WEEKLY,
        SYNTHETIC_FINISH_COEFF_INTERCEPT,
        SYNTHETIC_FINISH_COEFF_LONGEST_RUN,
        SYNTHETIC_FINISH_COEFF_NUM_20,
        SYNTHETIC_FINISH_COEFF_PACE,
        SYNTHETIC_FINISH_COEFF_PEAK_WEEKLY,
        SYNTHETIC_FINISH_NOISE_STD,
        SYNTHETIC_MET_GOAL_LABEL_FLIP_PROB,
        SYNTHETIC_MET_GOAL_SLACK_RANGE,
        SYNTHETIC_NEG_SENTIMENT_BETA_AB,
        SYNTHETIC_NEG_SENTIMENT_CLIP,
        SYNTHETIC_PACE_ADVANCED_OFFSET,
        SYNTHETIC_PACE_BASE_INTERCEPT,
        SYNTHETIC_PACE_BEGINNER_OFFSET,
        SYNTHETIC_PACE_CLIP_MIN_MAX,
        SYNTHETIC_PACE_NOISE_STD,
        SYNTHETIC_PACE_PER_PEAK_MILE,
        SYNTHETIC_TERRAIN_WEIGHTS,
        SYNTHETIC_TRACK_CAP,
        SYNTHETIC_TRAIL_BASE_RANGE_OTHER,
        SYNTHETIC_TRAIL_BASE_RANGE_TRAIL,
        SYNTHETIC_TRAIL_JITTER_SIGMA,
    )

# ---------------------------------------------------------------------------
# Distance profiles
# ---------------------------------------------------------------------------

RACE_DISTANCES_KM: dict[str, float] = {
    "5k": 5.0,
    "10k": 10.0,
    "half_marathon": HALF_MARATHON_KM,
    "marathon": MARATHON_KM,
}

RACE_DISTANCE_WEIGHTS: dict[str, float] = {
    "5k": 0.22,
    "10k": 0.25,
    "half_marathon": 0.30,
    "marathon": 0.23,
}

# Goal time ranges in minutes for each race type
GOAL_TIME_RANGES: dict[str, tuple[int, int]] = {
    "5k": (18, 45),
    "10k": (38, 95),
    "half_marathon": (95, 210),
    "marathon": (180, 420),
}

# Training profile by race type
DISTANCE_PROFILES: dict[str, dict[str, tuple[float, float]]] = {
    "5k": {
        "weeks": (6, 14),
        "peak_weekly": (10, 30),
        "avg_to_peak": (0.60, 0.88),
        "longest_run": (4, 9),
        "num_20": (0, 1),
    },
    "10k": {
        "weeks": (8, 16),
        "peak_weekly": (15, 38),
        "avg_to_peak": (0.62, 0.90),
        "longest_run": (6, 12),
        "num_20": (0, 1),
    },
    "half_marathon": {
        "weeks": (10, 20),
        "peak_weekly": (20, 50),
        "avg_to_peak": (0.66, 0.92),
        "longest_run": (8, 16),
        "num_20": (0, 1),
    },
    "marathon": {
        "weeks": (12, 24),
        "peak_weekly": (28, 70),
        "avg_to_peak": (0.68, 0.93),
        "longest_run": (12, 22),
        "num_20": (0, 4),
    },
}

# Pace adjustments by race type (min/mile offsets)
# Negative = faster
DISTANCE_PACE_OFFSETS: dict[str, float] = {
    "5k": -0.80,
    "10k": -0.50,
    "half_marathon": 0.00,
    "marathon": 0.40,
}

# Terrain effect on finish time, in minutes
TERRAIN_FINISH_OFFSETS: dict[str, float] = {
    "road": 0.0,
    "mixed": 6.0,
    "trail": 18.0,
}


def _encode_experience(rng: np.random.Generator) -> tuple[str, int]:
    level = rng.choice(EXPERIENCE_LEVELS, p=SYNTHETIC_EXPERIENCE_WEIGHTS)
    return level, EXPERIENCE_LEVELS.index(level)


def _encode_race_terrain(rng: np.random.Generator) -> tuple[str, int]:
    opts = ("road", "trail", "mixed")
    t = rng.choice(opts, p=SYNTHETIC_TERRAIN_WEIGHTS)
    return t, opts.index(t)


def _sample_race_distance(rng: np.random.Generator) -> tuple[str, float]:
    race_names = tuple(RACE_DISTANCES_KM.keys())
    probs = np.array([RACE_DISTANCE_WEIGHTS[n] for n in race_names], dtype=float)
    probs = probs / probs.sum()
    race_name = rng.choice(race_names, p=probs)
    return race_name, float(RACE_DISTANCES_KM[race_name])


def _simulate_avg_pace(
    rng: np.random.Generator,
    peak_weekly: float,
    exp_enc: int,
    race_name: str,
) -> float:
    """
    Simulate a plausible average training pace (min/mile).

    Higher volume runners tend to be faster.
    Shorter-race specialists also tend to train at faster average paces.
    """
    base_pace = SYNTHETIC_PACE_BASE_INTERCEPT + SYNTHETIC_PACE_PER_PEAK_MILE * peak_weekly
    base_pace += DISTANCE_PACE_OFFSETS[race_name]

    if exp_enc == 0:
        base_pace += SYNTHETIC_PACE_BEGINNER_OFFSET
    elif exp_enc == 2:
        base_pace += SYNTHETIC_PACE_ADVANCED_OFFSET

    lo, hi = SYNTHETIC_PACE_CLIP_MIN_MAX
    pace = float(np.clip(rng.normal(base_pace, SYNTHETIC_PACE_NOISE_STD), lo, hi))
    return round(pace, 3)


def generate_row(rng: np.random.Generator) -> dict[str, float]:
    age = float(rng.integers(SYNTHETIC_AGE_RANGE[0], SYNTHETIC_AGE_RANGE[1]))
    race_name, goal_distance_km = _sample_race_distance(rng)

    g_lo, g_hi = GOAL_TIME_RANGES[race_name]
    goal_time_minutes = float(rng.integers(g_lo, g_hi + 1))

    _, exp_enc = _encode_experience(rng)
    rt_name, rt_enc = _encode_race_terrain(rng)

    profile = DISTANCE_PROFILES[race_name]

    w_lo, w_hi = profile["weeks"]
    weeks_of_training = float(rng.integers(int(w_lo), int(w_hi) + 1))

    p_lo, p_hi = profile["peak_weekly"]
    peak_weekly = float(rng.uniform(p_lo, p_hi))

    a_lo, a_hi = profile["avg_to_peak"]
    avg_weekly = float(peak_weekly * rng.uniform(a_lo, a_hi))

    l_lo, l_hi = profile["longest_run"]
    longest_run = float(rng.uniform(l_lo, l_hi))

    n20_lo, n20_hi = profile["num_20"]
    num_20 = float(rng.integers(int(n20_lo), int(n20_hi) + 1))
    if goal_distance_km < 30.0:
        num_20 = 0.0

    if rt_name == "trail":
        t_lo, t_hi = SYNTHETIC_TRAIL_BASE_RANGE_TRAIL
        base_trail = rng.uniform(t_lo, t_hi)
    else:
        o_lo, o_hi = SYNTHETIC_TRAIL_BASE_RANGE_OTHER
        base_trail = rng.uniform(o_lo, o_hi)

    pct_trail = float(np.clip(base_trail + rng.normal(0, SYNTHETIC_TRAIL_JITTER_SIGMA), 0, 85))
    pct_track = float(np.clip(rng.uniform(0, SYNTHETIC_TRACK_CAP), 0, 100 - pct_trail))
    pct_road = float(max(0.0, 100.0 - pct_trail - pct_track))

    ad_lo, ad_hi = SYNTHETIC_ADHERENCE_CLIP
    adherence_pct = float(
        np.clip(rng.normal(SYNTHETIC_ADHERENCE_MEAN, SYNTHETIC_ADHERENCE_STD), ad_lo, ad_hi)
    )

    d_lo, d_hi = SYNTHETIC_DAYS_TO_RACE_RANGE
    days_to_race = float(rng.integers(d_lo, d_hi + 1))

    ba, bb = SYNTHETIC_NEG_SENTIMENT_BETA_AB
    n_lo, n_hi = SYNTHETIC_NEG_SENTIMENT_CLIP
    neg_rate = float(np.clip(rng.beta(ba, bb), n_lo, n_hi))

    avg_pace_min_per_mile = _simulate_avg_pace(rng, peak_weekly, exp_enc, race_name)

    # Distance factor relative to marathon (5K ≈ 0.12, half ≈ 0.50, marathon = 1.0)
    distance_factor = goal_distance_km / MARATHON_KM

    # Longer races depend more on endurance features.
    endurance_weight = 0.50 + 0.90 * distance_factor

    # Step 1: compute marathon-scale quality estimate from training features.
    marathon_base = (
        SYNTHETIC_FINISH_COEFF_INTERCEPT
        + SYNTHETIC_FINISH_COEFF_AGE * age
        + (SYNTHETIC_FINISH_COEFF_AVG_WEEKLY * endurance_weight) * avg_weekly
        + (SYNTHETIC_FINISH_COEFF_PEAK_WEEKLY * endurance_weight) * peak_weekly
        + (SYNTHETIC_FINISH_COEFF_LONGEST_RUN * endurance_weight) * longest_run
        + (SYNTHETIC_FINISH_COEFF_NUM_20 * endurance_weight) * num_20
        + SYNTHETIC_FINISH_COEFF_PACE * avg_pace_min_per_mile
    )

    if exp_enc == 0:
        marathon_base += SYNTHETIC_EXPERIENCE_FINISH_OFFSET_BEGINNER
    elif exp_enc == 2:
        marathon_base += SYNTHETIC_EXPERIENCE_FINISH_OFFSET_ADVANCED

    # Step 2: scale to actual race distance and add terrain offset.
    scaled_estimate = marathon_base * distance_factor + TERRAIN_FINISH_OFFSETS[rt_name]

    # Step 3: scale noise by distance so a 5K has ~1-2 min spread, marathon ~14 min.
    base = scaled_estimate
    noise = float(rng.normal(0, SYNTHETIC_FINISH_NOISE_STD * distance_factor))

    # Distance-appropriate clip: ~2.5 min/km fast end, ~12 min/km slow end.
    f_lo = max(10.0, goal_distance_km * 2.5)
    f_hi = max(f_lo + 10.0, goal_distance_km * 12.0)
    actual_finish = float(np.clip(base + noise, f_lo, f_hi))

    s_lo, s_hi = SYNTHETIC_MET_GOAL_SLACK_RANGE
    slack = float(rng.uniform(s_lo, s_hi))
    met_goal = 1.0 if actual_finish <= goal_time_minutes * slack else 0.0

    if rng.random() < SYNTHETIC_MET_GOAL_LABEL_FLIP_PROB:
        met_goal = 1.0 - met_goal

    return {
        "age": age,
        "goal_time_minutes": goal_time_minutes,
        "goal_distance_km": round(goal_distance_km, 4),
        "experience_encoded": float(exp_enc),
        "race_terrain_encoded": float(rt_enc),
        "weeks_of_training": weeks_of_training,
        "avg_weekly_miles_last_12w": round(avg_weekly, 2),
        "peak_weekly_miles": round(peak_weekly, 2),
        "avg_training_pace_min_per_mile": round(avg_pace_min_per_mile, 3),
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


def generate_dataset(
    n_rows: int = 2000,
    *,
    seed: int | None = 42,
    verbose: bool = True,
) -> list[dict[str, float]]:
    rng = np.random.default_rng(seed)
    rows = [generate_row(rng) for _ in range(n_rows)]

    if verbose:
        met = sum(r["met_goal"] for r in rows)
        times = [r["actual_finish_time_minutes"] for r in rows]
        print(
            f"[synthetic_data] Generated {n_rows} rows | "
            f"met_goal=1: {met:.0f} ({100 * met / n_rows:.1f}%) | "
            f"met_goal=0: {n_rows - met:.0f} ({100 * (n_rows - met) / n_rows:.1f}%) | "
            f"finish mean={sum(times) / len(times):.1f} min"
        )

    return rows


def write_synthetic_csv(
    path: str | Path,
    n_rows: int = 2000,
    *,
    seed: int | None = 42,
    verbose: bool = True,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = generate_dataset(n_rows, seed=seed, verbose=verbose)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in CSV_COLUMNS})

    return path


def load_synthetic_csv(
    path: str | Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    path = Path(path)

    rows: list[list[float]] = []
    y_time: list[float] = []
    y_goal: list[float] = []

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line in reader:
            rows.append([float(line[c]) for c in FEATURE_COLUMNS])
            y_time.append(float(line["actual_finish_time_minutes"]))
            y_goal.append(float(line["met_goal"]))

    return (
        np.asarray(rows, dtype=np.float64),
        np.asarray(y_time, dtype=np.float64),
        np.asarray(y_goal, dtype=np.float64),
    )


if __name__ == "__main__":
    import sys

    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "synthetic_training_data.csv"
    write_synthetic_csv(out)
    print(f"Saved to {out}")