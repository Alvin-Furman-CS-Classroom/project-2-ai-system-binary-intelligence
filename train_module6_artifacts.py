#!/usr/bin/env python3
"""
Regenerate `data/module6/synthetic_race_training.csv`, retrain models, and write
`module6_models.pkl` + `metadata.json`.

From the repository root:

    python3 train_module6_artifacts.py

Requires NumPy (`pip install -r requirements.txt`). If imports fail, use the same
Python you use for `pytest` (e.g. `which python3` after activating your venv).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.module6_race_predictor.synthetic_data import write_synthetic_csv
from src.module6_race_predictor.training import train_and_save


def main() -> None:
    base = ROOT / "data" / "module6"
    csv_path = base / "synthetic_race_training.csv"
    write_synthetic_csv(csv_path, n_rows=2000, seed=42, verbose=True)
    train_and_save(csv_path, base, n_epochs=600, batch_size=64)
    print("[train_module6_artifacts] Done.")


if __name__ == "__main__":
    main()
