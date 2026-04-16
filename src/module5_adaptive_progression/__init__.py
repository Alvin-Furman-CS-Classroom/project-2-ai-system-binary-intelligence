"""
Module 5 - Adaptive Progression System
Public API.

Primary entry points
--------------------
adapt_progression(context)
    Returns a simple next-session recommendation dict.

adapt_progression_detailed(context)
    Returns the recommendation plus internal Q-learning state for analysis.

train_on_run(context, outcome, q_table_path=None)
    Updates the Q-table after a run is logged, enabling online learning.

Example usage
-------------
from src.module5_adaptive_progression import adapt_progression

context = {
    "workout_type": "tempo run",
    "terrain": "track",
    "fatigue_score": 0.3,
    "history": [
        {"date": "2025-01-10", "distance": 5, "pace": 8.5,
         "terrain": "track", "sentiment": "positive"},
        {"date": "2025-01-12", "distance": 6, "pace": 8.4,
         "terrain": "track", "sentiment": "positive"},
    ],
    # Optional: same dict shape as Module 4 select_motivation_strategy input
    "motivation": {
        "current_streak": 12,
        "recent_sentiments": ["good", "good", "neutral"],
        "terrain_last_week": ["track", "track", "road"],
        "adherence_percent": 90,
        "days_to_race": 50,
    },
}

result = adapt_progression(context)
# {
#   "next_distance": 6.6,
#   "target_pace": 8.15,
#   "suggested_terrain": "road",
#   "confidence": 0.0,
#   "reasoning": "..."
# }
"""

from .advisor import adapt_progression, adapt_progression_detailed, train_on_run
from .input_validation import normalize_sentiment_to_canonical

__all__ = [
    "adapt_progression",
    "adapt_progression_detailed",
    "train_on_run",
    "normalize_sentiment_to_canonical",
]
