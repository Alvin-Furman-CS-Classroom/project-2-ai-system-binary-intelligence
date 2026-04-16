# Module Rubric Report — Module 6 (Race Readiness Predictor)

**Checkpoint:** 5 (Module 6 — supervised learning).

**Rubric:** [AI System Project Rubric](https://csc-343.path.app/projects/project-2-ai-system/ai-system.rubric.md)

**Report run:** 2026-04-16 — checkpoint preparation re-run (full `pytest` + rubric text synced to current `training.py`).

**Test status:** **945** tests collected, full `pytest` run passing (`PYTHONPATH=.` from repo root).

---

## Summary

Module 6 provides from-scratch gradient-descent linear and logistic models on scaled tabular features, honest test-set metrics (regression + precision/recall/F1/AUC/confusion matrix, with safe AUC handling), and `predict_race_readiness` output suitable for demos. Calibration against `data/CalibrationData.csv` is documented via `calibrate_from_real_data.py`. Unit tests cover Module 6 directly; `integration_tests/module6_integration/test_module6_pipeline.py` exercises `pipeline_predict_race_readiness` with an isolated `module6_dir`.

---

## Part 1: Source Code Review (`src/module6_race_predictor/`)

### 1.1 Functionality — **Suggested: 8 / 8**

| Area | Evidence |
| ---- | -------- |
| Inference | `predict_race_readiness`: validation → optional artifact ensure → scale → linear + logistic → CI from test residual std. |
| Training | `train_and_save`: 70/15/15 split; test metrics include precision/recall/F1/AUC/confusion matrix via `_readiness_test_metrics` (AUC `None` when undefined). |
| Artifacts | `ensure_training_artifacts`; pickle bundle validated in `load_models` (required keys enforced). |
| Pipeline | `pipeline_predict_race_readiness` builds snapshot from profile + history (`src/pipeline/orchestrator.py`). |

### 1.2 Code Elegance and Quality — **Suggested: 7 / 7**

See `checkpoint_5_elegance_report.md`: average **4.0** on the 8 elegance criteria (helpers, constants, error handling).

### 1.3 Documentation — **Suggested: 4 / 4**

| Strengths |
| --------- |
| Package docstring lists **public API** and points to `__all__` (`__init__.py`). |
| `train_and_save` documents split and test-set residual behavior. |
| README: Module 6 usage, gradient descent + feature scaling, calibration CSV, stale-artifact note. |

### 1.4 I/O Clarity — **Suggested: 3 / 3**

- **Inputs:** Runner snapshot (`age`, `goal_race`, `history`, optional experience/days/adherence).
- **Outputs:** Finish time (string + minutes), CI, `readiness_score`, `recommendations`.
- **Metrics:** Pickle `metadata` / `train_and_save` return dict includes finish test RMSE, residual std, readiness precision/recall/F1/AUC (or `None`), confusion matrix.

### 1.5 Topic Engagement (Supervised Learning) — **Suggested: 5 / 5**

- Mini-batch **gradient descent** implementations with validation early stopping.
- **Train/val/test** and **standardization** fit on training data only.
- **Calibration** from real runners; explicit **pace** feature aligned with label generation.
- **Rich classification metrics** on the test set.

---

## Part 2: Testing Review

### 2.1 Test Coverage and Design — **Suggested: 6 / 6**

| Layer | Files |
| ----- | ----- |
| Unit | `unit_tests/module6_race_predictor/` — validation (types, age 16–80, experience, goal variants, time parsing, days/adherence edges), feature aggregation (undated runs, grass/treadmill), synthetic clip bounds, GD smoke + unfitted predict errors, readiness metrics, training metadata keys, bundle guard, predictor smoke. |
| Integration | `integration_tests/module6_integration/test_module6_pipeline.py` — pipeline + isolated `module6_dir`. |
| Pipeline smoke | `unit_tests/pipeline/test_orchestrator.py` (race readiness). |

Core paths, **edge cases**, and **error conditions** for Module 6 are explicitly covered.

### 2.2 Test Quality and Correctness — **Suggested: 5 / 5**

- Assertions target behavior and shapes; 945 tests passing in last full run.

### 2.3 Test Documentation and Organization — **Suggested: 4 / 4**

- Parallel `unit_tests/module6_race_predictor/` layout; **`unit_tests/module6_race_predictor/README.md`** describes scope; descriptive file names (`test_m6_input_validation.py`, etc.).

---

## Part 3: GitHub Practices

**Not scored in-repo**—verify both teammates have substantive commits for Checkpoint 5 (participation gate).

---

## Module explanation (demo quick reference)

### Input

Dict with `age`, `goal_race` (`distance`, `target_time`, `terrain`), optional `experience_level`, `days_to_race`, `adherence_percent`, and `history` (runs with `distance`, `pace` / `pace_minutes`, optional `date`, `terrain`, `sentiment`).

### Output

`predicted_finish`, `confidence_interval`, `readiness_score`, `recommendations`, plus minute-level fields for reports.

**Downstream:** Terminal user-facing insight; pipeline wraps it for full-system demo.

### AI concepts

Supervised learning (linear + logistic regression via GD), train/val/test, feature scaling, real-data-informed synthetic labels, classification metrics on held-out data.

---

## Presentation checklist (`checkpoint_preparation.md`)

- [ ] Data-flow slide: snapshot → features → scaler → two models → outputs + training metadata (pickle / `train_and_save` return dict).
- [ ] Calibration slide (volume + pace).
- [ ] Screenshot or paste: training log line and/or sample metadata keys (AUC, F1, confusion matrix).

---

## Action items before submission

1. Run `pytest` (945 tests) and keep a log/screenshot if the course asks.
2. Re-run training if you need a fresh `data/module6/module6_models.pkl` for the appendix (`train_and_save` or `ensure_training_artifacts`).
3. Confirm **both** teammates have meaningful git history for this checkpoint.
4. Finish slides / in-person explanation using sections above.
