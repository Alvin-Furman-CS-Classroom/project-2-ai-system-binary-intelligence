"""
From-scratch gradient descent implementations of linear and logistic regression.

These match the course slides exactly:
  - Linear regression minimises MSE via gradient descent: θ := θ - α * ∇MSE(θ)
  - Logistic regression applies sigmoid + cross-entropy loss with the same update rule
  - Both record training and validation loss per epoch for loss curve inspection
"""

from __future__ import annotations

import numpy as np


def _add_bias(X: np.ndarray) -> np.ndarray:
    """Prepend a column of ones (bias / intercept term x_0 = 1)."""
    return np.hstack([np.ones((X.shape[0], 1), dtype=np.float64), X])


def _sigmoid(z: np.ndarray) -> np.ndarray:
    """Numerically stable sigmoid: σ(z) = 1 / (1 + e^{-z})."""
    return np.where(
        z >= 0,
        1.0 / (1.0 + np.exp(-z)),
        np.exp(z) / (1.0 + np.exp(z)),
    )


class LinearRegressionGD:
    """
    Multivariate linear regression trained with mini-batch gradient descent.

    Model:  ŷ = θ · x  (x augmented with x_0 = 1 for the intercept)
    Loss:   MSE(θ) = (1/m) * Σ (ŷ_i - y_i)²
    Update: θ := θ - α * ∇MSE(θ)
            ∇MSE(θ) = (1/m) * Σ e_i * x_i   where e_i = ŷ_i - y_i

    Parameters
    ----------
    learning_rate : float
        Step size α for each gradient descent update.
    n_epochs : int
        Number of full passes through the training data.
    batch_size : int
        Mini-batch size. Use len(X) for batch gradient descent.
    tol : float
        Early stopping: halt when validation MSE improves by less than tol.
    """

    def __init__(
        self,
        learning_rate: float = 0.01,
        n_epochs: int = 500,
        batch_size: int = 32,
        tol: float = 1e-4,
    ) -> None:
        self.learning_rate = learning_rate
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self.tol = tol

        self.theta_: np.ndarray | None = None
        self.train_losses_: list[float] = []
        self.val_losses_: list[float] = []

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
    ) -> "LinearRegressionGD":
        X_b = _add_bias(X_train)
        m, n = X_b.shape
        self.theta_ = np.zeros(n, dtype=np.float64)

        has_val = X_val is not None and y_val is not None
        if has_val:
            X_val_b = _add_bias(X_val)

        rng = np.random.default_rng(42)
        prev_val_loss = float("inf")

        for epoch in range(self.n_epochs):
            idx = rng.permutation(m)
            X_b = X_b[idx]
            y_train = y_train[idx]

            for start in range(0, m, self.batch_size):
                end = start + self.batch_size
                Xb = X_b[start:end]
                yb = y_train[start:end]

                # Step 1: compute predictions  ŷ = θ · x
                y_hat = Xb @ self.theta_

                # Step 2: compute errors  e = ŷ - y
                errors = y_hat - yb

                # Step 3: compute gradient  ∇MSE = (1/m) * Σ e_i * x_i
                grad = (Xb.T @ errors) / len(yb)

                # Step 4: update parameters  θ := θ - α * ∇MSE
                self.theta_ -= self.learning_rate * grad

            train_loss = float(np.mean((X_b @ self.theta_ - y_train) ** 2))
            self.train_losses_.append(train_loss)

            if has_val:
                val_loss = float(np.mean((X_val_b @ self.theta_ - y_val) ** 2))
                self.val_losses_.append(val_loss)

                if prev_val_loss - val_loss < self.tol and epoch > 20:
                    break
                prev_val_loss = val_loss

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.theta_ is None:
            raise RuntimeError("Model has not been fitted yet.")
        return _add_bias(X) @ self.theta_

    def mse(self, X: np.ndarray, y: np.ndarray) -> float:
        return float(np.mean((self.predict(X) - y) ** 2))

    def rmse(self, X: np.ndarray, y: np.ndarray) -> float:
        return float(np.sqrt(self.mse(X, y)))

    def mae(self, X: np.ndarray, y: np.ndarray) -> float:
        return float(np.mean(np.abs(self.predict(X) - y)))


