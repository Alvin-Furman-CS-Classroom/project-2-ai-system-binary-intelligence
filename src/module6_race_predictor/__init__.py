"""
Module 6 — Race Readiness Predictor (supervised learning).

Trains on synthetic tabular data using from-scratch gradient descent:
  - LinearRegressionGD  for finish time prediction (MSE loss)
  - LogisticRegressionGD for met_goal classification (cross-entropy loss)

**Public API** (see ``__all__``): ``predict_race_readiness``, ``ensure_training_artifacts``,
``train_and_save``, ``generate_dataset``, ``write_synthetic_csv``, ``LinearRegressionGD``,
``LogisticRegressionGD``, ``ValidationError``, ``DEFAULT_MODULE6_DATA_DIR``.

Example
-------
from src.module6_race_predictor import predict_race_readiness

out = predict_race_readiness({
    "age": 32,
    "experience_level": "intermediate",
    "days_to_race": 45,
    "adherence_percent": 88,
    "history": [
        {"date": "2026-01-01", "distance": 6, "pace": 9.2, "terrain": "road", "sentiment": "positive"},
        {"date": "2026-01-03", "distance": 8, "pace": 9.0, "terrain": "trail", "sentiment": "neutral"},
    ],
    "goal_race": {
        "distance": "marathon",
        "target_time": "4:15:00",
        "terrain": "road",
    },
})
# predicted_finish, confidence_interval, readiness_score, recommendations
"""

from .constants import DEFAULT_MODULE6_DATA_DIR
from .gradient_descent import LinearRegressionGD, LogisticRegressionGD
from .input_validation import ValidationError
from .predictor import predict_race_readiness
from .synthetic_data import generate_dataset, write_synthetic_csv
from .training import ensure_training_artifacts, train_and_save

__all__ = [
    "DEFAULT_MODULE6_DATA_DIR",
    "LinearRegressionGD",
    "LogisticRegressionGD",
    "ValidationError",
    "predict_race_readiness",
    "generate_dataset",
    "write_synthetic_csv",
    "ensure_training_artifacts",
    "train_and_save",
]