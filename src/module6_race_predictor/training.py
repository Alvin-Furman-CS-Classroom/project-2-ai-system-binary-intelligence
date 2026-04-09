"""Fit and persist sklearn pipelines for finish time and readiness."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .constants import FEATURE_COLUMNS
from .synthetic_data import load_synthetic_csv, write_synthetic_csv


def _finish_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            ("reg", LinearRegression()),
        ]
    )


def _readiness_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "clf",
                LogisticRegression(max_iter=500, class_weight="balanced", random_state=42),
            ),
        ]
    )


def train_and_save(
    csv_path: str | Path,
    models_dir: str | Path,
    *,
    test_fraction: float = 0.15,
) -> dict:
    """
    Train on CSV (must include FEATURE_COLUMNS + labels).
    Saves joblib bundle and metadata.json with residual RMSE for intervals.
    """
    csv_path = Path(csv_path)
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    X, y_time, y_goal = load_synthetic_csv(csv_path)
    n = X.shape[0]
    rng = np.random.default_rng(42)
    idx = np.arange(n)
    rng.shuffle(idx)
    cut = int(n * (1 - test_fraction))
    train_i, test_i = idx[:cut], idx[cut:]

    X_train, X_test = X[train_i], X[test_i]
    y_t_train, y_t_test = y_time[train_i], y_time[test_i]
    y_g_train = y_goal[train_i]

    finish = _finish_pipeline()
    finish.fit(X_train, y_t_train)
    pred_train = finish.predict(X_train)
    resid = y_t_train - pred_train
    residual_std = float(np.sqrt(np.mean(resid**2)) + 1e-6)

    ready = _readiness_pipeline()
    ready.fit(X_train, y_g_train.astype(int))

    bundle = {
        "finish": finish,
        "readiness": ready,
        "metadata": {
            "feature_names": list(FEATURE_COLUMNS),
            "residual_std_minutes": residual_std,
            "n_train": int(cut),
            "n_test": int(n - cut),
            "rmse_test_minutes": float(
                np.sqrt(np.mean((finish.predict(X_test) - y_t_test) ** 2))
            ),
        },
    }
    joblib.dump(bundle, models_dir / "module6_models.joblib")

    with open(models_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(bundle["metadata"], f, indent=2)

    return bundle["metadata"]


def load_models(models_dir: str | Path) -> dict:
    path = Path(models_dir) / "module6_models.joblib"
    if not path.exists():
        raise FileNotFoundError(path)
    return joblib.load(path)


def ensure_training_artifacts(
    module6_dir: str | Path | None = None,
    *,
    n_synthetic_rows: int = 1200,
) -> Path:
    """
    Create module6_dir, write synthetic CSV if missing, train if joblib missing.
    Returns path to module6_dir.
    """
    base = Path(module6_dir or "data/module6")
    base.mkdir(parents=True, exist_ok=True)
    csv_p = base / "synthetic_race_training.csv"
    if not csv_p.exists():
        write_synthetic_csv(csv_p, n_rows=n_synthetic_rows, seed=42)
    joblib_p = base / "module6_models.joblib"
    if not joblib_p.exists():
        train_and_save(csv_p, base)
    return base
