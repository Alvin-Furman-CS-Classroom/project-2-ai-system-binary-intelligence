"""Bundle loading validation."""

import pickle
from pathlib import Path

import pytest

from src.module6_race_predictor.training import load_models


def test_load_models_rejects_incomplete_bundle(tmp_path: Path):
    bad = tmp_path / "module6_models.pkl"
    with open(bad, "wb") as f:
        pickle.dump({"finish": None}, f)
    with pytest.raises(ValueError, match="missing keys"):
        load_models(tmp_path)
