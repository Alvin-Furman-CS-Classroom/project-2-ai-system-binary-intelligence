"""
Train and persist the Module 6 models.

Uses from-scratch gradient descent (LinearRegressionGD, LogisticRegressionGD)
so the training loop is academically transparent and matches course slides.

Split: 70% train / 15% validation / 15% test
  - Train:      learn θ via gradient descent
  - Validation: early stopping + loss curve logging
  - Test:       final reported metrics (never seen during training or tuning)

Confidence interval for finish time prediction uses TEST set residual std,
not training set residual std.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

from .constants import DEFAULT_MODULE6_DATA_DIR, FEATURE_COLUMNS
from .gradient_descent import LinearRegressionGD, LogisticRegressionGD
from .synthetic_data import load_synthetic_csv, write_synthetic_csv


def _readiness_test_metrics(
    ready_model: LogisticRegressionGD,
    X_test_s: np.ndarray,
    y_g_test: np.ndarray,
) -> tuple[float, float, float, float | None, list[list[int]]]:
    """
    Classification metrics on the test split only.
    ``readiness_auc`` is None if only one class is present (AUC undefined).
    """
    y_int = y_g_test.astype(int)
    test_preds_class = ready_model.predict(X_test_s)
    test_proba = ready_model.predict_proba(X_test_s)[:, 1]
    precision = float(precision_score(y_int, test_preds_class, zero_division=0))
    recall = float(recall_score(y_int, test_preds_class, zero_division=0))
    f1 = float(f1_score(y_int, test_preds_class, zero_division=0))
    cm = confusion_matrix(y_int, test_preds_class, labels=[0, 1]).tolist()
    auc: float | None
    if len(np.unique(y_int)) < 2:
        auc = None
    else:
        try:
            auc = float(roc_auc_score(y_int, test_proba))
        except ValueError:
            auc = None
    return precision, recall, f1, auc, cm


def _three_way_split(
    X: np.ndarray,
    y_time: np.ndarray,
    y_goal: np.ndarray,
    *,
    val_frac: float = 0.15,
    test_frac: float = 0.15,
    seed: int = 42,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """
    Returns X_train, X_val, X_test, y_t_train, y_t_val, y_t_test,
            y_g_train, y_g_val, y_g_test.
    """
    n = X.shape[0]
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)

    n_test = int(n * test_frac)
    n_val = int(n * val_frac)
    n_train = n - n_test - n_val

    train_i = idx[:n_train]
    val_i = idx[n_train : n_train + n_val]
    test_i = idx[n_train + n_val :]

    return (
        X[train_i], X[val_i], X[test_i],
        y_time[train_i], y_time[val_i], y_time[test_i],
        y_goal[train_i], y_goal[val_i], y_goal[test_i],
    )


def _scale_splits(
    X_train: np.ndarray,
    X_val: np.ndarray,
    X_test: np.ndarray,
) -> tuple[StandardScaler, np.ndarray, np.ndarray, np.ndarray]:
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    return scaler, X_train_s, scaler.transform(X_val), scaler.transform(X_test)


def _fit_finish_model(
    X_train_s: np.ndarray,
    y_t_train: np.ndarray,
    X_val_s: np.ndarray,
    y_t_val: np.ndarray,
    X_test_s: np.ndarray,
    y_t_test: np.ndarray,
    *,
    lr_finish: float,
    n_epochs: int,
    batch_size: int,
) -> tuple[LinearRegressionGD, float, float, float]:
    finish_model = LinearRegressionGD(
        learning_rate=lr_finish,
        n_epochs=n_epochs,
        batch_size=batch_size,
    )
    finish_model.fit(X_train_s, y_t_train, X_val_s, y_t_val)
    test_residuals = y_t_test - finish_model.predict(X_test_s)
    residual_std_test = float(np.std(test_residuals))
    rmse_test = finish_model.rmse(X_test_s, y_t_test)
    mae_test = finish_model.mae(X_test_s, y_t_test)
    return finish_model, rmse_test, mae_test, residual_std_test


def _fit_readiness_model(
    X_train_s: np.ndarray,
    y_g_train: np.ndarray,
    X_val_s: np.ndarray,
    y_g_val: np.ndarray,
    X_test_s: np.ndarray,
    y_g_test: np.ndarray,
    *,
    lr_readiness: float,
    n_epochs: int,
    batch_size: int,
) -> tuple[
    LogisticRegressionGD,
    float,
    float,
    float,
    float,
    float,
    float | None,
    list[list[int]],
]:
    ready_model = LogisticRegressionGD(
        learning_rate=lr_readiness,
        n_epochs=n_epochs,
        batch_size=batch_size,
        class_weight="balanced",
    )
    ready_model.fit(X_train_s, y_g_train, X_val_s, y_g_val)
    val_acc = ready_model.accuracy(X_val_s, y_g_val)
    test_acc = ready_model.accuracy(X_test_s, y_g_test)
    precision, recall, f1, auc, cm = _readiness_test_metrics(
        ready_model, X_test_s, y_g_test
    )
    return (
        ready_model,
        val_acc,
        test_acc,
        precision,
        recall,
        f1,
        auc,
        cm,
    )


def _compose_metadata(
    *,
    finish_model: LinearRegressionGD,
    ready_model: LogisticRegressionGD,
    X_train: np.ndarray,
    X_val: np.ndarray,
    X_test: np.ndarray,
    rmse_test: float,
    mae_test: float,
    residual_std_test: float,
    val_acc: float,
    test_acc: float,
    precision: float,
    recall: float,
    f1: float,
    auc: float | None,
    cm: list[list[int]],
) -> dict:
    return {
        "feature_names": list(FEATURE_COLUMNS),
        "n_train": int(X_train.shape[0]),
        "n_val": int(X_val.shape[0]),
        "n_test": int(X_test.shape[0]),
        "finish_rmse_test": round(rmse_test, 4),
        "finish_mae_test": round(mae_test, 4),
        "residual_std_minutes": round(residual_std_test, 4),
        "readiness_val_accuracy": round(val_acc, 4),
        "readiness_test_accuracy": round(test_acc, 4),
        "readiness_precision": round(precision, 4),
        "readiness_recall": round(recall, 4),
        "readiness_f1": round(f1, 4),
        "readiness_auc": None if auc is None else round(auc, 4),
        "readiness_confusion_matrix": cm,
        "finish_train_loss_final": round(finish_model.train_losses_[-1], 4),
        "finish_val_loss_final": round(finish_model.val_losses_[-1], 4) if finish_model.val_losses_ else None,
        "readiness_train_loss_final": round(ready_model.train_losses_[-1], 6),
        "readiness_val_loss_final": round(ready_model.val_losses_[-1], 6) if ready_model.val_losses_ else None,
        "class_weights": ready_model.class_weights_,
    }


def _print_training_summary(
    *,
    rmse_test: float,
    mae_test: float,
    residual_std_test: float,
    val_acc: float,
    test_acc: float,
    precision: float,
    recall: float,
    f1: float,
    auc: float | None,
    cm: list[list[int]],
) -> None:
    print(
        f"[training] Finish time  | RMSE={rmse_test:.2f} min  MAE={mae_test:.2f} min  "
        f"ResidualStd={residual_std_test:.2f} min (test set)"
    )
    auc_s = f"{auc:.3f}" if auc is not None else "n/a"
    print(
        f"[training] Readiness    | val_acc={val_acc:.3f}  test_acc={test_acc:.3f}  "
        f"P={precision:.3f}  R={recall:.3f}  F1={f1:.3f}  AUC={auc_s}  CM={cm}"
    )


def train_and_save(
    csv_path: str | Path,
    models_dir: str | Path,
    *,
    lr_finish: float = 0.01,
    lr_readiness: float = 0.05,
    n_epochs: int = 500,
    batch_size: int = 32,
) -> dict:
    """
    Train LinearRegressionGD (finish time) and LogisticRegressionGD (met_goal)
    on the synthetic CSV.

    Saves module6_models.pkl and metadata.json.
    Confidence interval residual_std is computed on the TEST set.
    """
    csv_path = Path(csv_path)
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    X, y_time, y_goal = load_synthetic_csv(csv_path)

    (
        X_train, X_val, X_test,
        y_t_train, y_t_val, y_t_test,
        y_g_train, y_g_val, y_g_test,
    ) = _three_way_split(X, y_time, y_goal)

    scaler, X_train_s, X_val_s, X_test_s = _scale_splits(X_train, X_val, X_test)

    finish_model, rmse_test, mae_test, residual_std_test = _fit_finish_model(
        X_train_s,
        y_t_train,
        X_val_s,
        y_t_val,
        X_test_s,
        y_t_test,
        lr_finish=lr_finish,
        n_epochs=n_epochs,
        batch_size=batch_size,
    )

    (
        ready_model,
        val_acc,
        test_acc,
        precision,
        recall,
        f1,
        auc,
        cm,
    ) = _fit_readiness_model(
        X_train_s,
        y_g_train,
        X_val_s,
        y_g_val,
        X_test_s,
        y_g_test,
        lr_readiness=lr_readiness,
        n_epochs=n_epochs,
        batch_size=batch_size,
    )

    metadata = _compose_metadata(
        finish_model=finish_model,
        ready_model=ready_model,
        X_train=X_train,
        X_val=X_val,
        X_test=X_test,
        rmse_test=rmse_test,
        mae_test=mae_test,
        residual_std_test=residual_std_test,
        val_acc=val_acc,
        test_acc=test_acc,
        precision=precision,
        recall=recall,
        f1=f1,
        auc=auc,
        cm=cm,
    )

    _print_training_summary(
        rmse_test=rmse_test,
        mae_test=mae_test,
        residual_std_test=residual_std_test,
        val_acc=val_acc,
        test_acc=test_acc,
        precision=precision,
        recall=recall,
        f1=f1,
        auc=auc,
        cm=cm,
    )

    bundle = {
        "finish": finish_model,
        "readiness": ready_model,
        "scaler": scaler,
        "metadata": metadata,
    }
    out_path = models_dir / "module6_models.pkl"
    with open(out_path, "wb") as f:
        pickle.dump(bundle, f, protocol=pickle.HIGHEST_PROTOCOL)

    with open(models_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata


def load_models(models_dir: str | Path) -> dict:
    path = Path(models_dir) / "module6_models.pkl"
    if not path.exists():
        raise FileNotFoundError(
            f"Trained models not found at {path}. Run ensure_training_artifacts() or train_and_save()."
        )
    with open(path, "rb") as f:
        bundle = pickle.load(f)
    required = ("finish", "readiness", "scaler", "metadata")
    missing = [k for k in required if k not in bundle]
    if missing:
        raise ValueError(
            f"{path} is missing keys {missing}. Delete the pickle and retrain "
            "(e.g. remove module6_models.pkl and run ensure_training_artifacts)."
        )
    return bundle


def ensure_training_artifacts(
    module6_dir: str | Path | None = None,
    *,
    n_synthetic_rows: int = 2000,
) -> Path:
    """
    Create module6_dir, write synthetic CSV if missing, train if model pickle missing.
    Returns path to module6_dir.
    """
    base = Path(module6_dir or DEFAULT_MODULE6_DATA_DIR)
    base.mkdir(parents=True, exist_ok=True)
    csv_p = base / "synthetic_race_training.csv"
    if not csv_p.exists():
        write_synthetic_csv(csv_p, n_rows=n_synthetic_rows, seed=42)
    if not (base / "module6_models.pkl").exists():
        train_and_save(csv_p, base)
    return base
