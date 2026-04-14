# Unit tests — `pipeline`

Covers ``load_runner_profile`` / ``save_runner_profile`` (including missing file and invalid JSON), schema version, Module 5 context building, plan adherence helpers, Module 6 ``pipeline_predict_race_readiness`` smoke, and exported defaults (e.g. ``DEFAULT_ADHERENCE_DAYS_WINDOW``).

Integration-style behavior for multi-module flows lives under ``integration_tests/``.
