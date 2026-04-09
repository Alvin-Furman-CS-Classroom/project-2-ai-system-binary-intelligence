"""
Module 6 — Race Readiness Predictor (supervised learning).

Trains on synthetic tabular data (linear regression for finish time,
logistic regression for meeting goal). First call can auto-generate data
and fit models under ``data/module6/``.

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

from .input_validation import ValidationError
from .predictor import predict_race_readiness
from .synthetic_data import generate_dataset, write_synthetic_csv
from .training import ensure_training_artifacts, train_and_save

__all__ = [
    "ValidationError",
    "predict_race_readiness",
    "generate_dataset",
    "write_synthetic_csv",
    "ensure_training_artifacts",
    "train_and_save",
]
