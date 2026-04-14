"""Synthetic dataset shape and column contract."""

from pathlib import Path
import tempfile

import numpy as np

from src.module6_race_predictor.constants import CSV_COLUMNS, FEATURE_COLUMNS
from src.module6_race_predictor.synthetic_data import (
    generate_row,
    load_synthetic_csv,
    write_synthetic_csv,
)


def test_generate_row_has_all_feature_columns():
    rng = np.random.default_rng(0)
    row = generate_row(rng)
    for c in FEATURE_COLUMNS:
        assert c in row
    assert "actual_finish_time_minutes" in row
    assert "met_goal" in row


def test_csv_roundtrip_load_matches_feature_order():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "t.csv"
        write_synthetic_csv(p, n_rows=30, seed=1, verbose=False)
        X, y_t, y_g = load_synthetic_csv(p)
        assert X.shape[1] == len(FEATURE_COLUMNS)
        assert len(y_t) == 30
        assert len(CSV_COLUMNS) == len(FEATURE_COLUMNS) + 2
