"""Names and encodings shared by synthetic data, training, and prediction."""

from pathlib import Path

DEFAULT_MODULE6_DATA_DIR = Path("data") / "module6"

FEATURE_COLUMNS = [
    "age",
    "goal_time_minutes",
    "goal_distance_km",
    "experience_encoded",
    "race_terrain_encoded",
    "weeks_of_training",
    "avg_weekly_miles_last_12w",
    "peak_weekly_miles",
    "avg_training_pace_min_per_mile",
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

CSV_COLUMNS = FEATURE_COLUMNS + [
    "actual_finish_time_minutes",
    "met_goal",
]

MARATHON_KM = 42.195
HALF_MARATHON_KM = 21.0975

# --- Synthetic row generation (`synthetic_data.generate_row`) ----------------
# Experience / terrain sampling
SYNTHETIC_EXPERIENCE_WEIGHTS = (0.5, 0.35, 0.15)
SYNTHETIC_TERRAIN_WEIGHTS = (0.70, 0.15, 0.15)
# Demographics & goal
SYNTHETIC_AGE_RANGE = (22, 56)
SYNTHETIC_GOAL_TIME_MINUTES_RANGE = (210, 361)
SYNTHETIC_WEEKS_OF_TRAINING_RANGE = (8, 25)
# Volume & long run
SYNTHETIC_PEAK_WEEKLY_RANGE = (15.0, 55.0)
SYNTHETIC_AVG_TO_PEAK_RANGE = (0.55, 0.95)
SYNTHETIC_LONGEST_RUN_PEAK_FRAC = 0.55
SYNTHETIC_LONGEST_RUN_CAP_MILES = 24.0
SYNTHETIC_NUM_LONG_RUNS_20_RANGE = (0, 5)
# Terrain mix
SYNTHETIC_TRAIL_BASE_RANGE_TRAIL = (25.0, 60.0)
SYNTHETIC_TRAIL_BASE_RANGE_OTHER = (5.0, 35.0)
SYNTHETIC_TRAIL_JITTER_SIGMA = 8.0
SYNTHETIC_TRACK_CAP = 25.0
# Adherence & horizon
SYNTHETIC_ADHERENCE_MEAN = 82.0
SYNTHETIC_ADHERENCE_STD = 12.0
SYNTHETIC_ADHERENCE_CLIP = (40.0, 100.0)
SYNTHETIC_DAYS_TO_RACE_RANGE = (21, 91)
SYNTHETIC_NEG_SENTIMENT_BETA_AB = (2.0, 8.0)
SYNTHETIC_NEG_SENTIMENT_CLIP = (0.0, 0.6)
# Simulated training pace (min/mile)
SYNTHETIC_PACE_BASE_INTERCEPT = 11.5
SYNTHETIC_PACE_PER_PEAK_MILE = -0.08
SYNTHETIC_PACE_BEGINNER_OFFSET = 1.5
SYNTHETIC_PACE_ADVANCED_OFFSET = -1.0
SYNTHETIC_PACE_NOISE_STD = 0.8
SYNTHETIC_PACE_CLIP_MIN_MAX = (6.5, 16.0)
# Label noise & met-goal (finish time = linear form + noise, then clip)
SYNTHETIC_FINISH_COEFF_INTERCEPT = 310.0
SYNTHETIC_FINISH_COEFF_AGE = 0.55
SYNTHETIC_FINISH_COEFF_AVG_WEEKLY = -0.90
SYNTHETIC_FINISH_COEFF_PEAK_WEEKLY = -0.935
SYNTHETIC_FINISH_COEFF_LONGEST_RUN = -2.4
SYNTHETIC_FINISH_COEFF_NUM_20 = -4.0
SYNTHETIC_FINISH_COEFF_GOAL_TIME = 0.12
SYNTHETIC_FINISH_COEFF_PACE = 7.383
SYNTHETIC_FINISH_NOISE_STD = 14.0
SYNTHETIC_EXPERIENCE_FINISH_OFFSET_BEGINNER = 8.0
SYNTHETIC_EXPERIENCE_FINISH_OFFSET_ADVANCED = -6.0
SYNTHETIC_FINISH_CLIP_MIN_MAX = (145.0, 420.0)
SYNTHETIC_MET_GOAL_SLACK_RANGE = (1.03, 1.12)
SYNTHETIC_MET_GOAL_LABEL_FLIP_PROB = 0.04