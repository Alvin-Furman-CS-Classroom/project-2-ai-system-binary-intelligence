"""
rules.py (JSON-backed)

Loads safety rules from the project-root safety_rules.json and exposes:
- ABSOLUTE_SAFETY_RULES, INJURY_TERRAIN_RULES, ...
- SAFETY_RULES (combined list)
- get_rules_by_category()
- get_rule_by_name()
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class SafetyRule:
    name: str
    conditions: List[str]
    conclusion: str
    severity: str
    explanation: str
    can_suggest_alternative: bool


# Optional constants (avoid typos)
SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_NONE = "none"


def _load_rules_from_json(path: Path) -> Dict[str, List[SafetyRule]]:
    data = json.loads(path.read_text(encoding="utf-8"))

    # Handle if data is a list (flat format) vs dict (grouped format)
    rules_by_category: Dict[str, List[SafetyRule]] = {}
    
    # Initialize implementation-defined categories
    known_categories = ["absolute", "injury", "training", "recovery", "environment"]
    for c in known_categories:
        rules_by_category[c] = []

    if isinstance(data, list):
        # Flat format: [{"category": "absolute", ...}, ...]
        for i, rule_dict in enumerate(data):
            if not isinstance(rule_dict, dict):
                continue
            
            # Extract category so it doesn't break SafetyRule constructor
            category = rule_dict.pop("category", "unknown")
            
            try:
                rule = SafetyRule(**rule_dict)
                if category not in rules_by_category:
                    rules_by_category[category] = []
                rules_by_category[category].append(rule)
            except TypeError:
                # In case of extra fields or missing fields, skip or log (ignoring for now to prevent crash)
                pass
                
    elif isinstance(data, dict):
        # Grouped format (original code expectation)
        for category, rules in data.items():
            if not isinstance(rules, list):
                continue

            converted: List[SafetyRule] = []
            for rule_dict in rules:
                if isinstance(rule_dict, dict):
                    # Remove category if present to avoid init errors
                    rule_dict.pop("category", None) 
                    converted.append(SafetyRule(**rule_dict))

            rules_by_category[category] = converted

    return rules_by_category


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_RULES_PATH = _PROJECT_ROOT / "data" / "safety_rules.json"

try:
    _rules_by_category = _load_rules_from_json(_RULES_PATH)
except Exception as e:
    raise RuntimeError(f"Failed to load safety rules JSON at: {_RULES_PATH}") from e


ABSOLUTE_SAFETY_RULES = _rules_by_category.get("absolute", [])
INJURY_TERRAIN_RULES = _rules_by_category.get("injury_terrain", [])
TRAINING_LOAD_RULES = _rules_by_category.get("training_load", [])
RECOVERY_FATIGUE_RULES = _rules_by_category.get("recovery_fatigue", [])
ENVIRONMENT_PREPARATION_RULES = _rules_by_category.get("environment_preparation", [])

SAFETY_RULES: List[SafetyRule] = (
    ABSOLUTE_SAFETY_RULES
    + INJURY_TERRAIN_RULES
    + TRAINING_LOAD_RULES
    + RECOVERY_FATIGUE_RULES
    + ENVIRONMENT_PREPARATION_RULES
)


def get_rules_by_category(category: str) -> List[SafetyRule]:
    category_map = {
        "absolute": ABSOLUTE_SAFETY_RULES,
        "injury": INJURY_TERRAIN_RULES,
        "training": TRAINING_LOAD_RULES,
        "recovery": RECOVERY_FATIGUE_RULES,
        "environment": ENVIRONMENT_PREPARATION_RULES,
    }
    return category_map.get(category, [])


def get_rule_by_name(rule_name: str) -> SafetyRule:
    for rule in SAFETY_RULES:
        if rule.name == rule_name:
            return rule
    raise ValueError(f"Rule '{rule_name}' not found in knowledge base")
