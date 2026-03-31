"""
Module 5 - Adaptive Progression System
MDP formulation: states, actions, and transition logic.
"""

from enum import Enum

VALID_TERRAINS = {"road", "track", "treadmill", "trail"}


# ---------------------------------------------------------------------------
# State space discretization
# ---------------------------------------------------------------------------

class FitnessTier(Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


class FatigueLevel(Enum):
    FRESH    = "fresh"
    MODERATE = "moderate"
    FATIGUED = "fatigued"


class TerrainStreak(Enum):
    VARIED = "varied"
    SAME   = "same"


class WorkoutCategory(Enum):
    EASY    = "easy"
    QUALITY = "quality"
    LONG    = "long"
    OTHER   = "other"


class AdherenceTier(Enum):          # NEW
    LOW    = "low"                  # < 60%  — runner is skipping sessions
    MEDIUM = "medium"               # 60–85% — partial compliance
    HIGH   = "high"                 # > 85%  — runner is following the plan


def workout_type_to_category(workout_type: str) -> WorkoutCategory:
    wt = (workout_type or "easy run").strip().lower()
    if wt in ("easy run", "recovery run"):
        return WorkoutCategory.EASY
    if wt == "long run":
        return WorkoutCategory.LONG
    if wt in ("tempo run", "interval", "hill workout", "fartlek", "time trial"):
        return WorkoutCategory.QUALITY
    if wt in ("race", "cross training"):
        return WorkoutCategory.OTHER
    return WorkoutCategory.EASY


# ---------------------------------------------------------------------------
# Action space
# ---------------------------------------------------------------------------

class VolumeAdjustment(Enum):
    DECREASE = -1
    HOLD     =  0
    INCREASE = +1


class IntensityAdjustment(Enum):
    EASIER  = -1
    HOLD    =  0
    HARDER  = +1


def all_actions():
    preferred = [
        (VolumeAdjustment.HOLD,     IntensityAdjustment.HOLD),
        (VolumeAdjustment.HOLD,     IntensityAdjustment.HARDER),
        (VolumeAdjustment.HOLD,     IntensityAdjustment.EASIER),
        (VolumeAdjustment.INCREASE, IntensityAdjustment.HOLD),
        (VolumeAdjustment.INCREASE, IntensityAdjustment.HARDER),
        (VolumeAdjustment.INCREASE, IntensityAdjustment.EASIER),
        (VolumeAdjustment.DECREASE, IntensityAdjustment.HOLD),
        (VolumeAdjustment.DECREASE, IntensityAdjustment.HARDER),
        (VolumeAdjustment.DECREASE, IntensityAdjustment.EASIER),
    ]
    return preferred


ALL_ACTIONS = all_actions()
COLD_START_ACTION = ALL_ACTIONS[0]


# ---------------------------------------------------------------------------
# State encoding
# ---------------------------------------------------------------------------

def encode_state(fitness_tier, fatigue_level, terrain_streak, workout_category, adherence_tier):
    return (fitness_tier, fatigue_level, terrain_streak, workout_category, adherence_tier)


def discretize_state(weekly_miles, fatigue_score, terrain_history, workout_type="easy run", adherence_percent=100.0):
    """
    Convert continuous runner metrics into a discrete MDP state.

    Now includes AdherenceTier as a 5th dimension so the agent learns
    separate policies for runners who are and aren't following their plan.
    State space: 3 × 3 × 2 × 4 × 3 = 216 states.
    """
    if weekly_miles < 20:
        fitness_tier = FitnessTier.LOW
    elif weekly_miles <= 40:
        fitness_tier = FitnessTier.MEDIUM
    else:
        fitness_tier = FitnessTier.HIGH

    if fatigue_score <= 0.33:
        fatigue_level = FatigueLevel.FRESH
    elif fatigue_score <= 0.66:
        fatigue_level = FatigueLevel.MODERATE
    else:
        fatigue_level = FatigueLevel.FATIGUED

    if len(terrain_history) >= 2 and terrain_history[-1] == terrain_history[-2]:
        terrain_streak = TerrainStreak.SAME
    else:
        terrain_streak = TerrainStreak.VARIED

    workout_category = workout_type_to_category(workout_type)

    # NEW: adherence tier
    if adherence_percent >= 85.0:
        adherence_tier = AdherenceTier.HIGH
    elif adherence_percent >= 60.0:
        adherence_tier = AdherenceTier.MEDIUM
    else:
        adherence_tier = AdherenceTier.LOW

    return encode_state(fitness_tier, fatigue_level, terrain_streak, workout_category, adherence_tier)


# ---------------------------------------------------------------------------
# Reward function
# ---------------------------------------------------------------------------

REWARD_COMPLETED_POSITIVE = +5.0
REWARD_COMPLETED_NEUTRAL  = +2.0
REWARD_COMPLETED_NEGATIVE = -1.0
REWARD_FATIGUE_SPIKE      = -4.0
REWARD_INJURY_RISK        = -8.0
REWARD_VARIETY_BONUS      = +1.0
REWARD_STEP_PENALTY       = -0.5

# NEW: adherence rewards — primary signal for plan compliance
REWARD_HIGH_ADHERENCE     = +3.0   # runner is consistently following the plan
REWARD_MEDIUM_ADHERENCE   =  0.0   # neutral — neither rewarded nor penalised
REWARD_LOW_ADHERENCE      = -5.0   # runner is skipping sessions — plan is at risk

# Loose bounds for sanity tests (optional adherence + motivation shaping included)
REWARD_MIN_APPROX = -18.0
REWARD_MAX_APPROX = 12.0


def motivation_reward_shaping(motivation, sentiment_canonical: str) -> float:
    if not motivation:
        return 0.0
    bonus = 0.0
    if motivation.get("adherence_percent", 0) >= 85.0 and sentiment_canonical == "positive":
        bonus += 0.5
    struggled = sum(1 for s in motivation.get("recent_sentiments", []) if s == "struggled")
    if struggled >= 2:
        bonus -= 1.0
    if motivation.get("days_to_race", 999) <= 14 and sentiment_canonical == "negative":
        bonus -= 0.5
    return bonus


def compute_reward(
    sentiment,
    fatigue_score_before,
    fatigue_score_after,
    terrain_before,
    terrain_after,
    adherence_percent=None,     # NEW
    motivation=None,
):
    """
    Compute the scalar reward for one completed training session.

    adherence_percent is now a primary signal. A runner skipping sessions
    (< 60%) produces a −5 penalty regardless of how the individual session
    went — because incomplete plans cannot produce marathon-ready fitness.
    """
    reward = REWARD_STEP_PENALTY

    sentiment = (sentiment or "neutral").lower()
    if sentiment == "positive":
        reward += REWARD_COMPLETED_POSITIVE
    elif sentiment == "negative":
        reward += REWARD_COMPLETED_NEGATIVE
    else:
        reward += REWARD_COMPLETED_NEUTRAL

    if fatigue_score_after > 0.85:
        reward += REWARD_INJURY_RISK
    elif fatigue_score_after - fatigue_score_before > 0.3:
        reward += REWARD_FATIGUE_SPIKE

    if terrain_before and terrain_after and terrain_before != terrain_after:
        reward += REWARD_VARIETY_BONUS

    # NEW: adherence is a primary reward component, not a post-processing tweak
    if adherence_percent is not None:
        if adherence_percent >= 85.0:
            reward += REWARD_HIGH_ADHERENCE
        elif adherence_percent < 60.0:
            reward += REWARD_LOW_ADHERENCE
        # 60–85% gets REWARD_MEDIUM_ADHERENCE = 0.0, no change

    reward += motivation_reward_shaping(motivation, sentiment)

    return reward