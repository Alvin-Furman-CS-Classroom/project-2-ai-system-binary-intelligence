"""
Generate an inline 95 % prediction-interval chart as a base64 PNG.
No files written to disk; returns a data-URI string ready for <img src=...>.
"""

from __future__ import annotations

import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def _fmt(minutes: float) -> str:
    total_sec = int(round(minutes * 60))
    h, rem = divmod(total_sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def make_interval_chart_b64(
    pred_min: float,
    lo_min: float,
    hi_min: float,
    goal_min: float | None = None,
) -> str:
    """Return a base64-encoded PNG data-URI for the 95 % interval chart."""

    ORANGE    = "#e67e22"
    ORANGE_LT = "#fdebd0"
    BLUE      = "#2980b9"
    GREY_LT   = "#aaaaaa"
    TRACK_BG  = "#eeeeee"
    BG        = "#ffffff"

    fig, ax = plt.subplots(figsize=(5.6, 2.0))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])

    span = hi_min - lo_min
    pad  = span * 0.40
    ax.set_xlim(lo_min - pad, hi_min + pad)
    ax.set_ylim(0, 1)

    CY = 0.48   # vertical centre of the track
    TH = 0.10   # half-height of track

    # ── background track ─────────────────────────────────────────────────────
    ax.add_patch(mpatches.Rectangle(
        (lo_min - pad, CY - TH), span + 2 * pad, 2 * TH,
        linewidth=0, facecolor=TRACK_BG, zorder=1,
    ))

    # ── CI band ───────────────────────────────────────────────────────────────
    ax.add_patch(mpatches.Rectangle(
        (lo_min, CY - TH - 0.04), span, 2 * TH + 0.08,
        linewidth=1.6, edgecolor=ORANGE, facecolor=ORANGE_LT, zorder=2,
    ))

    # ── goal dashed line (no label here) ─────────────────────────────────────
    if goal_min is not None:
        x_lo_vis = lo_min - pad
        x_hi_vis = hi_min + pad
        if x_lo_vis < goal_min < x_hi_vis:
            ax.plot([goal_min, goal_min], [CY - TH - 0.04, CY + TH + 0.04],
                    color=BLUE, lw=1.5, linestyle=(0, (4, 3)), zorder=4)

    # ── prediction circle on the track ───────────────────────────────────────
    ax.plot([pred_min, pred_min], [CY - TH, CY + TH + 0.04],
            color=ORANGE, lw=2.0, zorder=5, solid_capstyle="round")
    ax.plot(pred_min, CY, "o",
            color="white", markersize=11, zorder=6,
            markeredgecolor=ORANGE, markeredgewidth=2.2)

    # ── predicted time — above band ───────────────────────────────────────────
    ax.text(pred_min, CY + TH + 0.18,
            _fmt(pred_min),
            ha="center", va="bottom",
            fontsize=11.5, fontweight="bold", color=ORANGE,
            zorder=7, clip_on=False)

    # ── labels below band: lo bound, goal (if present), hi bound ─────────────
    lbl_y = CY - TH - 0.10
    tick_y_top = CY - TH - 0.04

    # Build list of (x, text, color), sorted left→right
    bottom = [(lo_min, _fmt(lo_min), GREY_LT)]
    if goal_min is not None and (lo_min - pad) < goal_min < (hi_min + pad):
        bottom.append((goal_min, f"Goal  {_fmt(goal_min)}", BLUE))
    bottom.append((hi_min, _fmt(hi_min), GREY_LT))
    bottom.sort(key=lambda t: t[0])

    # Outer labels anchor outward so they never overlap the band edge.
    # Middle label (goal) faces away from whichever bound is closer.
    n = len(bottom)
    aligns = ["center"] * n
    if n >= 2:
        aligns[0]  = "left"
        aligns[-1] = "right"
    if n == 3:
        # middle = goal; align away from the nearer neighbour
        mid_x = bottom[1][0]
        aligns[1] = "right" if (mid_x - bottom[0][0]) > (bottom[2][0] - mid_x) else "left"

    for (x_val, lbl, color), ha in zip(bottom, aligns):
        ax.plot([x_val, x_val], [tick_y_top, lbl_y + 0.01],
                color=color, lw=1.0, zorder=3, clip_on=False)
        ax.text(x_val, lbl_y, lbl,
                ha=ha, va="top", fontsize=7.5,
                color=color, clip_on=False)

    plt.subplots_adjust(left=0.03, right=0.97, top=0.92, bottom=0.12)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=160, bbox_inches="tight",
                facecolor=BG, transparent=False)
    plt.close(fig)
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode()
