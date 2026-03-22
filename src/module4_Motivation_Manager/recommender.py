"""
recommender.py — Translate Nash Equilibrium into a concrete workout recommendation.

Takes the game-theoretic equilibrium result and the runner's state, then produces:
  - A specific intensity level: "hard" | "moderate" | "easy" | "rest"
  - A predicted adherence probability
  - A motivational message tailored to the runner's current situation
  - A strategic rationale explaining the game-theory reasoning

Intensity mapping from equilibrium strategies:
  Coach=hard + Runner=push  →  "hard"     (both aligned on effort)
  Coach=hard + Runner=rest  →  "moderate" (meet in the middle)
  Coach=easy + Runner=push  →  "moderate" (redirect runner's energy safely)
  Coach=easy + Runner=rest  →  "easy" or "rest" (full recovery)
"""

from dataclasses import dataclass
from src.module4_Motivation_Manager.state import RunnerState
from src.module4_Motivation_Manager.equilibrium import NashResult


@dataclass
class MotivationRecommendation:
    """
    Full output of the Module 4 recommendation pipeline.
    """
    recommended_intensity: str      # "hard" | "moderate" | "easy" | "rest"
    predicted_adherence:   float    # 0.0–1.0
    motivational_message:  str
    strategic_rationale:   str

    def to_dict(self) -> dict:
        return {
            "recommended_intensity": self.recommended_intensity,
            "predicted_adherence":   self.predicted_adherence,
            "motivational_message":  self.motivational_message,
            "strategic_rationale":   self.strategic_rationale,
        }


def build_recommendation(
    state: RunnerState,
    equilibrium: NashResult,
) -> MotivationRecommendation:
    """
    Translate Nash Equilibrium result into a concrete training recommendation.

    Args:
        state:       current RunnerState (fatigue, sentiment, safety, etc.)
        equilibrium: NashResult from equilibrium.find_nash_equilibrium()

    Returns:
        MotivationRecommendation with intensity, adherence, and messaging
    """
    cs = equilibrium.coach_strategy
    rs = equilibrium.runner_strategy

    # ── Intensity decision ───────────────────────────────────────────────────
    intensity = _map_intensity(cs, rs, state)

    # ── Safety override: Module 1 always wins ────────────────────────────────
    if not state.is_safe_to_push and intensity == "hard":
        intensity = "easy"

    # ── Overtraining circuit breaker ─────────────────────────────────────────
    if state.is_overtraining_risk() and intensity in ("hard", "moderate"):
        intensity = "rest"

    # ── Predicted adherence ──────────────────────────────────────────────────
    predicted_adherence = _compute_adherence(state, cs, rs)

    # ── Motivational message ─────────────────────────────────────────────────
    message = _build_message(state, equilibrium, intensity)

    # ── Strategic rationale ──────────────────────────────────────────────────
    rationale = (
        f"Game theory analysis ({equilibrium.equilibrium_type} equilibrium): "
        f"given your current fatigue ({state.fatigue_level:.0%}) and "
        f"adherence history ({state.adherence_rate:.0%}), "
        f"the stable strategy is coach assigns '{cs}' and runner plays '{rs}'. "
        f"Recommended intensity: {intensity.upper()}."
    )

    return MotivationRecommendation(
        recommended_intensity=intensity,
        predicted_adherence=round(predicted_adherence, 2),
        motivational_message=message,
        strategic_rationale=rationale,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _map_intensity(coach: str, runner: str, state: RunnerState) -> str:
    """Map equilibrium strategy pair to a concrete intensity level."""
    if coach == "hard" and runner == "push":
        return "hard"
    if coach == "hard" and runner == "rest":
        return "moderate"
    if coach == "easy" and runner == "push":
        return "moderate"
    # coach == "easy" and runner == "rest"
    return "rest" if state.fatigue_level > 0.7 else "easy"


def _compute_adherence(state: RunnerState, coach: str, runner: str) -> float:
    """
    Estimate how likely the runner is to follow today's recommendation.

    Alignment bonus: when coach and runner strategies naturally converge,
    adherence tends to be higher because the plan matches the runner's
    instinct.
    """
    base = state.adherence_rate

    # Both wanting to push → runner is motivated, more likely to follow
    if coach == "hard" and runner == "push":
        base += 0.15
    # Both wanting recovery → runner agrees, easy to comply
    elif coach == "easy" and runner == "rest":
        base += 0.10
    # Conflict: coach wants hard but runner wants rest (or vice versa)
    else:
        base -= 0.05

    # Sentiment boost: positive recent runs → more buy-in
    if state.avg_sentiment > 0.3:
        base += 0.05

    return max(0.0, min(1.0, base))


def _build_message(
    state: RunnerState,
    eq: NashResult,
    intensity: str,
) -> str:
    """Generate a contextual motivational message based on the full situation."""

    if intensity == "rest":
        if state.is_overtraining_risk():
            return (
                "Your body is sending clear signals — multiple overtraining indicators "
                "are active. Full rest today is not optional, it is the training."
            )
        return (
            "Rest is part of training, not a break from it. "
            "Your body adapts during recovery, not during the run itself."
        )

    if intensity == "easy":
        if state.avg_sentiment < 0.0:
            return (
                "Your recent logs show some tough days. An easy effort today "
                "rebuilds both your legs and your momentum — no pressure."
            )
        return (
            "Easy days make hard days possible. "
            "Keep the effort fully conversational today."
        )

    if intensity == "moderate":
        if eq.equilibrium_type == "mixed":
            p = eq.coach_mix_prob or 0.5
            return (
                f"The strategic analysis found a mixed equilibrium — "
                f"optimal effort today sits between easy and hard "
                f"(hard probability: {p:.0%}). Moderate intensity is the sweet spot."
            )
        return (
            f"You've been consistent ({state.adherence_rate:.0%} adherence). "
            "A moderate effort today builds on that momentum without overdoing it."
        )

    # intensity == "hard"
    if eq.equilibrium_type == "dominant":
        return (
            "Conditions are optimal — low fatigue, positive trend, safe to push. "
            "Today is a day to give it everything you have."
        )
    return (
        "Strategic analysis confirms you're ready for a hard effort. "
        "Trust the process — this is exactly where fitness is built."
    )