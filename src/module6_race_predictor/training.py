"""
Train and persist the Module 6 race prediction models.

Artifacts saved inside `base` directory:
  synthetic_race_training.csv  – synthetic training data (auto-generated)
  module6_models.pkl           – scaler + models + metadata
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

from .constants import DEFAULT_MODULE6_DATA_DIR, FEATURE_COLUMNS
from .gradient_descent import LinearRegressionGD, LogisticRegressionGD

_CSV_NAME = "synthetic_race_training.csv"
_PKL_NAME = "module6_models.pkl"


class _StandardScaler:
    """Zero-mean, unit-variance scaler built from scratch (no sklearn)."""

    def __init__(self) -> None:
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> "_StandardScaler":
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0)
        self.std_[self.std_ == 0] = 1.0  # avoid division by zero on constant cols
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        return (X - self.mean_) / self.std_

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)


def _train(csv_path: Path) -> dict:
    from .synthetic_data import load_synthetic_csv

    X, y_time, y_goal = load_synthetic_csv(csv_path)

    # 80/20 train / validation split
    n = len(X)
    split = int(n * 0.8)
    rng = np.random.default_rng(42)
    idx = rng.permutation(n)
    tr, val = idx[:split], idx[split:]

    X_tr, X_val = X[tr], X[val]
    y_time_tr, y_time_val = y_time[tr], y_time[val]
    y_goal_tr, y_goal_val = y_goal[tr], y_goal[val]

    scaler = _StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_val_s = scaler.transform(X_val)

    # Finish-time regressor (linear regression via gradient descent)
    finish_model = LinearRegressionGD(
        learning_rate=0.01, n_epochs=600, batch_size=64, tol=1e-5
    )
    finish_model.fit(X_tr_s, y_time_tr, X_val_s, y_time_val)

    preds_val = finish_model.predict(X_val_s)
    residual_std = float(np.std(preds_val - y_time_val))
    rmse = finish_model.rmse(X_val_s, y_time_val)

    # Readiness classifier (logistic regression via gradient descent)
    ready_model = LogisticRegressionGD(
        learning_rate=0.05, n_epochs=500, batch_size=64, tol=1e-5
    )
    ready_model.fit(X_tr_s, y_goal_tr, X_val_s, y_goal_val)
    acc = ready_model.accuracy(X_val_s, y_goal_val)

    print(f"[training] finish RMSE={rmse:.2f} min | readiness acc={acc:.3f}")

    return {
        "finish": finish_model,
        "readiness": ready_model,
        "scaler": scaler,
        "metadata": {
            "residual_std_minutes": residual_std,
            "val_rmse_minutes": rmse,
            "val_accuracy": acc,
            "n_train": split,
            "n_val": n - split,
            "feature_columns": FEATURE_COLUMNS,
        },
    }


def ensure_training_artifacts(base: Path | None = None) -> None:
    """Generate synthetic data and train models if the pkl bundle is missing."""
    base = Path(base or DEFAULT_MODULE6_DATA_DIR)
    pkl_path = base / _PKL_NAME
    if pkl_path.exists():
        return

    csv_path = base / _CSV_NAME
    if not csv_path.exists():
        from .synthetic_data import write_synthetic_csv
        print(f"[training] Generating synthetic data → {csv_path}")
        write_synthetic_csv(csv_path, n_rows=2000)

    print("[training] Training models...")
    bundle = _train(csv_path)
    pkl_path.parent.mkdir(parents=True, exist_ok=True)
    with open(pkl_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"[training] Saved models → {pkl_path}")


def load_models(base: Path | None = None) -> dict:
    """Load the trained model bundle (scaler + models + metadata) from disk."""
    base = Path(base or DEFAULT_MODULE6_DATA_DIR)
    pkl_path = base / _PKL_NAME
    if not pkl_path.exists():
        raise FileNotFoundError(
            f"Model bundle not found at {pkl_path}. "
            "Call ensure_training_artifacts() first, or set auto_train=True."
        )
    with open(pkl_path, "rb") as f:
        return pickle.load(f)
