"""Tests for test-set readiness metrics helper."""

import numpy as np

from src.module6_race_predictor.gradient_descent import LogisticRegressionGD
from src.module6_race_predictor.training import _readiness_test_metrics


def test_readiness_metrics_auc_none_when_single_class():
    X = np.random.default_rng(0).normal(size=(16, 3))
    y = np.zeros(16)
    m = LogisticRegressionGD(n_epochs=80, batch_size=8, class_weight=None)
    m.fit(X, y)
    _, _, _, auc, _ = _readiness_test_metrics(m, X, y)
    assert auc is None


def test_readiness_metrics_auc_when_two_classes():
    rng = np.random.default_rng(1)
    X = rng.normal(size=(64, 2))
    y = np.array([0.0] * 32 + [1.0] * 32)
    m = LogisticRegressionGD(n_epochs=250, batch_size=16, class_weight=None)
    m.fit(X, y, X, y)
    _, _, _, auc, cm = _readiness_test_metrics(m, X, y)
    assert auc is not None
    assert isinstance(cm, list)
