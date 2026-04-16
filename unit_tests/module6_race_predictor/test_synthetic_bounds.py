"""Synthetic label and row bounds."""

import numpy as np

from src.module6_race_predictor.synthetic_data import generate_row


def test_generate_row_finish_time_within_clip():
    rng = np.random.default_rng(12345)
    for _ in range(50):
        row = generate_row(rng)
        g_km = row["goal_distance_km"]
        lo = max(10.0, g_km * 2.5)
        hi = max(lo + 10.0, g_km * 12.0)
        assert lo <= row["actual_finish_time_minutes"] <= hi
