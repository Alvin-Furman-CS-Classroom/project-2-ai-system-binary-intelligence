"""
Default paths and schema for the runner profile and pipeline artifacts.

Centralizes integration defaults so orchestration code avoids scattered literals.
"""

from __future__ import annotations

# JSON runner profile (planner + Module 1 block + paths)
DEFAULT_RUNNER_PROFILE_PATH = "data/runner_profile.json"
PROFILE_SCHEMA_VERSION = 1

# Q-table path (Module 5); overridden by profile paths.q_table or explicit args
DEFAULT_Q_TABLE_PATH = "data/q_table.json"

# Adherence window when merging plan vs log (days)
DEFAULT_ADHERENCE_DAYS_WINDOW = 7
