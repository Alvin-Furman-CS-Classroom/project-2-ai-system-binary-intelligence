"""Smoke tests for from-scratch GD models."""

import numpy as np

from src.module6_race_predictor.gradient_descent import LinearRegressionGD, LogisticRegressionGD


def test_linear_gd_low_rmse_on_linear_data():
    rng = np.random.default_rng(42)
    X = rng.normal(size=(120, 3))
    y = 2.0 + 1.5 * X[:, 0] - 0.7 * X[:, 1] + 0.3 * X[:, 2]
    m = LinearRegressionGD(learning_rate=0.08, n_epochs=600, batch_size=24)
    m.fit(X, y)
    assert m.rmse(X, y) < 0.35


def test_logistic_gd_reasonable_accuracy():
    rng = np.random.default_rng(7)
    X0 = rng.normal(size=(60, 2)) - 1.2
    X1 = rng.normal(size=(60, 2)) + 1.2
    X = np.vstack([X0, X1])
    y = np.array([0] * 60 + [1] * 60, dtype=float)
    m = LogisticRegressionGD(
        learning_rate=0.15, n_epochs=400, batch_size=20, class_weight=None
    )
    m.fit(X, y)
    assert m.accuracy(X, y) >= 0.85
