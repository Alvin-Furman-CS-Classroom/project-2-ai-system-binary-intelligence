import json
from pathlib import Path
from typing import Set, Dict, Any
from datetime import datetime

# src/module/fact.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH = PROJECT_ROOT / "data" / "fact_config.json"

def _load_config() -> Dict[str, Any]:
    with _CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

CONFIG = _load_config()


def _matches_any(text: str, contains_list: list[str]) -> bool:
    return any(substr in text for substr in contains_list)


def _extract_health_facts(profile: Dict[str, Any]) -> Set[str]:
    facts = set()

    symptoms = [s.lower() for s in profile.get("symptoms", [])]

    for fact, aliases in CONFIG["symptom_aliases"].items():
        if any(alias.lower() in symptoms for alias in aliases):
            facts.add(fact)

    pain_level = str(profile.get("pain_level", "none")).lower()
    pain_map = CONFIG.get("pain_level_facts", {})
    if pain_level in pain_map:
        facts.add(pain_map[pain_level])

    return facts


def _extract_injury_facts(profile: Dict[str, Any]) -> Set[str]:
    facts = set()
    injuries = profile.get("injuries", [])

    if injuries:
        facts.add("active_injury")

    for injury in injuries:
        injury_lower = str(injury).lower()
        for rule in CONFIG["injury_mappings"]:
            if _matches_any(injury_lower, rule["contains"]):
                facts.add(rule["fact"])
                break

    if injuries and not profile.get("cleared_by_doctor", False):
        facts.add("not_cleared_by_doctor")

    return facts


def _extract_training_facts(profile: Dict[str, Any]) -> Set[str]:
    facts = set()

    experience = str(profile.get("experience_level", "beginner")).lower()
    exp_map = CONFIG["experience_level_facts"]
    if experience in exp_map:
        facts.add(exp_map[experience])

    race_date_str = profile.get("race_date")
    if race_date_str:
        try:
            race_date = datetime.fromisoformat(race_date_str.replace("Z", "+00:00"))
            today = datetime.now(race_date.tzinfo) if race_date.tzinfo else datetime.now()
            days_until = (race_date - today).days

            within_days = int(CONFIG["derived_rules"].get("race_within_days", 7))
            if 0 <= days_until <= within_days:
                facts.add("race_within_7_days")
        except (ValueError, AttributeError):
            pass

    return facts


def _extract_recovery_facts(profile: Dict[str, Any]) -> Set[str]:
    facts = set()
    
    # Direct boolean mappings
    bool_facts = [
        "hard_workout_yesterday", 
        "hard_workout_today"
    ]
    
    for fact in bool_facts:
        if profile.get(fact, False):
            facts.add(fact)
            
    # Conditional mappings
    if str(profile.get("sleep_quality", "")).lower() == "poor" or profile.get("poor_sleep", False):
        facts.add("poor_sleep")
        
    if "rest_days_this_week" in profile and profile["rest_days_this_week"] == 0:
        facts.add("zero_rest_days_this_week")
    # Also support direct flag just in case
    if profile.get("zero_rest_days_this_week", False):
        facts.add("zero_rest_days_this_week")
        
    if profile.get("days_trained_this_week", 0) >= 6:
        facts.add("six_plus_training_days")
    if profile.get("six_plus_training_days", False):
         facts.add("six_plus_training_days")

    if "rest_day_yesterday" in profile and not profile["rest_day_yesterday"]:
        facts.add("no_rest_yesterday")
    if profile.get("no_rest_yesterday", False):
        facts.add("no_rest_yesterday")
            
    # Handle recovery status
    if not profile.get("fully_recovered", True) or profile.get("not_fully_recovered", False):
        facts.add("not_fully_recovered")
        
    return facts


def _extract_environment_facts(profile: Dict[str, Any]) -> Set[str]:
    facts = set()

    weather = str(profile.get("weather", "normal")).lower()
    if weather in CONFIG["extreme_weather_values"]:
        facts.add("extreme_weather")

    if not profile.get("hydrated", True):
        facts.add("not_hydrated")

    if not profile.get("proper_footwear", True):
        facts.add("no_proper_footwear")

    return facts


def _extract_workout_facts(profile: Dict[str, Any]) -> Set[str]:
    facts = set()
    workout = profile.get("proposed_workout", {})

    workout_type = str(workout.get("type", "")).lower()
    for rule in CONFIG["workout_type_mappings"]:
        if _matches_any(workout_type, rule["contains"]):
            facts.update(rule["facts"])
            break

    terrain = str(workout.get("terrain", "")).lower()
    for rule in CONFIG["terrain_mappings"]:
        if _matches_any(terrain, rule["contains"]):
            facts.update(rule["facts"])
            break

    return facts


def _compute_derived_facts(facts: Set[str], profile: Dict[str, Any]) -> Set[str]:
    derived = set()
    rules = CONFIG.get("derived_rules", {})

    workout = profile.get("proposed_workout", {})
    distance = workout.get("distance", 0) or 0
    weekly_mileage = profile.get("weekly_mileage", 0) or 0

    ex = rules.get("excessive_distance", {})
    if ex.get("enabled", True) and "long_run" in facts and weekly_mileage > 0:
        multiplier = float(ex.get("long_run_multiplier", 1.5))
        if distance > weekly_mileage * multiplier:
            derived.add("excessive_distance")

    return derived


def get_fact_explanation(fact: str) -> str:
    return CONFIG.get("fact_explanations", {}).get(fact, f"Unknown fact: {fact}")


def profile_to_facts(profile: Dict[str, Any]) -> Set[str]:
    facts = set()
    facts.update(_extract_health_facts(profile))
    facts.update(_extract_injury_facts(profile))
    facts.update(_extract_recovery_facts(profile))
    facts.update(_extract_training_facts(profile))
    facts.update(_extract_environment_facts(profile))
    facts.update(_extract_workout_facts(profile))
    
    derived = _compute_derived_facts(facts, profile)
    facts.update(derived)
    
    return facts

# Alias for backward compatibility if needed by other modules
extract_facts = profile_to_facts
