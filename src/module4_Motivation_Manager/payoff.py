"""
payoff.py — PayoffMatrix dataclass and computation from RunnerState.

Builds the 2x2 normal-form game matrix between:
  Coach  strategies: "hard" | "easy"
  Runner strategies: "push" | "rest"

Each cell holds (coach_payoff, runner_payoff).

Design is grounded in lecture concepts (Slides 38–39):
  - Payoff structure mirrors the Prisoner's Dilemma when both push while fatigued.
  - Coach payoffs weight adaptation gain vs. injury risk.
  - Runner payoffs weight feel-good motivation vs. fatigue cost.
"""

from dataclasses import dataclass, field
from src.module4_Motivation_Manager.state import RunnerState


COACH_STRATEGIES  = ["hard", "easy"]
RUNNER_STRATEGIES = ["push", "rest"]


@dataclass
class PayoffMatrix:
    """
    2x2 payoff matrix for the Coach vs Runner game.

    payoffs[coach_strategy][runner_strategy] = (coach_payoff, runner_payoff)
    """
    payoffs: dict = field(default_factory=dict)

    def get(self, coach_strategy: str, runner_strategy: str) -> tuple:
        """Return (coach_payoff, runner_payoff) for the given strategy pair."""
        return self.payoffs[coach_strategy][runner_strategy]

    def to_dict(self) -> dict:
        return self.payoffs

    def display(self) -> str:
        """Human-readable payoff matrix for logging/debugging."""
        lines = [
            f"{'':20} {'PUSH':>12} {'REST':>12}",
            "-" * 46,
        ]
        for cs in COACH_STRATEGIES:
            cp, rp = self.get(cs, "push")
            cr, rr = self.get(cs, "rest")
            lines.append(
                f"COACH={cs.upper():6}        "
                f"({cp:+.2f}, {rp:+.2f})   "
                f"({cr:+.2f}, {rr:+.2f})"
            )
        return "\n".join(lines)


def compute_payoff_matrix(state: RunnerState) -> PayoffMatrix:
    """
    Construct the 2x2 payoff matrix from the runner's current state.

    Payoff design principles:
      - Coach wants maximum safe adaptation. High fatigue + unsafe = injury penalty.
      - Runner wants to feel capable but not destroyed. High effort + fatigue = pain.
      - Both pushing hard when fatigued = Prisoner's Dilemma (both lose long-term).
      - Mutual easy/rest = cooperative outcome (both gain recovery benefit).

    Args:
        state: current RunnerState snapshot

    Returns:
        PayoffMatrix with all four cells populated
    """
    f  = state.fatigue_level        # 0=fresh, 1=exhausted
    s  = 1.0 if state.is_safe_to_push else 0.0
    se = state.avg_sentiment        # -1 to +1
    e  = state.avg_effort           # 0=easy, 1=maximal
    a  = state.adherence_rate       # 0=never follows plan, 1=always

    # ── Coach payoffs ────────────────────────────────────────────────────────
    # hard+push: best when safe and fresh; worst when fatigued and unsafe
    adaptation_gain  = 8.0 * s * (1.0 - f)
    injury_penalty   = 10.0 * f * (1.0 - s)
    coach_hard_push  = round(adaptation_gain - injury_penalty, 2)

    # hard+rest: runner ignored the hard plan — loss of coaching control
    coach_hard_rest  = round(-3.0 * (1.0 - a), 2)

    # easy+push: runner over-performed on an easy day — minor concern
    coach_easy_push  = round(-2.0, 2)

    # easy+rest: ideal recovery day — both comply, positive outcome
    coach_easy_rest  = round(5.0 * (1.0 - f), 2)

    # ── Runner payoffs ───────────────────────────────────────────────────────
    feel_good        = 4.0 * se                   # positive sentiment = motivation
    effort_cost      = 6.0 * e * f                # high effort × fatigue = pain

    # hard+push: runner feels accomplished but pays fatigue cost
    runner_hard_push = round(feel_good - effort_cost + 2.0, 2)

    # hard+rest: runner skipped hard plan, slight guilt but body recovers
    rest_base        = 3.0 + 2.0 * max(0.0, 1.0 - state.days_since_rest / 7.0)
    runner_hard_rest = round(rest_base - 1.0, 2)

    # easy+push: runner pushed harder than plan — reduced cost because plan was easy
    runner_easy_push = round(feel_good - effort_cost * 0.5, 2)

    # easy+rest: full compliance with easy plan — best recovery feeling
    runner_easy_rest = round(rest_base + 1.0, 2)

    payoffs = {
        "hard": {
            "push": (coach_hard_push, runner_hard_push),
            "rest": (coach_hard_rest, runner_hard_rest),
        },
        "easy": {
            "push": (coach_easy_push, runner_easy_push),
            "rest": (coach_easy_rest, runner_easy_rest),
        },
    }

    return PayoffMatrix(payoffs=payoffs)