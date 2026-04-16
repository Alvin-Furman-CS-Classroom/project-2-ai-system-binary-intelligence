"""End-to-end smoke: train artifacts and predict."""

from pathlib import Path

from src.module6_race_predictor.predictor import predict_race_readiness


def test_predict_race_readiness_smoke(tmp_path: Path):
    snap = {
        "age": 35,
        "experience_level": "intermediate",
        "days_to_race": 45,
        "adherence_percent": 88,
        "history": [
            {
                "date": "2026-01-01",
                "distance": 6,
                "pace": 9.0,
                "terrain": "road",
                "sentiment": "positive",
            },
        ],
        "goal_race": {
            "distance": "marathon",
            "target_time": "4:15:00",
            "terrain": "road",
        },
    }
    out = predict_race_readiness(snap, module6_dir=tmp_path, auto_train=True)
    assert "predicted_finish" in out
    assert "readiness_score" in out
    assert len(out["recommendations"]) >= 1
