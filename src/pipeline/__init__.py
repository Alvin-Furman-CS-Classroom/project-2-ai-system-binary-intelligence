"""
Cross-module pipeline (orchestration). Not part of any single course module — it wires
modules together using ``data/runner_profile.json`` and optional helpers.

Prefer importing from this package::

    from src.pipeline import load_runner_profile, pipeline_generate_plan
"""

from .orchestrator import *  # noqa: F403
from .orchestrator import __all__ as __all__
