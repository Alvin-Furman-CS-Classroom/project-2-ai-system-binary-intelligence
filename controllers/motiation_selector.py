# src/module4_motivation_selector/controller.py

from datetime import date
from fastapi import Request
from app_templates import templates

from src.module4_motivation_selector.selector import select_motivation_strategy_detailed

# The 4 hardcoded demo scenarios (mirrors demo.py's SCENARIOS)
DEMO_SCENARIOS = [
    {
        "label": "Engaged runner approaching race day",
        "context": {
            "current_streak": 18,
            "recent_sentiments": ["great", "good", "strong"],
            "terrain_last_week": ["road", "track", "trail"],
            "adherence_percent": 95.0,
            "days_to_race": 14,
        },
    },
    {
        "label": "Bored runner on monotonous terrain",
        "context": {
            "current_streak": 10,
            "recent_sentiments": ["ok", "fine", "neutral"],
            "terrain_last_week": ["treadmill", "treadmill", "treadmill"],
            "adherence_percent": 80.0,
            "days_to_race": 45,
        },
    },
    {
        "label": "Burnout risk — struggling with high load",
        "context": {
            "current_streak": 5,
            "recent_sentiments": ["tired", "struggled", "bad"],
            "terrain_last_week": ["road", "track"],
            "adherence_percent": 92.0,
            "days_to_race": 30,
        },
    },
    {
        "label": "Frazzled runner far from race",
        "context": {
            "current_streak": 3,
            "recent_sentiments": ["ok", "tired", "neutral"],
            "terrain_last_week": ["road", "road"],
            "adherence_percent": 65.0,
            "days_to_race": 90,
        },
    },
]


def _bar(score: float, max_score: float = 6.0, width: int = 20) -> str:
    filled = int(round(max(0.0, score) / max_score * width))
    return "[" + "#" * filled + "." * (width - filled) + f"] {score:+.2f}"


def show_demo(request: Request):
    """GET /motivation/demo — run all hardcoded scenarios and display results."""
    scenario_results = []

    for scenario in DEMO_SCENARIOS:
        result = select_motivation_strategy_detailed(scenario["context"])

        # Build score rows with bar + selected marker (mirrors demo.py output)
        score_rows = [
            {
                "strategy": strategy,
                "bar": _bar(score),
                "selected": strategy == result["strategy"],
            }
            for strategy, score in sorted(result["scores"].items(), key=lambda x: -x[1])
        ]

        scenario_results.append({
            "label": scenario["label"],
            "context": scenario["context"],
            "inferred_state": result["inferred_state"],
            "strategy": result["strategy"],
            "message_tone": result["message_tone"],
            "score_rows": score_rows,
            "reasoning": result["reasoning"],
        })

    return templates.TemplateResponse(
        "motivation_demo.html",
        {
            "request": request,
            "scenario_results": scenario_results,
        },
    )


def _score_metrics(scores: dict, best: str, max_score: float = 6.0) -> dict:
    """Compute display metrics from raw strategy scores."""
    sorted_scores = sorted(scores.values(), reverse=True)
    best_score = scores.get(best, 0.0)
    second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0.0
    margin = best_score - second_score
    confidence_pct = round(min(100.0, max(0.0, best_score / max_score * 100)), 1)
    return {
        "best_score": round(best_score, 2),
        "second_score": round(second_score, 2),
        "margin": round(margin, 2),
        "confidence_pct": confidence_pct,
    }


def handle_custom(request: Request, form_data: dict):
    """POST /motivation/custom — run a single user-supplied context."""
    # Parse multi-value fields from form
    sentiments_raw = form_data.get("recent_sentiments", "")
    terrain_raw = form_data.get("terrain_last_week", "")

    context = {
        "current_streak": int(form_data.get("current_streak", 0)),
        "recent_sentiments": [s.strip() for s in sentiments_raw.split(",") if s.strip()],
        "terrain_last_week": [t.strip() for t in terrain_raw.split(",") if t.strip()],
        "adherence_percent": float(form_data.get("adherence_percent", 80.0)),
        "days_to_race": int(form_data.get("days_to_race", 30)),
    }

    result = select_motivation_strategy_detailed(context)
    MAX_SCORE = 6.0

    score_rows = [
        {
            "strategy": strategy,
            "bar": _bar(score),
            "score": round(score, 2),
            "score_pct": round(min(100.0, max(0.0, score / MAX_SCORE * 100)), 1),
            "selected": strategy == result["strategy"],
        }
        for strategy, score in sorted(result["scores"].items(), key=lambda x: -x[1])
    ]

    metrics = _score_metrics(result["scores"], result["strategy"], MAX_SCORE)

    return templates.TemplateResponse(
        "motivation_result.html",
        {
            "request": request,
            "context": context,
            "inferred_state": result["inferred_state"],
            "strategy": result["strategy"],
            "message_tone": result["message_tone"],
            "score_rows": score_rows,
            "reasoning": result["reasoning"],
            "metrics": metrics,
        },
    )