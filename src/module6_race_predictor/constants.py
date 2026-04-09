"""Names and encodings shared by synthetic data, training, and prediction."""

# Order must match the column order used when fitting models.
FEATURE_COLUMNS = [
    "age",
    "goal_time_minutes",
    "goal_distance_km",
    "experience_encoded",
    "race_terrain_encoded",
    "weeks_of_training",
    "avg_weekly_miles_last_12w",
    "peak_weekly_miles",
    "longest_run_miles",
    "num_runs_20_plus",
    "pct_miles_road",
    "pct_miles_trail",
    "pct_miles_track",
    "adherence_pct",
    "days_to_race",
    "negative_sentiment_rate",
]

EXPERIENCE_LEVELS = ("beginner", "intermediate", "advanced")
TERRAIN_TYPES = ("road", "trail", "track", "treadmill")

# Synthetic dataset CSV columns (features + labels)
CSV_COLUMNS = FEATURE_COLUMNS + [
    "actual_finish_time_minutes",
    "met_goal",
]

MARATHON_KM = 42.195
HALF_MARATHON_KM = 21.0975
