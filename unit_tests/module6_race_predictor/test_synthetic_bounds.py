"""Synthetic label and row bounds."""

import numpy as np

from src.module6_race_predictor.constants import SYNTHETIC_FINISH_CLIP_MIN_MAX
from src.module6_race_predictor.synthetic_data import generate_row


def test_generate_row_finish_time_within_clip():
    rng = np.random.default_rng(12345)
    for _ in range(50):
        row = generate_row(rng)
        lo, hi = SYNTHETIC_FINISH_CLIP_MIN_MAX
        assert lo <= row["actual_finish_time_minutes"] <= hi
