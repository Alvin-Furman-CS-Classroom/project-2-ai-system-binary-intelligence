"""
  M1 safety_result ──┐
  M3 run_history  ──▶│ build_runner_state()  →  RunnerState
  runner_profile  ──┘
                            ↓
                   compute_payoff_matrix()  →  PayoffMatrix (2×2 normal-form game)
                            ↓
                   find_nash_equilibrium()  →  NashResult (dominant / pure / mixed)
                            ↓
                   build_recommendation()  →  MotivationRecommendation
                            ↓
                   get_daily_recommendation()  →  dict  ← what the rest of the system calls

"""

from src.module4_Motivation_Manager.state       import RunnerState, build_runner_state
from src.module4_Motivation_Manager.payoff      import PayoffMatrix, compute_payoff_matrix
from src.module4_Motivation_Manager.equilibrium import NashResult, find_nash_equilibrium
from src.module4_Motivation_Manager.recommender import MotivationRecommendation, build_recommendation


def get_daily_recommendation(
    runner_profile: dict,
    run_history:    list,
    safety_result:  dict,
) -> dict:
    # Stage 1 — build state from M1 + M3 outputs
    state = build_runner_state(runner_profile, run_history, safety_result)

    # Stage 2 — construct the normal-form game payoff matrix
    matrix = compute_payoff_matrix(state)

    # Stage 3 — solve for Nash Equilibrium
    equilibrium = find_nash_equilibrium(matrix)

    # Stage 4 — translate equilibrium to actionable recommendation
    recommendation = build_recommendation(state, equilibrium)

    return {
        # Primary outputs
        "recommended_intensity":   recommendation.recommended_intensity,
        "predicted_adherence":     recommendation.predicted_adherence,
        "motivational_message":    recommendation.motivational_message,
        "strategic_rationale":     recommendation.strategic_rationale,

        # Equilibrium details
        "equilibrium_type":        equilibrium.equilibrium_type,
        "coach_strategy":          equilibrium.coach_strategy,
        "runner_strategy":         equilibrium.runner_strategy,
        "coach_mix_prob":          equilibrium.coach_mix_prob,
        "runner_mix_prob":         equilibrium.runner_mix_prob,
        "equilibrium_explanation": equilibrium.explanation,

        # Debug / transparency
        "runner_state":            state.to_dict(),
        "payoff_matrix":           matrix.to_dict(),
    }


# ---------------------------------------------------------------------------
# Convenience re-exports so callers can do:
#   from src.module4_Motivation_Manager.manager import RunnerState, ...
# ---------------------------------------------------------------------------

__all__ = [
    "get_daily_recommendation",
    "RunnerState",
    "build_runner_state",
    "PayoffMatrix",
    "compute_payoff_matrix",
    "NashResult",
    "find_nash_equilibrium",
    "MotivationRecommendation",
    "build_recommendation",
]