from typing import Any, Dict, List, Optional
from src.module1_safety_validator.validator import (
    validate_workout,
    validate_workout_detailed,
    quick_validate,
    batch_validate,
)

import re

_IGNORED_VALUES = {"no", "none", "n/a", "na", "nil", "nope", "nothing", "not applicable", ""}
_NO_INJURY_PATTERN = re.compile(
    r"\b(no injur|don'?t have|have no|not injured|no issues|nothing wrong|injury.?free)\b",
    re.IGNORECASE,
)


def _clean_string_list(items: List[str]) -> List[str]:
    """Remove entries like 'no', 'none', 'n/a', or natural-language 'no injury' phrases."""
    return [
        i for i in items
        if i.strip().lower() not in _IGNORED_VALUES
        and not _NO_INJURY_PATTERN.search(i)
    ]


def _apply_defaults(profile: Dict[str, Any]) -> Dict[str, Any]:
    defaults = {
        "symptoms": [],
        "pain_level": "none",
        "cleared_by_doctor": False,
        "fully_recovered": True,
        "sleep_quality": "good",
        "days_trained_this_week": 3,
        "hard_workout_yesterday": False,
        "experience_level": "intermediate",
        "race_date": None,
        "weather": "normal",
        "hydrated": True,
        "proper_footwear": True,
    }
    for k, v in defaults.items():
        profile.setdefault(k, v)

    # Sanitise list fields so that "No" / "None" are not treated as real entries
    for key in ("injuries", "symptoms"):
        if key in profile and isinstance(profile[key], list):
            profile[key] = _clean_string_list(profile[key])

    return profile


def run_validate(
    runner_profile: Dict[str, Any],
    proposed_workout: Optional[Dict[str, Any]],
    debug: bool = False,
):
    runner_profile = _apply_defaults(runner_profile)
    if debug:
        return validate_workout_detailed(runner_profile, proposed_workout, debug=True)
    return validate_workout(runner_profile, proposed_workout)


def run_batch_validate(
    runner_profile: Dict[str, Any],
    proposed_workouts: List[Dict[str, Any]],
    debug: bool = False,
):
    runner_profile = _apply_defaults(runner_profile)

    if debug:
        return [
            validate_workout_detailed(runner_profile, w, debug=True)
            for w in proposed_workouts
        ]

    return batch_validate(runner_profile, proposed_workouts)


def run_quick_validate(
    injuries: List[str],
    workout_type: str,
    distance: float,
    terrain: str,
    weekly_mileage: float,
) -> bool:
    return quick_validate(
        injuries=injuries,
        workout_type=workout_type,
        distance=distance,
        terrain=terrain,
        weekly_mileage=weekly_mileage,
    )
