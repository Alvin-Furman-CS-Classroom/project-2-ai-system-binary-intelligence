"""
Server-side context for templates/long_run_demo.html so numbers match the real
modules (M1–M6), not placeholder copy.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from src.module1_safety_validator import validate_workout, validate_workout_detailed
from src.module1_safety_validator.rules import SAFETY_RULES
from src.module2_plan_generator.planner import generate_plan

_PROJECT = Path(__file__).resolve().parent.parent
_METADATA = _PROJECT / "data" / "module6" / "metadata.json"

# Demo runner — must match Module 1 profile shape used in tests.
_DEMO_PROFILE: dict = {
    "injuries": ["shin splints"],
    "cleared_by_doctor": True,
    "weekly_mileage": 28,
    "experience_level": "intermediate",
    "hydrated": True,
    "proper_footwear": True,
    "weather": "normal",
    "rest_days_this_week": 2,
    "days_trained_this_week": 3,
    "fully_recovered": True,
    "sleep_quality": "good",
    # Includes track so a “bad” track proposal is structurally valid; plan gen uses road+treadmill only.
    "available_terrain": ["road", "treadmill", "track"],
}


def _rule_explanation(rule_name: str) -> str:
    for r in SAFETY_RULES:
        if r.name == rule_name:
            return r.explanation
    return ""


def build_long_run_demo_context() -> dict[str, object]:
    ctx: dict[str, object] = {}

    ctx["m1_rule_count"] = len(SAFETY_RULES)

    bad_workout = {"type": "long run", "distance": 14, "terrain": "track"}
    bad = validate_workout(_DEMO_PROFILE, bad_workout)
    bad_dbg = validate_workout_detailed(_DEMO_PROFILE, bad_workout, debug=True)
    fired = (bad_dbg.get("_debug_info") or {}).get("fired_rules") or []

    ctx["m1_bad_label"] = "Proposed — rejected"
    ctx["m1_bad_title"] = f"{bad_workout['distance']:.0f} mi {bad_workout['terrain']} long run"
    ctx["m1_bad_sub"] = (
        f"{len(fired)} rule violation(s) fired" if fired else "Marked unsafe by validator"
    )
    ctx["m1_bad_rules"] = [
        {"name": name, "explanation": _rule_explanation(name)} for name in fired
    ]
    alt = bad.get("alternative") or {}
    ctx["m1_good_label"] = "Safe alternative"
    if alt:
        ctx["m1_good_title"] = (
            f"{float(alt.get('distance', 0)):.0f} mi {alt.get('terrain', '')} {alt.get('type', 'run')}"
        )
        ctx["m1_good_sub"] = "Suggested by Module 1 alternative generator"
    else:
        ctx["m1_good_title"] = "11 mi treadmill long run"
        ctx["m1_good_sub"] = "Example safe session on soft surface"

    pass_a = validate_workout_detailed(
        _DEMO_PROFILE, {"type": "easy run", "distance": 5, "terrain": "treadmill"}, debug=True
    )
    pass_b = validate_workout_detailed(
        _DEMO_PROFILE, {"type": "long run", "distance": 11, "terrain": "treadmill"}, debug=True
    )
    ctx["m1_pass_rows"] = [
        {
            "title": "easy run 5 mi · treadmill",
            "ok": bool(pass_a.get("safe")),
        },
        {
            "title": "long run 11 mi · treadmill",
            "ok": bool(pass_b.get("safe")),
        },
    ]

    def _vf(workout: dict, profile: dict) -> dict:
        return validate_workout(profile, workout)

    race = date.today() + timedelta(days=120)
    plan_cfg = {
        "goal": "complete marathon",
        "race_date": race.isoformat(),
        "days_per_week": 4,
        "current_weekly_miles": 28,
        "experience": "intermediate",
        "available_terrain": ["road", "treadmill"],
    }
    plan_profile = {**_DEMO_PROFILE, "available_terrain": ["road", "treadmill"]}
    plan = generate_plan(plan_cfg, validate_fn=_vf, runner_profile=plan_profile)

    if plan.get("success"):
        stats = plan.get("search_stats") or {}
        ctx["m2_nodes"] = stats.get("nodes_explored")
        ctx["m2_generated"] = stats.get("nodes_generated")
        ctx["m2_penalty"] = plan.get("total_penalty")
        ctx["m2_weeks"] = plan.get("total_weeks")
        ctx["m2_algorithm"] = stats.get("algorithm", "a_star")
        raw_weeks = plan.get("plan") or []

        def _pill_type(wt: str) -> str:
            wtl = (wt or "").lower()
            if "long" in wtl:
                return "long"
            if "interval" in wtl:
                return "interval"
            if "tempo" in wtl:
                return "tempo"
            return "easy"

        plan_js: list[dict[str, object]] = []
        for wk in raw_weeks:
            wouts = wk.get("workouts") or []
            pills = [
                f"{o.get('type', 'run')} {float(o.get('distance', 0)):.1f} mi · {o.get('terrain', '')}"
                for o in wouts
            ]
            types = [_pill_type(str(o.get("type", ""))) for o in wouts]
            plan_js.append(
                {
                    "w": f"Week {wk.get('week', '?')}",
                    "miles": round(float(wk.get("weekly_total", wk.get("total_miles", 0))), 1),
                    "pills": pills,
                    "types": types,
                }
            )
        ctx["m2_plan_js"] = plan_js
    else:
        ctx["m2_nodes"] = None
        ctx["m2_generated"] = None
        ctx["m2_penalty"] = None
        ctx["m2_weeks"] = None
        ctx["m2_algorithm"] = None
        ctx["m2_plan_error"] = ", ".join(plan.get("errors") or []) or "Plan generation failed"
        ctx["m2_plan_js"] = []

    ctx["m5_alpha"] = 0.3
    ctx["m5_gamma"] = 0.9
    ctx["m5_state_dims"] = "fitness · fatigue · terrain streak · workout category · adherence (216 states)"

    if _METADATA.exists():
        ctx["m6_meta"] = json.loads(_METADATA.read_text(encoding="utf-8"))
    else:
        ctx["m6_meta"] = None

    return ctx
