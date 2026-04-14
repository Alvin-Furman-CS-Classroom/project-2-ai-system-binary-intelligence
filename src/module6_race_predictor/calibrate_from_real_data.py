"""
Utility: calibrate the Module 6 synthetic finish-time formula using real runners.

We use 86 actual marathon runners (``data/CalibrationData.csv``). Each row has
kilometers run in the four weeks before the race (``km4week``), average
training speed in that window (``sp4week``, km/h), and actual finish time.

Fitting linear regression on converted features (weekly miles, pace in min/mile)
recovers the real relationship between training and outcome: roughly **~2.8 minutes
faster per extra mile per week** of volume, and **pace as the strongest
predictor** (~11 minutes slower finish per 1 min/mile slower training pace).

That informed updates to ``src/module6_race_predictor/synthetic_data.py``
(stronger weekly terms and a simulated pace feature in the label). This script
is not imported by the module; it only documents the reasoning and writes JSON.

Usage
-----
From the repository root::

    python -m src.module6_race_predictor.calibrate_from_real_data
    python -m src.module6_race_predictor.calibrate_from_real_data --csv data/CalibrationData.csv

Outputs
-------
  Prints real coefficients, comparison to the current synthetic constants,
  and saves ``calibrated_coefficients.json`` next to the CSV (by default).
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CSV = _PROJECT_ROOT / "data" / "CalibrationData.csv"


# ---------------------------------------------------------------------------
# Unit conversions
# ---------------------------------------------------------------------------

def _km4week_to_weekly_miles(km4week: float) -> float:
    """Total km over 4 weeks -> average weekly miles."""
    return (km4week / 4.0) * 0.621371


def _sp4week_to_pace_min_per_mile(sp4week_kmh: float) -> float:
    """Average speed in km/h -> pace in minutes per mile."""
    return 60.0 / (sp4week_kmh * 0.621371)


def _marathon_hours_to_minutes(decimal_hours: float) -> float:
    return decimal_hours * 60.0


# ---------------------------------------------------------------------------
# Load and clean
# ---------------------------------------------------------------------------

def load_and_clean(csv_path: str | Path) -> list[dict]:
    """
    Load CalibrationData.csv (Kaggle Girardi-style columns) and return cleaned rows.

    Drops:
      - Rows missing km4week, sp4week, or MarathonTime
      - Obvious data-entry errors (sp4week > 20 km/h — one bad row in source)
    """
    path = Path(csv_path)
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                sp = float(r["sp4week"])
                km = float(r["km4week"])
                t = float(r["MarathonTime"])
            except (ValueError, KeyError):
                continue
            if sp > 20:
                continue  # clear outlier — single bad row (11125 km/h)
            rows.append(
                {
                    "weekly_miles": _km4week_to_weekly_miles(km),
                    "pace_min_per_mile": _sp4week_to_pace_min_per_mile(sp),
                    "finish_minutes": _marathon_hours_to_minutes(t),
                    "raw_km4week": km,
                    "raw_sp4week": sp,
                }
            )
    return rows


# ---------------------------------------------------------------------------
# Fit
# ---------------------------------------------------------------------------

def fit_real_coefficients(rows: list[dict]) -> dict:
    """
    Fit multivariate linear regression via the normal equation:
        theta* = (X^T X)^-1 X^T y

    Features: weekly_miles, pace_min_per_mile
    Target:   finish_minutes

    Returns a dict with theta_0 (intercept), theta_1 (weekly_miles),
    theta_2 (pace_min_per_mile), and evaluation metrics.
    """
    X = np.array(
        [[1.0, r["weekly_miles"], r["pace_min_per_mile"]] for r in rows],
        dtype=np.float64,
    )
    y = np.array([r["finish_minutes"] for r in rows], dtype=np.float64)

    # Normal equation: theta = (X^T X)^-1 X^T y
    theta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)

    preds = X @ theta
    residuals = y - preds
    rmse = float(np.sqrt(np.mean(residuals ** 2)))
    mae = float(np.mean(np.abs(residuals)))
    r2 = float(1 - np.sum(residuals ** 2) / np.sum((y - np.mean(y)) ** 2))

    return {
        "theta_0_intercept": float(theta[0]),
        "theta_1_weekly_miles": float(theta[1]),
        "theta_2_pace_min_per_mile": float(theta[2]),
        "rmse_minutes": rmse,
        "mae_minutes": mae,
        "r_squared": r2,
        "n_rows": len(rows),
    }


# ---------------------------------------------------------------------------
# Compare to synthetic formula
# ---------------------------------------------------------------------------

SYNTHETIC_FORMULA_NOTE = """
Current generate_row formula (synthetic_data.py) — calibrated from real data:

    base = (
        310.0
        + 0.55  * age
        - 0.90  * avg_weekly_miles
        - 0.935 * peak_weekly_miles
        + 7.383 * avg_training_pace_min_per_mile   # column in CSV / learner input
        - 2.4   * longest_run_miles
        - 4.0   * num_runs_20_plus
        + 0.12  * goal_time_minutes
    )
    + experience offset (+8 beginner, -6 advanced)
    + Normal(0, 14) noise

