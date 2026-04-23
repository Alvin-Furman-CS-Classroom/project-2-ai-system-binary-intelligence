"""
Controller for Module 6 – Race Readiness & Finish-Time Predictor demo routes.
"""

from fastapi import Request
from fastapi.templating import Jinja2Templates

from src.module6_race_predictor.predictor import predict_race_readiness
from src.module6_race_predictor.charts import make_interval_chart_b64

templates = Jinja2Templates(directory="templates")

DEMO_SCENARIOS = [
    {
        "label": "Beginner – Road Marathon, 5:00 goal",
        "snapshot": {
            "age": 28,
            "experience_level": "beginner",
            "days_to_race": 56,
            "adherence_percent": 65,
            "goal_race": {"distance": "marathon", "target_time": "5:00:00", "terrain": "road"},
            "history": [
                {"distance_miles": 4.0,  "pace_minutes": 11.5, "terrain": "road",  "sentiment": "positive"},
                {"distance_miles": 3.5,  "pace_minutes": 12.0, "terrain": "road",  "sentiment": "neutral"},
                {"distance_miles": 6.0,  "pace_minutes": 11.8, "terrain": "road",  "sentiment": "negative"},
                {"distance_miles": 5.0,  "pace_minutes": 11.5, "terrain": "road",  "sentiment": "neutral"},
                {"distance_miles": 8.0,  "pace_minutes": 12.2, "terrain": "road",  "sentiment": "positive"},
                {"distance_miles": 3.0,  "pace_minutes": 12.5, "terrain": "road",  "sentiment": "negative"},
                {"distance_miles": 10.0, "pace_minutes": 12.0, "terrain": "road",  "sentiment": "neutral"},
                {"distance_miles": 4.0,  "pace_minutes": 11.8, "terrain": "road",  "sentiment": "negative"},
                {"distance_miles": 12.0, "pace_minutes": 12.1, "terrain": "road",  "sentiment": "neutral"},
                {"distance_miles": 5.0,  "pace_minutes": 11.6, "terrain": "road",  "sentiment": "positive"},
            ],
        },
    },
    {
        "label": "Intermediate – Road Marathon, 3:55 goal",
        "snapshot": {
            "age": 35,
            "experience_level": "intermediate",
            "days_to_race": 42,
            "adherence_percent": 82,
            "goal_race": {"distance": "marathon", "target_time": "3:55:00", "terrain": "road"},
            "history": [
                {"distance_miles": 8.0,  "pace_minutes": 9.2,  "terrain": "road",  "sentiment": "positive"},
                {"distance_miles": 6.0,  "pace_minutes": 9.5,  "terrain": "road",  "sentiment": "neutral"},
                {"distance_miles": 14.0, "pace_minutes": 9.8,  "terrain": "road",  "sentiment": "positive"},
                {"distance_miles": 10.0, "pace_minutes": 9.3,  "terrain": "road",  "sentiment": "positive"},
                {"distance_miles": 6.0,  "pace_minutes": 9.6,  "terrain": "trail", "sentiment": "neutral"},
                {"distance_miles": 18.0, "pace_minutes": 10.0, "terrain": "road",  "sentiment": "neutral"},
                {"distance_miles": 7.0,  "pace_minutes": 9.4,  "terrain": "road",  "sentiment": "positive"},
                {"distance_miles": 12.0, "pace_minutes": 9.5,  "terrain": "road",  "sentiment": "neutral"},
                {"distance_miles": 20.0, "pace_minutes": 10.2, "terrain": "road",  "sentiment": "negative"},
                {"distance_miles": 8.0,  "pace_minutes": 9.1,  "terrain": "road",  "sentiment": "positive"},
                {"distance_miles": 14.0, "pace_minutes": 9.7,  "terrain": "road",  "sentiment": "neutral"},
                {"distance_miles": 22.0, "pace_minutes": 10.3, "terrain": "road",  "sentiment": "positive"},
            ],
        },
    },
    {
        "label": "Advanced – Trail Marathon, 3:10 goal",
        "snapshot": {
            "age": 42,
            "experience_level": "advanced",
            "days_to_race": 28,
            "adherence_percent": 93,
            "goal_race": {"distance": "marathon", "target_time": "3:10:00", "terrain": "trail"},
            "history": [
                {"distance_miles": 12.0, "pace_minutes": 7.8,  "terrain": "trail", "sentiment": "positive"},
                {"distance_miles": 10.0, "pace_minutes": 7.5,  "terrain": "road",  "sentiment": "positive"},
                {"distance_miles": 20.0, "pace_minutes": 8.5,  "terrain": "trail", "sentiment": "positive"},
                {"distance_miles": 14.0, "pace_minutes": 7.9,  "terrain": "trail", "sentiment": "neutral"},
                {"distance_miles": 8.0,  "pace_minutes": 7.4,  "terrain": "road",  "sentiment": "positive"},
                {"distance_miles": 22.0, "pace_minutes": 8.6,  "terrain": "trail", "sentiment": "neutral"},
                {"distance_miles": 10.0, "pace_minutes": 7.6,  "terrain": "trail", "sentiment": "positive"},
                {"distance_miles": 20.0, "pace_minutes": 8.4,  "terrain": "trail", "sentiment": "positive"},
                {"distance_miles": 16.0, "pace_minutes": 8.0,  "terrain": "trail", "sentiment": "neutral"},
                {"distance_miles": 12.0, "pace_minutes": 7.7,  "terrain": "road",  "sentiment": "neutral"},
                {"distance_miles": 24.0, "pace_minutes": 8.7,  "terrain": "trail", "sentiment": "neutral"},
                {"distance_miles": 10.0, "pace_minutes": 7.5,  "terrain": "trail", "sentiment": "positive"},
            ],
        },
    },
    {
        "label": "Half-Marathon Specialist – Road, 1:45 goal",
        "snapshot": {
            "age": 30,
            "experience_level": "intermediate",
            "days_to_race": 35,
            "adherence_percent": 88,
            "goal_race": {"distance": "half marathon", "target_time": "1:45:00", "terrain": "road"},
            "history": [
                {"distance_miles": 6.0,  "pace_minutes": 8.0, "terrain": "road", "sentiment": "positive"},
                {"distance_miles": 4.0,  "pace_minutes": 7.8, "terrain": "road", "sentiment": "positive"},
                {"distance_miles": 10.0, "pace_minutes": 8.5, "terrain": "road", "sentiment": "neutral"},
                {"distance_miles": 5.0,  "pace_minutes": 7.9, "terrain": "road", "sentiment": "positive"},
                {"distance_miles": 12.0, "pace_minutes": 8.7, "terrain": "road", "sentiment": "neutral"},
                {"distance_miles": 6.0,  "pace_minutes": 8.1, "terrain": "road", "sentiment": "positive"},
                {"distance_miles": 8.0,  "pace_minutes": 8.2, "terrain": "road", "sentiment": "neutral"},
                {"distance_miles": 13.1, "pace_minutes": 8.6, "terrain": "road", "sentiment": "positive"},
            ],
        },
    },
    {
        "label": "5K Runner – Road, 22:00 goal",
        "snapshot": {
            "age": 24,
            "experience_level": "intermediate",
            "days_to_race": 21,
            "adherence_percent": 90,
            "goal_race": {"distance": "5k", "target_time": "0:22:00", "terrain": "road"},
            "history": [
                {"distance_miles": 3.0, "pace_minutes": 7.2, "terrain": "road", "sentiment": "positive"},
                {"distance_miles": 4.0, "pace_minutes": 7.5, "terrain": "road", "sentiment": "neutral"},
                {"distance_miles": 2.0, "pace_minutes": 6.9, "terrain": "road", "sentiment": "positive"},
                {"distance_miles": 5.0, "pace_minutes": 7.8, "terrain": "road", "sentiment": "neutral"},
                {"distance_miles": 3.0, "pace_minutes": 7.1, "terrain": "road", "sentiment": "positive"},
                {"distance_miles": 4.0, "pace_minutes": 7.4, "terrain": "road", "sentiment": "neutral"},
            ],
        },
    },
    {
        "label": "10K Runner – Road, 48:00 goal",
        "snapshot": {
            "age": 31,
            "experience_level": "intermediate",
            "days_to_race": 28,
            "adherence_percent": 85,
            "goal_race": {"distance": "10k", "target_time": "0:48:00", "terrain": "road"},
            "history": [
                {"distance_miles": 4.0, "pace_minutes": 8.0, "terrain": "road", "sentiment": "positive"},
                {"distance_miles": 6.0, "pace_minutes": 8.3, "terrain": "road", "sentiment": "neutral"},
                {"distance_miles": 3.5, "pace_minutes": 7.8, "terrain": "road", "sentiment": "positive"},
                {"distance_miles": 8.0, "pace_minutes": 8.5, "terrain": "road", "sentiment": "neutral"},
                {"distance_miles": 4.0, "pace_minutes": 8.1, "terrain": "road", "sentiment": "neutral"},
                {"distance_miles": 6.0, "pace_minutes": 8.2, "terrain": "road", "sentiment": "positive"},
                {"distance_miles": 5.0, "pace_minutes": 8.0, "terrain": "road", "sentiment": "neutral"},
            ],
        },
    },
]


