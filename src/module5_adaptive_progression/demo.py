"""Demo for the adaptive progression module.

Run from project root:
    python -m src.module5_adaptive_progression.demo
"""

from __future__ import annotations

import os
import sys

try:
    from .adaptor import adapt_progression_detailed
except ImportError:
    path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(path))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from src.module5_adaptive_progression.adaptor import adapt_progression_detailed


SCENARIOS = [
    {
        "label": "Consistent runner ready to progress",
        "context": {
            "workout_type": "easy run",
            "terrain": "road",
            "fatigue_score": 0.2,
            "history": [
                {"distance": 5.0, "pace": 9.5, "terrain": "road",     "sentiment": "great"},
                {"distance": 5.2, "pace": 9.4, "terrain": "trail",    "sentiment": "good"},
                {"distance": 5.5, "pace": 9.3, "terrain": "road",     "sentiment": "strong"},
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
                {"distance": 8.0, "pace": 8.8, "terrain": "road",      "sentiment": "exhausted"},
                {"distance": 7.5, "pace": 9.0, "terrain": "road",      "sentiment": "struggled"},
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
        "label": "Cold-start — brand new runner (no history)",
        "context": {
            "workout_type": "easy run",
            "terrain": "trail",
            "fatigue_score": 0.3,
            "history": [],
        },
    },
    {
        "label": "Low-adherence runner rebuilding consistency",
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


def _conf_bar(confidence: float, width: int = 20) -> str:
    filled = int(round(confidence * width))
    return "[" + "#" * filled + "." * (width - filled) + f"] {confidence:.2f}"


def _q_bar(q: float, width: int = 16) -> str:
    norm = min(1.0, max(0.0, (q + 5) / 10))
    filled = int(round(norm * width))
    return "[" + "#" * filled + "." * (width - filled) + f"] {q:+.4f}"


def run_demo() -> None:
    for i, scenario in enumerate(SCENARIOS, 1):
        label = scenario["label"]
        ctx   = scenario["context"]

        print(f"\n{'=' * 65}")
        print(f"Scenario {i}: {label}")
        print(f"{'=' * 65}")
        print(f"  Workout type : {ctx['workout_type']}")
        print(f"  Terrain      : {ctx['terrain']}")
        print(f"  Fatigue score: {ctx['fatigue_score']}")
        print(f"  History      : {len(ctx['history'])} run(s)")

        result = adapt_progression_detailed(ctx)

        print(f"\n  ── Recommendation ──────────────────────────────────")
        print(f"  Next distance    : {result['next_distance']:.2f} mi")
        print(f"  Target pace      : {result['target_pace']:.2f} min/mi")
        print(f"  Suggested terrain: {result['suggested_terrain']}")
        print(f"  Confidence       : {_conf_bar(result['confidence'])}")
        print(f"  Weekly miles     : {result['weekly_miles']:.2f} mi")
        print(f"  Sentiment trend  : {result['sentiment_trend']}")
        print(f"  Adherence        : {result['adherence_percent']:.0f}%")
        print(f"  State            : {result['state']}")
        print(f"  Episodes trained : {result['episode_count']}")

        print(f"\n  ── Q-values ─────────────────────────────────────────")
        for action, q in sorted(result["q_values"].items(), key=lambda x: -x[1]):
            print(f"    {action:<30} {_q_bar(q)}")

        print(f"\n  ── Reasoning ────────────────────────────────────────")
        for line in result["reasoning"].split(". "):
            line = line.strip()
            if line:
                print(f"    {line}.")

    print(f"\n{'=' * 65}")
    print("Demo complete.")


if __name__ == "__main__":
    run_demo()
