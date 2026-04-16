"""Training pipeline returns complete metadata for checkpoint reporting."""

from pathlib import Path

from src.module6_race_predictor.synthetic_data import write_synthetic_csv
from src.module6_race_predictor.training import train_and_save


def test_train_and_save_includes_classification_metric_keys(tmp_path: Path):
    csv_p = tmp_path / "train.csv"
    write_synthetic_csv(csv_p, n_rows=500, seed=7, verbose=False)
    meta = train_and_save(csv_p, tmp_path, n_epochs=120, batch_size=32)

    for key in (
        "readiness_precision",
        "readiness_recall",
        "readiness_f1",
        "readiness_auc",
        "readiness_confusion_matrix",
        "finish_rmse_test",
        "finish_mae_test",
        "residual_std_minutes",
    ):
        assert key in meta