def show_demo(request: Request):
    """GET /race/demo — run all hardcoded profiles."""
    scenario_results = []
    for scenario in DEMO_SCENARIOS:
        result = predict_race_readiness(scenario["snapshot"], auto_train=True)
        scenario_results.append({
            "label": scenario["label"],
            "snapshot": scenario["snapshot"],
            "result": result,
        })

    return templates.TemplateResponse(
        "race_demo.html",
        {"request": request, "scenario_results": scenario_results},
    )


def handle_custom(request: Request, form_data: dict):
    """POST /race/custom — run a single user-supplied snapshot."""
    history = []
    for i in range(1, 16):
        dist_raw = form_data.get(f"run_distance{i}", "").strip()
        if not dist_raw:
            continue
        try:
            history.append({
                "distance_miles": float(dist_raw),
                "pace_minutes":   float(form_data.get(f"run_pace{i}", "10.0")),
                "terrain":        form_data.get(f"run_terrain{i}", "road").strip().lower(),
                "sentiment":      form_data.get(f"run_sentiment{i}", "neutral").strip().lower(),
            })
        except ValueError:
            pass

    target_time = form_data.get("target_time", "4:00:00").strip()
    # If the browser sent a bare number (e.g. "1"), convert to h:mm:ss so
    # _parse_time_to_minutes doesn't blow up with a cryptic error.
    if target_time.isdigit():
        mins = int(target_time)
        target_time = f"{mins // 60}:{mins % 60:02d}:00"

    snapshot = {
        "age":               float(form_data.get("age", 30)),
        "experience_level":  form_data.get("experience_level", "intermediate").strip().lower(),
        "days_to_race":      int(form_data.get("days_to_race", 42)),
        "adherence_percent": float(form_data.get("adherence_percent", 80)),
        "goal_race": {
            "distance":    form_data.get("race_distance", "marathon").strip().lower(),
            "target_time": target_time,
            "terrain":     form_data.get("race_terrain", "road").strip().lower(),
        },
        "history": history,
    }

    result = predict_race_readiness(snapshot, auto_train=True)

    # Parse goal time to minutes for the chart
    def _parse_goal(t: str) -> float | None:
        try:
            parts = [float(p) for p in t.split(":")]
            if len(parts) == 3:
                return parts[0] * 60 + parts[1] + parts[2] / 60
            if len(parts) == 2:
                return parts[0] * 60 + parts[1]
        except Exception:
            pass
        return None

    goal_min = _parse_goal(target_time)
    interval_chart = make_interval_chart_b64(
        pred_min=result["predicted_finish_minutes"],
        lo_min=result["confidence_interval_minutes"][0],
        hi_min=result["confidence_interval_minutes"][1],
        goal_min=goal_min,
    )

    return templates.TemplateResponse(
        "race_result.html",
        {"request": request, "snapshot": snapshot, "result": result,
         "interval_chart": interval_chart},
    )