class LogisticRegressionGD:
    """
    Binary logistic regression trained with mini-batch gradient descent.

    Model:  ŷ = σ(θ · x)   where σ is the sigmoid function
    Loss:   Cross-entropy = -(1/m) * Σ [y log(ŷ) + (1-y) log(1-ŷ)]
    Update: θ := θ - α * ∇CE(θ)
            ∇CE(θ) = (1/m) * Σ (ŷ_i - y_i) * x_i

    Parameters
    ----------
    learning_rate : float
    n_epochs : int
    batch_size : int
    tol : float
        Early stopping on validation cross-entropy.
    class_weight : str or None
        If "balanced", weights minority class inversely proportional to frequency.
    """

    def __init__(
        self,
        learning_rate: float = 0.05,
        n_epochs: int = 500,
        batch_size: int = 32,
        tol: float = 1e-4,
        class_weight: str | None = "balanced",
    ) -> None:
        self.learning_rate = learning_rate
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self.tol = tol
        self.class_weight = class_weight

        self.theta_: np.ndarray | None = None
        self.train_losses_: list[float] = []
        self.val_losses_: list[float] = []
        self.class_weights_: dict[int, float] = {}

    def _sample_weights(self, y: np.ndarray) -> np.ndarray:
        if self.class_weight != "balanced":
            return np.ones(len(y), dtype=np.float64)
        classes, counts = np.unique(y, return_counts=True)
        total = len(y)
        w_map = {int(c): total / (len(classes) * cnt) for c, cnt in zip(classes, counts)}
        self.class_weights_ = w_map
        return np.array([w_map[int(yi)] for yi in y], dtype=np.float64)

    def _cross_entropy(
        self, X_b: np.ndarray, y: np.ndarray, weights: np.ndarray
    ) -> float:
        y_hat = _sigmoid(X_b @ self.theta_)
        eps = 1e-12
        loss = -np.mean(
            weights * (y * np.log(y_hat + eps) + (1 - y) * np.log(1 - y_hat + eps))
        )
        return float(loss)

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
    ) -> "LogisticRegressionGD":
        X_b = _add_bias(X_train)
        m, n = X_b.shape
        self.theta_ = np.zeros(n, dtype=np.float64)
        weights = self._sample_weights(y_train)

        has_val = X_val is not None and y_val is not None
        if has_val:
            X_val_b = _add_bias(X_val)
            val_weights = self._sample_weights(y_val)

        rng = np.random.default_rng(42)
        prev_val_loss = float("inf")

        for epoch in range(self.n_epochs):
            idx = rng.permutation(m)
            X_b = X_b[idx]
            y_train = y_train[idx]
            weights = weights[idx]

            for start in range(0, m, self.batch_size):
                end = start + self.batch_size
                Xb = X_b[start:end]
                yb = y_train[start:end]
                wb = weights[start:end]

                # Step 1: ŷ = σ(θ · x)
                y_hat = _sigmoid(Xb @ self.theta_)

                # Step 2: errors  e = ŷ - y
                errors = (y_hat - yb) * wb

                # Step 3: gradient  ∇CE = (1/m) * Σ e_i * x_i
                grad = (Xb.T @ errors) / len(yb)

                # Step 4: θ := θ - α * ∇CE
                self.theta_ -= self.learning_rate * grad

            train_loss = self._cross_entropy(X_b, y_train, weights)
            self.train_losses_.append(train_loss)

            if has_val:
                val_loss = self._cross_entropy(X_val_b, y_val, val_weights)
                self.val_losses_.append(val_loss)

                if prev_val_loss - val_loss < self.tol and epoch > 20:
                    break
                prev_val_loss = val_loss

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.theta_ is None:
            raise RuntimeError("Model has not been fitted yet.")
        p = _sigmoid(_add_bias(X) @ self.theta_)
        return np.column_stack([1 - p, p])

    def predict(self, X: np.ndarray) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)

    def accuracy(self, X: np.ndarray, y: np.ndarray) -> float:
        return float(np.mean(self.predict(X) == y.astype(int)))