"""
demo.py — Runnable demo for Module 4: Motivation Manager.

How to run (from project root):
    python -m src.module4_Motivation_Manager.demo
  or:
    python src/module4_Motivation_Manager/demo.py
"""

from __future__ import annotations

import json
import sys
import os
from typing import Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.module4_Motivation_Manager.manager import get_daily_recommendation


def pretty(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


# ---------------------------------------------------------------------------
# User-facing input adapter
#
# The system receives a compact summary dict (what a frontend or API would
# send) and expands it into the three arguments get_daily_recommendation()
# expects: runner_profile, run_history, safety_result.
# ---------------------------------------------------------------------------

# Maps M3 sentiment labels → float scores used by state.py
_SENTIMENT_SCORE: dict[str, float] = {
    "easy":      1.0,
    "good":      0.7,
    "moderate":  0.0,
    "hard":     -0.5,
    "struggled": -1.0,
}

# Maps sentiment label → approximate effort level
_SENTIMENT_EFFORT: dict[str, float] = {
    "easy":      0.3,
    "good":      0.5,
    "moderate":  0.6,
    "hard":      0.8,
    "struggled": 0.9,
}


def from_user_input(user_input: dict) -> tuple[dict, list, dict]:
    """
    Convert a compact user-facing summary dict into the three inputs
    expected by get_daily_recommendation().

    User input keys:
        current_streak      int    consecutive training days
        recent_sentiments   list   M3 labels: "easy"|"good"|"moderate"|"hard"|"struggled"
        terrain_last_week   list   terrain strings per session
        adherence_percent   int    0–100
        days_to_race        int    days until race (optional, informational)

    Returns:
        (runner_profile, run_history, safety_result)
    """
    streak       = user_input.get("current_streak", 0)
    sentiments   = user_input.get("recent_sentiments", [])
    terrains     = user_input.get("terrain_last_week", [])
    adherence_pct = user_input.get("adherence_percent", 70)

    # Build run_history — pair each sentiment with its terrain (zip stops at shorter)
    run_history = []
    for i, label in enumerate(sentiments):
        terrain = terrains[i] if i < len(terrains) else "road"
        run_history.append({
            "sentiment": _SENTIMENT_SCORE.get(label, 0.0),
            "effort":    _SENTIMENT_EFFORT.get(label, 0.5),
            "terrain":   terrain,
            "type":      "easy run",   # default; M3 would fill this from log text
        })

    runner_profile = {
        "days_trained_this_week": min(streak, 7),
        "adherence_rate":         adherence_pct / 100.0,
        "experience_level":       "intermediate",  # default; extend if user sends it
        "weekly_mileage":         streak * 5.0,    # rough estimate: 5 km/day
    }

    # Safety heuristic: flag rest if streak is very long or last run was "struggled"
    last_label = sentiments[-1] if sentiments else "good"
    safe = streak < 7 and last_label != "struggled"
    safety_result = {
        "safe":   safe,
        "reason": (
            "No contraindications found." if safe
            else f"Streak of {streak} days or recent struggle detected — rest advised."
        ),
    }

    return runner_profile, run_history, safety_result


# ---------------------------------------------------------------------------
# Demo scenes
# ---------------------------------------------------------------------------

def demo_from_user_input() -> None:
    """DEMO 1 — The exact input format the user provided."""
    user_input = {
        "current_streak":    18,
        "recent_sentiments": ["good", "good", "struggled"],
        "terrain_last_week": ["treadmill", "treadmill", "treadmill"],
        "adherence_percent": 85,
        "days_to_race":      45,
    }

    print("\n" + "=" * 70)
    print("DEMO 1 — User input format  (streak=18, last run: struggled)")
    print("=" * 70)
    print("User input:", pretty(user_input))

    runner_profile, run_history, safety_result = from_user_input(user_input)

    print("\nExpanded runner_profile:", pretty(runner_profile))
    print("Expanded run_history   :", pretty(run_history))
    print("Expanded safety_result :", pretty(safety_result))

    result = get_daily_recommendation(
        runner_profile=runner_profile,
        run_history=run_history,
        safety_result=safety_result,
    )
    _print_result(result)


def demo_fresh_runner() -> None:
    """DEMO 2 — Short streak, all-positive sentiments."""
    user_input = {
        "current_streak":    3,
        "recent_sentiments": ["good", "easy", "good"],
        "terrain_last_week": ["track", "road", "treadmill"],
        "adherence_percent": 90,
        "days_to_race":      60,
    }

    print("\n" + "=" * 70)
    print("DEMO 2 — Fresh runner  (streak=3, all good sentiments)")
    print("=" * 70)
    print("User input:", pretty(user_input))

    runner_profile, run_history, safety_result = from_user_input(user_input)
    result = get_daily_recommendation(
        runner_profile=runner_profile,
        run_history=run_history,
        safety_result=safety_result,
    )
    _print_result(result)


def demo_struggling_runner() -> None:
    """DEMO 3 — Moderate streak but consecutive struggles."""
    user_input = {
        "current_streak":    5,
        "recent_sentiments": ["hard", "struggled", "struggled"],
        "terrain_last_week": ["road", "road", "road"],
        "adherence_percent": 60,
        "days_to_race":      14,
    }

    print("\n" + "=" * 70)
    print("DEMO 3 — Struggling runner  (streak=5, back-to-back struggles)")
    print("=" * 70)
    print("User input:", pretty(user_input))

    runner_profile, run_history, safety_result = from_user_input(user_input)
    result = get_daily_recommendation(
        runner_profile=runner_profile,
        run_history=run_history,
        safety_result=safety_result,
    )
    _print_result(result)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_result(result: dict) -> None:
    print("\n--- Primary Recommendation ---")
    print(f"  Intensity          : {result['recommended_intensity']}")
    print(f"  Predicted adherence: {result['predicted_adherence']:.0%}")
    print(f"  Message            : {result['motivational_message']}")
    print(f"  Rationale          : {result['strategic_rationale']}")

    print("\n--- Game-Theory Equilibrium ---")
    print(f"  Equilibrium type   : {result['equilibrium_type']}")
    print(f"  Coach strategy     : {result['coach_strategy']}")
    print(f"  Runner strategy    : {result['runner_strategy']}")
    if result["coach_mix_prob"] is not None:
        print(f"  Coach mix prob     : {result['coach_mix_prob']:.2f}")
        print(f"  Runner mix prob    : {result['runner_mix_prob']:.2f}")
    print(f"  Explanation        : {result['equilibrium_explanation']}")

    print("\n--- Runner State ---")
    print(pretty(result["runner_state"]))

    print("\n--- Payoff Matrix ---")
    print(pretty(result["payoff_matrix"]))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    demo_from_user_input()
    demo_fresh_runner()
    demo_struggling_runner()


if __name__ == "__main__":
    main()