Weekly volume: two correlated features (avg + peak); combined effect was
strengthened toward the real single-feature mileage coefficient.
Pace: added (scaled ×0.65 for a broader synthetic population than the real cohort).
"""


def compare_and_suggest(real: dict) -> dict:
    """
    Derive scaled coefficients for a wider synthetic population than the real cohort.

    The real data skew fast (narrow finish-time range). We scale by 0.65 when
    suggesting pace/weekly terms for the full synthetic range.
    """
    real_weekly = real["theta_1_weekly_miles"]
    real_pace = real["theta_2_pace_min_per_mile"]

    scale = 0.65
    suggested_weekly = round(real_weekly * scale, 3)
    suggested_pace = round(real_pace * scale, 3)

    return {
        "suggested_avg_weekly_miles_coeff": suggested_weekly,
        "suggested_pace_min_per_mile_coeff": suggested_pace,
        "note": (
            "Scale factor 0.65: real data are mostly sub-4h runners; synthetic "
            "population is wider. Intercept 310.0 retained; pace term added in code."
        ),
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(real: dict, suggestion: dict, rows: list[dict]) -> None:
    wm = [r["weekly_miles"] for r in rows]
    pm = [r["pace_min_per_mile"] for r in rows]
    fm = [r["finish_minutes"] for r in rows]

    print("=" * 62)
    print("  MODULE 6 — REAL DATA CALIBRATION REPORT")
    print("=" * 62)
    print(f"\nDataset: {real['n_rows']} clean rows (1 outlier dropped)")
    print(f"  weekly_miles:      {min(wm):.1f} – {max(wm):.1f}  mean={np.mean(wm):.1f}")
    print(f"  pace_min_per_mile: {min(pm):.1f} – {max(pm):.1f}  mean={np.mean(pm):.1f}")
    print(f"  finish_minutes:    {min(fm):.1f} – {max(fm):.1f}  mean={np.mean(fm):.1f}")

    print(SYNTHETIC_FORMULA_NOTE)

    print("Real data linear regression (normal equation θ* = (XᵀX)⁻¹Xᵀy):")
    print(f"  θ₀  intercept:         {real['theta_0_intercept']:.2f} min")
    print(f"  θ₁  weekly_miles:      {real['theta_1_weekly_miles']:.4f} min per mile/week")
    print(f"  θ₂  pace_min_per_mile: {real['theta_2_pace_min_per_mile']:.4f} min per min/mile unit")
    print(f"  RMSE:  {real['rmse_minutes']:.2f} min")
    print(f"  MAE:   {real['mae_minutes']:.2f} min")
    print(f"  R²:    {real['r_squared']:.4f}")

    print()
    print("Comparison (real θ vs calibrated synthetic constants):")
    print(
        f"  weekly volume — real θ₁ (single feature): {real['theta_1_weekly_miles']:.2f}  |  "
        "synthetic: split across avg (-0.90) + peak (-0.935) ≈ combined -1.835 effect"
    )
    print(
        f"  pace          — real θ₂: {real['theta_2_pace_min_per_mile']:.2f}  |  "
        f"synthetic _COEFF_PACE: 7.383 (= θ₂ × 0.65)"
    )

    print()
    print("Scaled targets used when updating synthetic_data.py:")
    print(f"  suggested weekly (×0.65 from θ₁): {suggestion['suggested_avg_weekly_miles_coeff']}")
    print(f"  suggested pace coeff (×0.65):   {suggestion['suggested_pace_min_per_mile_coeff']}")
    print()
    print(f"  Note: {suggestion['note']}")
    print("=" * 62)


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_calibration(output_path: str | Path, real: dict, suggestion: dict) -> None:
    data = {"real_coefficients": real, "suggested_updates": suggestion}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"\nSaved calibration to: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calibrate synthetic formula from real marathon data (utility, not part of the package)."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=_DEFAULT_CSV,
        help=f"Path to CalibrationData.csv (default: {_DEFAULT_CSV})",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Path for calibrated_coefficients.json (default: same folder as CSV)",
    )
    args = parser.parse_args()

    csv_path = args.csv
    out_path = Path(args.out) if args.out else csv_path.parent / "calibrated_coefficients.json"

    rows = load_and_clean(csv_path)
    real = fit_real_coefficients(rows)
    suggestion = compare_and_suggest(real)
    print_report(real, suggestion, rows)
    save_calibration(out_path, real, suggestion)


if __name__ == "__main__":
    main()
