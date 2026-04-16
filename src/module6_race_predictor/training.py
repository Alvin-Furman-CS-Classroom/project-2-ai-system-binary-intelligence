"""
Train and persist the Module 6 race prediction models.

Artifacts saved inside `base` directory:
  synthetic_race_training.csv  – synthetic training data (auto-generated)
  module6_models.pkl           – scaler + models + metadata
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np

from .constants import DEFAULT_MODULE6_DATA_DIR, FEATURE_COLUMNS
from .gradient_descent import LinearRegressionGD, LogisticRegressionGD

_CSV_NAME = "synthetic_race_training.csv"
_PKL_NAME = "module6_models.pkl"
_REQUIRED_BUNDLE_KEYS = frozenset({"finish", "readiness", "scaler", "metadata"})


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


def _average_rank_1based(scores: np.ndarray) -> np.ndarray:
    """Average ranks (1-based), tie-aware (Wilcoxon / ROC AUC style)."""
    n = len(scores)
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(n, dtype=np.float64)
    sorted_scores = scores[order]
    i = 0
    while i < n:
        j = i
        while j + 1 < n and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        ranks[order[i : j + 1]] = avg
        i = j + 1
    return ranks


def _roc_auc_binary(y_true: np.ndarray, proba_positive: np.ndarray) -> float | None:
    """Mann–Whitney U / rank AUC; ``None`` if only one class is present."""
    y_true = np.asarray(y_true).astype(int)
    proba_positive = np.asarray(proba_positive).astype(float)
    n_pos = int(np.sum(y_true == 1))
    n_neg = int(np.sum(y_true == 0))
    if n_pos == 0 or n_neg == 0:
        return None
    ranks = _average_rank_1based(proba_positive)
    sum_ranks_pos = float(np.sum(ranks[y_true == 1]))
    return (sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def _json_safe(obj: Any) -> Any:
    """Convert metadata values for ``json.dump`` (NumPy scalars, nested lists)."""
    if obj is None or isinstance(obj, (bool, str)):
        return obj
    if isinstance(obj, (float, int)):
        return obj
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


def _readiness_test_metrics(
    model: LogisticRegressionGD, X: np.ndarray, y: np.ndarray
) -> tuple[float, float, float, float | None, list[list[int]]]:
    """Test-set precision, recall, F1, ROC AUC, and 2×2 confusion matrix [[TN,FP],[FN,TP]]."""
    y_true = y.astype(int)
    y_pred = model.predict(X).astype(int)
    proba = model.predict_proba(X)[:, 1]

    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    cm: list[list[int]] = [[tn, fp], [fn, tp]]

    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

    auc = _roc_auc_binary(y_true, proba)
    return prec, rec, f1, auc, cm


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
        bundle = pickle.load(f)
    if not isinstance(bundle, dict):
        raise ValueError("Model bundle must be a dict.")
    missing = _REQUIRED_BUNDLE_KEYS - bundle.keys()
    if missing:
        raise ValueError(f"Model bundle missing keys: {sorted(missing)}")
    return bundle


def train_and_save(
    csv_path: str | Path,
    out_dir: str | Path,
    *,
    n_epochs: int = 600,
    batch_size: int = 64,
) -> dict:
    """
    Train on a CSV using a 70/15/15 train/validation/test split, persist ``module6_models.pkl``
    under ``out_dir``, and return metadata including test-set regression and classification metrics.
    """
    from .synthetic_data import load_synthetic_csv

    csv_path = Path(csv_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    X, y_time, y_goal = load_synthetic_csv(csv_path)
    n = len(X)
    if n < 3:
        raise ValueError("train_and_save requires at least 3 rows for train/val/test splits.")

    rng = np.random.default_rng(42)
    idx = rng.permutation(n)
    n_tr = int(0.70 * n)
    n_val = int(0.15 * n)
    n_te = n - n_tr - n_val
    n_tr = max(1, n_tr)
    n_val = max(1, n_val)
    n_te = max(1, n_te)
    # Fix rounding so the three parts sum to n
    while n_tr + n_val + n_te > n:
        if n_tr >= n_val and n_tr >= n_te:
            n_tr -= 1
        elif n_val >= n_te:
            n_val -= 1
        else:
            n_te -= 1
    while n_tr + n_val + n_te < n:
        n_tr += 1

    i1 = n_tr
    i2 = n_tr + n_val
    tr, val, te = idx[:i1], idx[i1:i2], idx[i2:]

    scaler = _StandardScaler()
    X_tr_s = scaler.fit_transform(X[tr])
    X_val_s = scaler.transform(X[val])
    X_te_s = scaler.transform(X[te])

    y_time_tr, y_time_val, y_time_te = y_time[tr], y_time[val], y_time[te]
    y_goal_tr, y_goal_val, y_goal_te = y_goal[tr], y_goal[val], y_goal[te]

    finish_model = LinearRegressionGD(
        learning_rate=0.01, n_epochs=n_epochs, batch_size=batch_size, tol=1e-5
    )
    finish_model.fit(X_tr_s, y_time_tr, X_val_s, y_time_val)

    ready_model = LogisticRegressionGD(
        learning_rate=0.05, n_epochs=n_epochs, batch_size=batch_size, tol=1e-5
    )
    ready_model.fit(X_tr_s, y_goal_tr, X_val_s, y_goal_val)

    preds_te = finish_model.predict(X_te_s)
    finish_rmse_test = finish_model.rmse(X_te_s, y_time_te)
    finish_mae_test = float(np.mean(np.abs(preds_te - y_time_te)))
    residual_std = float(np.std(preds_te - y_time_te))

    prec, rec, f1, auc, cm = _readiness_test_metrics(ready_model, X_te_s, y_goal_te)

    meta = {
        "residual_std_minutes": residual_std,
        "finish_rmse_test": finish_rmse_test,
        "finish_mae_test": finish_mae_test,
        "readiness_precision": prec,
        "readiness_recall": rec,
        "readiness_f1": f1,
        "readiness_auc": auc,
        "readiness_confusion_matrix": cm,
        "n_train": len(tr),
        "n_val": len(val),
        "n_test": len(te),
        "feature_columns": FEATURE_COLUMNS,
        "val_rmse_minutes": finish_model.rmse(X_val_s, y_time_val),
        "val_accuracy": ready_model.accuracy(X_val_s, y_goal_val),
    }

    bundle = {
        "finish": finish_model,
        "readiness": ready_model,
        "scaler": scaler,
        "metadata": meta,
    }
    pkl_path = out_dir / _PKL_NAME
    with open(pkl_path, "wb") as f:
        pickle.dump(bundle, f)

    meta_json_path = out_dir / "metadata.json"
    with open(meta_json_path, "w", encoding="utf-8") as f:
        json.dump(_json_safe(meta), f, indent=2)
        f.write("\n")
    print(f"[training] Wrote evaluation metadata → {meta_json_path}")

    return meta
