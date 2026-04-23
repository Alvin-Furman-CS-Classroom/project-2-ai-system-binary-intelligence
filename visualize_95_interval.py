"""
Visualise the 95 % prediction interval from the Module 6 race predictor.

Three panels:
  1. Predicted vs Actual finish time + 95 % CI band on the validation set
  2. Residual histogram + ±1.96 σ markers
  3. CI width as the key driver (training pace) changes
"""

from __future__ import annotations

import sys
from pathlib import Path

# ── project root on path ─────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import matplotlib
matplotlib.use("Agg")                   # headless – saves a PNG
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from module6_race_predictor.training import ensure_training_artifacts, load_models
from module6_race_predictor.synthetic_data import load_synthetic_csv
from module6_race_predictor.constants import DEFAULT_MODULE6_DATA_DIR, MARATHON_KM

# ── load / train ──────────────────────────────────────────────────────────────
base = ROOT / DEFAULT_MODULE6_DATA_DIR
ensure_training_artifacts(base)
bundle   = load_models(base)
scaler   = bundle["scaler"]
finish   = bundle["finish"]
meta     = bundle["metadata"]
resid_sd = float(meta["residual_std_minutes"])   # σ from val set

csv_path = base / "synthetic_race_training.csv"
X_all, y_time, _ = load_synthetic_csv(csv_path)

# reproduce the same 80/20 split used during training
n = len(X_all)
rng = np.random.default_rng(42)
idx  = rng.permutation(n)
val_idx = idx[int(n * 0.8):]
X_val, y_val = X_all[val_idx], y_time[val_idx]

X_val_s = scaler.transform(X_val)
preds   = finish.predict(X_val_s)
resids  = preds - y_val
lo      = preds - 1.96 * resid_sd
hi      = preds + 1.96 * resid_sd
in_band = ((y_val >= lo) & (y_val <= hi)).mean() * 100

# ── figure ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle(
    f"Module 6 · Race Finish-Time Predictor  |  95 % interval (σ = {resid_sd:.1f} min)",
    fontsize=14, fontweight="bold", y=1.01,
)

BG   = "#0f1117"
GRID = "#2a2d3a"
BLUE = "#4c9be8"
TEAL = "#38d9a9"
ORG  = "#ff9f43"
RED  = "#ee5a5a"

for ax in axes:
    ax.set_facecolor(BG)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID)
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    ax.grid(color=GRID, linewidth=0.5)
fig.patch.set_facecolor(BG)

# ─── Panel 1 : Predicted vs Actual + CI band ─────────────────────────────────
ax = axes[0]
sort_order = np.argsort(preds)
p_sorted = preds[sort_order]
lo_s     = lo[sort_order]
hi_s     = hi[sort_order]
y_s      = y_val[sort_order]

ax.fill_between(p_sorted, lo_s, hi_s, alpha=0.25, color=TEAL, label="95 % CI band")
ax.scatter(preds, y_val, s=6, alpha=0.45, color=BLUE, linewidths=0, label="Runners")
ax.plot([y_val.min(), y_val.max()],
        [y_val.min(), y_val.max()],
        "--", color=ORG, lw=1.4, label="Perfect prediction")

ax.set_xlabel("Predicted finish (min)")
ax.set_ylabel("Actual finish (min)")
ax.set_title(f"Predicted vs Actual\n{in_band:.1f} % of runners inside band")
ax.legend(facecolor=GRID, labelcolor="white", fontsize=8)

# ─── Panel 2 : Residual histogram ────────────────────────────────────────────
ax = axes[1]
ax.hist(resids, bins=50, color=BLUE, alpha=0.8, edgecolor="none")
ax.axvline( 1.96 * resid_sd, color=RED,  lw=2, linestyle="--", label=f"+1.96σ = +{1.96*resid_sd:.1f} min")
ax.axvline(-1.96 * resid_sd, color=TEAL, lw=2, linestyle="--", label=f"−1.96σ = −{1.96*resid_sd:.1f} min")
ax.axvline(0, color=ORG, lw=1.5, linestyle=":", label="Zero error")

ax.set_xlabel("Residual  (predicted − actual, min)")
ax.set_ylabel("Count")
ax.set_title("Residual distribution\n(errors your model makes)")
ax.legend(facecolor=GRID, labelcolor="white", fontsize=8)

# shade the 95 % zone
ax.axvspan(-1.96*resid_sd, 1.96*resid_sd, alpha=0.08, color=TEAL)

# annotation
ax.text(0.98, 0.97,
        f"σ = {resid_sd:.1f} min\n95 % band width = {2*1.96*resid_sd:.0f} min",
        transform=ax.transAxes, ha="right", va="top",
        color="white", fontsize=9,
        bbox=dict(boxstyle="round,pad=0.4", fc=GRID, ec="none"))

# ─── Panel 3 : CI shifts as training pace changes ────────────────────────────
ax = axes[2]

# Build a "template" runner at median feature values, then sweep pace
X_median = np.median(X_val, axis=0)

# column index of avg_training_pace_min_per_mile  (index 8 in FEATURE_COLUMNS)
PACE_COL = 8
paces = np.linspace(6.5, 15.5, 200)
sweep_X = np.tile(X_median, (len(paces), 1))
sweep_X[:, PACE_COL] = paces

sweep_s    = scaler.transform(sweep_X)
sweep_pred = finish.predict(sweep_s)
sweep_lo   = sweep_pred - 1.96 * resid_sd
sweep_hi   = sweep_pred + 1.96 * resid_sd

ax.fill_between(paces, sweep_lo, sweep_hi, alpha=0.30, color=TEAL, label="95 % CI")
ax.plot(paces, sweep_pred, color=ORG, lw=2.2, label="Predicted finish")
ax.plot(paces, sweep_lo,   color=TEAL, lw=1, linestyle="--")
ax.plot(paces, sweep_hi,   color=RED,  lw=1, linestyle="--")

# mark the example the user saw:  1:34:21 – 2:01:38
ex_lo_m = 94 + 21/60        # 1:34:21
ex_hi_m = 121 + 38/60       # 2:01:38
ex_mid  = (ex_lo_m + ex_hi_m) / 2
ax.axhline(ex_mid, color=BLUE, lw=1, linestyle=":")
ax.axhspan(ex_lo_m, ex_hi_m, alpha=0.18, color=BLUE)
ax.text(6.7, ex_mid + 2, "1:34:21 – 2:01:38\nyour example", color=BLUE, fontsize=8)

ax.set_xlabel("Training pace  (min / mile)")
ax.set_ylabel("Finish time  (min)")
ax.set_title("How the 95 % band moves\nas pace changes")
ax.legend(facecolor=GRID, labelcolor="white", fontsize=8)

plt.tight_layout()
out = ROOT / "module6_95_interval.png"
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG)
print(f"Saved → {out}")
