"""
Controller for Module 5 – Adaptive Progression demo routes.
"""

from fastapi import Request
from fastapi.templating import Jinja2Templates

from src.module5_adaptive_progression.adaptor import adapt_progression_detailed

templates = Jinja2Templates(directory="templates")

DEMO_SCENARIOS = [
    {
        "label": "Consistent runner ready to progress",
        "context": {
            "workout_type": "easy run",
            "terrain": "road",
            "fatigue_score": 0.2,
            "history": [
                {"distance": 5.0, "pace": 9.5, "terrain": "road", "sentiment": "great"},
                {"distance": 5.2, "pace": 9.4, "terrain": "trail", "sentiment": "good"},
                {"distance": 5.5, "pace": 9.3, "terrain": "road", "sentiment": "strong"},
            ],
            "motivation": {
                "current_streak": 14,
                "recent_sentiments": ["great", "good", "strong"],
                "terrain_last_week": ["road", "trail", "road"],
                "adherence_percent": 95.0,
                "days_to_race": 21,
            },
        },
    },
    {
        "label": "Fatigued runner needing a recovery week",
        "context": {
            "workout_type": "recovery run",
            "terrain": "road",
            "fatigue_score": 0.8,
            "history": [
                {"distance": 8.0, "pace": 8.8, "terrain": "road", "sentiment": "exhausted"},
                {"distance": 7.5, "pace": 9.0, "terrain": "road", "sentiment": "struggled"},
                {"distance": 6.0, "pace": 9.5, "terrain": "treadmill", "sentiment": "bad"},
            ],
            "motivation": {
                "current_streak": 5,
                "recent_sentiments": ["tired", "struggled", "bad"],
                "terrain_last_week": ["road", "road", "treadmill"],
                "adherence_percent": 88.0,
                "days_to_race": 35,
            },
        },
    },
    {
        "label": "Cold-start – brand new runner",
        "context": {
            "workout_type": "easy run",
            "terrain": "trail",
            "fatigue_score": 0.3,
            "history": [],
        },
    },
    {
        "label": "Low-adherence runner — rebuilding consistency",
        "context": {
            "workout_type": "easy run",
            "terrain": "treadmill",
            "fatigue_score": 0.45,
            "history": [
                {"distance": 3.0, "pace": 11.0, "terrain": "treadmill", "sentiment": "ok"},
                {"distance": 2.5, "pace": 11.5, "terrain": "treadmill", "sentiment": "fine"},
            ],
            "motivation": {
                "current_streak": 2,
                "recent_sentiments": ["ok", "fine", "tired"],
                "terrain_last_week": ["treadmill", "treadmill"],
                "adherence_percent": 58.0,
                "days_to_race": 90,
            },
        },
    },
]


def show_demo(request: Request):
    """GET /progression/demo — run all hardcoded scenarios."""
    scenario_results = []
    for scenario in DEMO_SCENARIOS:
        result = adapt_progression_detailed(scenario["context"])
        scenario_results.append({
            "label": scenario["label"],
            "context": scenario["context"],
            "result": result,
        })

    return templates.TemplateResponse(
        "adaptive_demo.html",
        {"request": request, "scenario_results": scenario_results},
    )


def handle_custom(request: Request, form_data: dict):
    """POST /progression/custom — run a single user-supplied context."""
    # Build history from up to 3 run entries
    history = []
    for i in range(1, 11):
        dist_raw = form_data.get(f"distance{i}", "").strip()
        if not dist_raw:
            continue
        try:
            history.append({
                "distance": float(dist_raw),
                "pace":     float(form_data.get(f"pace{i}", "10.0")),
                "terrain":  form_data.get(f"terrain{i}", "road").strip().lower(),
                "sentiment": form_data.get(f"sentiment{i}", "neutral").strip().lower(),
            })
        except ValueError:
            pass

    context = {
        "workout_type":  form_data.get("workout_type", "easy run").strip().lower(),
        "terrain":       form_data.get("terrain", "road").strip().lower(),
        "fatigue_score": float(form_data.get("fatigue_score", 0.3)),
        "history":       history,
    }

    # Count total run slots submitted (including blank) to auto-calc adherence
    total_slots = sum(1 for i in range(1, 11) if f"distance{i}" in form_data)
    filled_slots = len(history)
    auto_adherence = round(filled_slots / total_slots * 100, 1) if total_slots else 100.0

    # Build motivation block — use explicit adherence if provided, else auto-calculate
    adh_raw = form_data.get("adherence_percent", "").strip()
    streak_raw = form_data.get("current_streak", "").strip()
    race_raw = form_data.get("days_to_race", "").strip()

    # Derive terrain_last_week and recent_sentiments from history; fall back to safe defaults
    terrain_last_week = [r["terrain"] for r in history] or [context["terrain"]]
    recent_sentiments = [r["sentiment"] for r in history] or ["neutral"]

    context["motivation"] = {
        "adherence_percent": float(adh_raw) if adh_raw else auto_adherence,
        "current_streak":    int(streak_raw) if streak_raw else 0,
        "days_to_race":      int(race_raw) if race_raw else 0,
        "terrain_last_week": terrain_last_week,
        "recent_sentiments": recent_sentiments,
    }

    result = adapt_progression_detailed(context)

    return templates.TemplateResponse(
        "adaptive_result.html",
        {"request": request, "context": context, "result": result},
    )
