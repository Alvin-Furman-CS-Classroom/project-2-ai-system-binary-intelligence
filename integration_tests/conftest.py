"""
Pytest conftest for integration tests.

Ensures the repository root is on sys.path so that
``from src.module1_safety_validator import ...`` and
``from src.module2_plan_generator import ...`` work when running
pytest from any directory.
"""

import sys
from pathlib import Path

# integration_tests/conftest.py -> repo root = parent of integration_tests
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
