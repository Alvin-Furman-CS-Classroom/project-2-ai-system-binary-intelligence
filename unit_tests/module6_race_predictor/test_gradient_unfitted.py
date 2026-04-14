"""Error paths when models are used before fitting."""

import numpy as np
import pytest

from src.module6_race_predictor.gradient_descent import LinearRegressionGD, LogisticRegressionGD


def test_linear_predict_before_fit_raises():
    m = LinearRegressionGD(n_epochs=10)
    with pytest.raises(RuntimeError, match="not been fitted"):
        m.predict(np.array([[1.0, 2.0]]))


def test_logistic_predict_before_fit_raises():
    m = LogisticRegressionGD(n_epochs=10)
    with pytest.raises(RuntimeError, match="not been fitted"):
        m.predict_proba(np.array([[1.0, 2.0]]))
