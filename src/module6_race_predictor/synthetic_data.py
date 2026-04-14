"""
Generate synthetic tabular data for training the race predictor.

Label formula calibrated against real marathon data (data/CalibrationData.csv, 86 runners).
Real data linear regression yielded:
  theta_1 (weekly_miles):      -2.82 min per mile/week
  theta_2 (pace_min_per_mile): +11.36 min per min/mile unit
  RMSE on real data: 14.76 min

Calibrated values (scaled by 0.65 for broader synthetic population):
  weekly_miles coeff:      -1.835  (was -0.35 avg + -1.15 peak, both kept but reweighted)
  pace_min_per_mile coeff: +7.383  (new term — not modeled in original formula)

avg_training_pace_min_per_mile is stored as a column and fed to the learner so
the supervised model sees the same signal used in the finish-time label.
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
    SYNTHETIC_ADHERENCE_CLIP,
    SYNTHETIC_ADHERENCE_MEAN,
    SYNTHETIC_ADHERENCE_STD,
    SYNTHETIC_AGE_RANGE,
    SYNTHETIC_AVG_TO_PEAK_RANGE,
    SYNTHETIC_DAYS_TO_RACE_RANGE,
    SYNTHETIC_EXPERIENCE_FINISH_OFFSET_ADVANCED,
    SYNTHETIC_EXPERIENCE_FINISH_OFFSET_BEGINNER,
    SYNTHETIC_EXPERIENCE_WEIGHTS,
    SYNTHETIC_FINISH_CLIP_MIN_MAX,
    SYNTHETIC_FINISH_COEFF_AGE,
    SYNTHETIC_FINISH_COEFF_AVG_WEEKLY,
    SYNTHETIC_FINISH_COEFF_GOAL_TIME,
    SYNTHETIC_FINISH_COEFF_INTERCEPT,
    SYNTHETIC_FINISH_COEFF_LONGEST_RUN,
    SYNTHETIC_FINISH_COEFF_NUM_20,
    SYNTHETIC_FINISH_COEFF_PACE,
    SYNTHETIC_FINISH_COEFF_PEAK_WEEKLY,
    SYNTHETIC_FINISH_NOISE_STD,
    SYNTHETIC_GOAL_TIME_MINUTES_RANGE,
    SYNTHETIC_LONGEST_RUN_CAP_MILES,
    SYNTHETIC_LONGEST_RUN_PEAK_FRAC,
    SYNTHETIC_MET_GOAL_LABEL_FLIP_PROB,
    SYNTHETIC_MET_GOAL_SLACK_RANGE,
    SYNTHETIC_NEG_SENTIMENT_BETA_AB,
    SYNTHETIC_NEG_SENTIMENT_CLIP,
    SYNTHETIC_NUM_LONG_RUNS_20_RANGE,
    SYNTHETIC_PACE_ADVANCED_OFFSET,
    SYNTHETIC_PACE_BASE_INTERCEPT,
    SYNTHETIC_PACE_BEGINNER_OFFSET,
    SYNTHETIC_PACE_CLIP_MIN_MAX,
    SYNTHETIC_PACE_NOISE_STD,
    SYNTHETIC_PACE_PER_PEAK_MILE,
    SYNTHETIC_PEAK_WEEKLY_RANGE,
    SYNTHETIC_TERRAIN_WEIGHTS,
    SYNTHETIC_TRACK_CAP,
    SYNTHETIC_TRAIL_BASE_RANGE_OTHER,
    SYNTHETIC_TRAIL_BASE_RANGE_TRAIL,
    SYNTHETIC_TRAIL_JITTER_SIGMA,
    SYNTHETIC_WEEKS_OF_TRAINING_RANGE,
)


def _encode_experience(rng: np.random.Generator) -> tuple[str, int]:
    level = rng.choice(EXPERIENCE_LEVELS, p=SYNTHETIC_EXPERIENCE_WEIGHTS)
    return level, EXPERIENCE_LEVELS.index(level)


def _encode_race_terrain(rng: np.random.Generator) -> tuple[str, int]:
    opts = ("road", "trail", "mixed")
    t = rng.choice(opts, p=SYNTHETIC_TERRAIN_WEIGHTS)
    return t, opts.index(t)


def _simulate_avg_pace(
    rng: np.random.Generator,
    peak_weekly: float,
    exp_enc: int,
) -> float:
    """
    Simulate a plausible average training pace (min/mile).
    Higher volume runners tend to be faster. Real data mean was 8.1 min/mile.
    Extended upward for slower recreational runners in the synthetic population.
    """
    base_pace = SYNTHETIC_PACE_BASE_INTERCEPT + SYNTHETIC_PACE_PER_PEAK_MILE * peak_weekly
    if exp_enc == 0:
        base_pace += SYNTHETIC_PACE_BEGINNER_OFFSET
    elif exp_enc == 2:
        base_pace += SYNTHETIC_PACE_ADVANCED_OFFSET
    lo, hi = SYNTHETIC_PACE_CLIP_MIN_MAX
    return round(
        float(np.clip(rng.normal(base_pace, SYNTHETIC_PACE_NOISE_STD), lo, hi)),
        3,
    )


def generate_row(rng: np.random.Generator) -> dict[str, float]:
    age = float(rng.integers(SYNTHETIC_AGE_RANGE[0], SYNTHETIC_AGE_RANGE[1]))
    goal_distance_km = MARATHON_KM
    g_lo, g_hi = SYNTHETIC_GOAL_TIME_MINUTES_RANGE
    goal_time_minutes = float(rng.integers(g_lo, g_hi))
    _, exp_enc = _encode_experience(rng)
    rt_name, rt_enc = _encode_race_terrain(rng)

    w_lo, w_hi = SYNTHETIC_WEEKS_OF_TRAINING_RANGE
    weeks_of_training = float(rng.integers(w_lo, w_hi))
    p_lo, p_hi = SYNTHETIC_PEAK_WEEKLY_RANGE
    peak_weekly = rng.uniform(p_lo, p_hi)
    a_lo, a_hi = SYNTHETIC_AVG_TO_PEAK_RANGE
    avg_weekly = peak_weekly * rng.uniform(a_lo, a_hi)
    cap = min(peak_weekly * SYNTHETIC_LONGEST_RUN_PEAK_FRAC, SYNTHETIC_LONGEST_RUN_CAP_MILES)
    longest_run = rng.uniform(6, cap)
    n20_lo, n20_hi = SYNTHETIC_NUM_LONG_RUNS_20_RANGE
    num_20 = float(rng.integers(n20_lo, n20_hi))

    if rt_name == "trail":
        t_lo, t_hi = SYNTHETIC_TRAIL_BASE_RANGE_TRAIL
        base_trail = rng.uniform(t_lo, t_hi)
    else:
        o_lo, o_hi = SYNTHETIC_TRAIL_BASE_RANGE_OTHER
        base_trail = rng.uniform(o_lo, o_hi)
    pct_trail = float(
        np.clip(base_trail + rng.normal(0, SYNTHETIC_TRAIL_JITTER_SIGMA), 0, 85)
    )
    pct_track = float(np.clip(rng.uniform(0, SYNTHETIC_TRACK_CAP), 0, 100 - pct_trail))
    pct_road = float(max(0.0, 100.0 - pct_trail - pct_track))

    ad_lo, ad_hi = SYNTHETIC_ADHERENCE_CLIP
    adherence_pct = float(np.clip(rng.normal(SYNTHETIC_ADHERENCE_MEAN, SYNTHETIC_ADHERENCE_STD), ad_lo, ad_hi))
    d_lo, d_hi = SYNTHETIC_DAYS_TO_RACE_RANGE
    days_to_race = float(rng.integers(d_lo, d_hi))
    ba, bb = SYNTHETIC_NEG_SENTIMENT_BETA_AB
    n_lo, n_hi = SYNTHETIC_NEG_SENTIMENT_CLIP
    neg_rate = float(np.clip(rng.beta(ba, bb), n_lo, n_hi))

    avg_pace_min_per_mile = _simulate_avg_pace(rng, peak_weekly, exp_enc)

    base = (
        SYNTHETIC_FINISH_COEFF_INTERCEPT
        + SYNTHETIC_FINISH_COEFF_AGE * age
        + SYNTHETIC_FINISH_COEFF_AVG_WEEKLY * avg_weekly
        + SYNTHETIC_FINISH_COEFF_PEAK_WEEKLY * peak_weekly
        + SYNTHETIC_FINISH_COEFF_LONGEST_RUN * longest_run
        + SYNTHETIC_FINISH_COEFF_NUM_20 * num_20
        + SYNTHETIC_FINISH_COEFF_GOAL_TIME * goal_time_minutes
        + SYNTHETIC_FINISH_COEFF_PACE * avg_pace_min_per_mile
    )
    if exp_enc == 0:
        base += SYNTHETIC_EXPERIENCE_FINISH_OFFSET_BEGINNER
    elif exp_enc == 2:
        base += SYNTHETIC_EXPERIENCE_FINISH_OFFSET_ADVANCED

    noise = float(rng.normal(0, SYNTHETIC_FINISH_NOISE_STD))
    f_lo, f_hi = SYNTHETIC_FINISH_CLIP_MIN_MAX
    actual_finish = float(np.clip(base + noise, f_lo, f_hi))

    s_lo, s_hi = SYNTHETIC_MET_GOAL_SLACK_RANGE
    slack = rng.uniform(s_lo, s_hi)
    met_goal = 1.0 if actual_finish <= goal_time_minutes * slack else 0.0
    if rng.random() < SYNTHETIC_MET_GOAL_LABEL_FLIP_PROB:
        met_goal = 1.0 - met_goal

    return {
        "age": age,
        "goal_time_minutes": goal_time_minutes,
        "goal_distance_km": goal_distance_km,
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
            f"met_goal=1: {met:.0f} ({100*met/n_rows:.1f}%) | "
            f"met_goal=0: {n_rows-met:.0f} ({100*(n_rows-met)/n_rows:.1f}%) | "
            f"finish mean={sum(times)/len(times):.1f} min"
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
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in CSV_COLUMNS})
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
        np.asarray(y_time),
        np.asarray(y_goal),
    )