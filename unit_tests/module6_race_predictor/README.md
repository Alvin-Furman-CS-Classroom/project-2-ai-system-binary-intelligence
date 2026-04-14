# Unit tests — `module6_race_predictor`

Mirrors `src/module6_race_predictor/`:

- **Validation:** type checks, age/days/adherence boundaries, goal distance variants, time parsing, error messages.
- **Features:** empty history, weighted pace, undated runs, grass→trail, treadmill→track bucket.
- **Synthetic:** CSV round-trip, finish time within configured clip bounds.
- **Gradient descent:** toy fits + predict-before-fit errors.
- **Training:** incomplete-bundle guard, `_readiness_test_metrics`, full `train_and_save` metadata keys on a small CSV.
- **Predictor:** smoke with `tmp_path`.

Pipeline-level coverage: `integration_tests/module6_integration/` and `unit_tests/pipeline/test_orchestrator.py`.
