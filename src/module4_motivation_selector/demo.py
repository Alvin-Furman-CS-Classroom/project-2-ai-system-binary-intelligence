"""Demo for the motivation selector module.

Run from project root:
    python -m src.module4_motivation_selector.demo
"""

from __future__ import annotations

import json
import os
import sys

try:
    from .selector import select_motivation_strategy_detailed
except ImportError:
    # Add project root to path relative to this file so we can import from src
    # This allows running the demo directly without -m from project root
    path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(path))
    if project_root not in sys.path:
        sys.path.append(project_root)
    # Use absolute import from project root
    from src.module4_motivation_selector.selector import select_motivation_strategy_detailed

SCENARIOS = [
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


def run_demo() -> None:
    for i, scenario in enumerate(SCENARIOS, 1):
        label = scenario["label"]
        ctx = scenario["context"]

        print(f"\n{'=' * 60}")
        print(f"Scenario {i}: {label}")
        print(f"{'=' * 60}")
        print(f"  Streak       : {ctx['current_streak']} days")
        print(f"  Sentiments   : {ctx['recent_sentiments']}")
        print(f"  Terrain      : {ctx['terrain_last_week']}")
        print(f"  Adherence    : {ctx['adherence_percent']}%")
        print(f"  Days to race : {ctx['days_to_race']}")

        result = select_motivation_strategy_detailed(ctx)

        print(f"\n  Inferred state : {result['inferred_state']}")
        print(f"  Strategy       : {result['strategy']}")
        print(f"  Message tone   : {result['message_tone']}")

        print("\n  Strategy scores:")
        for strategy, score in sorted(result["scores"].items(), key=lambda x: -x[1]):
            marker = " <-- selected" if strategy == result["strategy"] else ""
            print(f"    {strategy:<22} {_bar(score)}{marker}")

        print(f"\n  Reasoning:\n    {result['reasoning']}")

    print(f"\n{'=' * 60}")
    print("Demo complete.")


if __name__ == "__main__":
    run_demo()
