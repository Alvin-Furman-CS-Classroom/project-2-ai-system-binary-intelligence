"""
equilibrium.py — Nash Equilibrium computation for the Coach vs Runner game.

Implements three solution concepts from the lecture:
  1. Dominant Strategy Equilibrium  (Slides 41, 47)
  2. Pure Nash Equilibrium          (Slides 50–53)
  3. Mixed Nash Equilibrium         (Slides 55–65, Indifference Principle)

Algorithm (Slide 53):
  - For each coach strategy, find runner's best response (max runner payoff in that column).
  - For each runner strategy, find coach's best response (max coach payoff in that row).
  - Pure NE = where both are simultaneously best responses (overlapping marks).
  - If no pure NE → solve via Indifference Principle for mixed equilibrium.
"""

from dataclasses import dataclass
from typing import Optional
from src.module4_Motivation_Manager.payoff import PayoffMatrix, COACH_STRATEGIES, RUNNER_STRATEGIES


@dataclass
class NashResult:
    """
    Result of Nash Equilibrium computation.

    equilibrium_type: "dominant" | "pure" | "mixed"
    coach_strategy:   recommended coach action ("hard" | "easy")
    runner_strategy:  predicted runner action  ("push" | "rest")
    coach_mix_prob:   P(coach plays "hard") — only set for mixed NE
    runner_mix_prob:  P(runner plays "push") — only set for mixed NE
    explanation:      human-readable rationale
    """
    equilibrium_type: str
    coach_strategy:   str
    runner_strategy:  str
    coach_mix_prob:   Optional[float]
    runner_mix_prob:  Optional[float]
    explanation:      str

    def to_dict(self) -> dict:
        return {
            "equilibrium_type": self.equilibrium_type,
            "coach_strategy":   self.coach_strategy,
            "runner_strategy":  self.runner_strategy,
            "coach_mix_prob":   self.coach_mix_prob,
            "runner_mix_prob":  self.runner_mix_prob,
            "explanation":      self.explanation,
        }


def find_nash_equilibrium(matrix: PayoffMatrix) -> NashResult:
    """
    Find the Nash Equilibrium of the 2x2 payoff matrix.

    Priority order:
      1. Check for dominant strategies first (strongest solution concept).
      2. If not dominant, search for pure Nash Equilibrium.
      3. If no pure NE, compute mixed NE via Indifference Principle.

    Args:
        matrix: PayoffMatrix with all four (coach, runner) payoff cells

    Returns:
        NashResult describing the equilibrium found
    """
    # ── Step 1: Dominant Strategy Equilibrium ───────────────────────────────
    coach_dom  = _dominant_strategy_coach(matrix)
    runner_dom = _dominant_strategy_runner(matrix)

    if coach_dom and runner_dom:
        payoff = matrix.get(coach_dom, runner_dom)
        return NashResult(
            equilibrium_type="dominant",
            coach_strategy=coach_dom,
            runner_strategy=runner_dom,
            coach_mix_prob=None,
            runner_mix_prob=None,
            explanation=(
                f"Dominant strategy equilibrium: coach plays '{coach_dom}', "
                f"runner plays '{runner_dom}' regardless of what the other does. "
                f"Payoffs — Coach: {payoff[0]}, Runner: {payoff[1]}."
            ),
        )

    # ── Step 2: Pure Nash Equilibrium ───────────────────────────────────────
    pure_ne = _find_pure_ne(matrix)

    if pure_ne:
        cs, rs = pure_ne[0]
        payoff = matrix.get(cs, rs)
        return NashResult(
            equilibrium_type="pure",
            coach_strategy=cs,
            runner_strategy=rs,
            coach_mix_prob=None,
            runner_mix_prob=None,
            explanation=(
                f"Pure Nash Equilibrium: coach='{cs}', runner='{rs}'. "
                f"Neither player wants to unilaterally deviate. "
                f"Payoffs — Coach: {payoff[0]}, Runner: {payoff[1]}."
            ),
        )

    # ── Step 3: Mixed Nash Equilibrium (Indifference Principle) ─────────────
    return _find_mixed_ne(matrix)


# ---------------------------------------------------------------------------
# Helper: Dominant strategy detection
# ---------------------------------------------------------------------------

def _dominant_strategy_coach(matrix: PayoffMatrix) -> Optional[str]:
    """
    Return coach's strictly dominant strategy if one exists, else None.
    A strategy dominates if it yields strictly higher coach payoff against
    ALL possible runner strategies.
    """
    for cs in COACH_STRATEGIES:
        other = [s for s in COACH_STRATEGIES if s != cs][0]
        if all(
            matrix.get(cs, rs)[0] > matrix.get(other, rs)[0]
            for rs in RUNNER_STRATEGIES
        ):
            return cs
    return None


def _dominant_strategy_runner(matrix: PayoffMatrix) -> Optional[str]:
    """
    Return runner's strictly dominant strategy if one exists, else None.
    """
    for rs in RUNNER_STRATEGIES:
        other = [s for s in RUNNER_STRATEGIES if s != rs][0]
        if all(
            matrix.get(cs, rs)[1] > matrix.get(cs, other)[1]
            for cs in COACH_STRATEGIES
        ):
            return rs
    return None


# ---------------------------------------------------------------------------
# Helper: Pure NE detection
# ---------------------------------------------------------------------------

def _find_pure_ne(matrix: PayoffMatrix) -> list:
    """
    Find all pure Nash Equilibria using the best-response method (Slide 53).

    For each cell (cs, rs):
      - Is cs the coach's best response to rs?  (max coach payoff in that column)
      - Is rs the runner's best response to cs?  (max runner payoff in that row)
    If both yes → pure NE.

    Returns list of (coach_strategy, runner_strategy) tuples.
    """
    pure_ne = []
    for cs in COACH_STRATEGIES:
        for rs in RUNNER_STRATEGIES:
            coach_br  = max(COACH_STRATEGIES,  key=lambda c: matrix.get(c, rs)[0])
            runner_br = max(RUNNER_STRATEGIES, key=lambda r: matrix.get(cs, r)[1])
            if cs == coach_br and rs == runner_br:
                pure_ne.append((cs, rs))
    return pure_ne


# ---------------------------------------------------------------------------
# Helper: Mixed NE via Indifference Principle (Slides 64–65)
# ---------------------------------------------------------------------------

def _find_mixed_ne(matrix: PayoffMatrix) -> NashResult:
    """
    Compute mixed Nash Equilibrium using the Indifference Principle.

    Key insight (Slide 64):
      Each player chooses mixing probabilities that make the OPPONENT indifferent
      between their pure strategies — not to directly maximize their own payoff.

    Let p = P(coach plays "hard"), q = P(runner plays "push").

    Coach's mixing (p) makes runner indifferent between push and rest:
      p·R(hard,push) + (1-p)·R(easy,push) = p·R(hard,rest) + (1-p)·R(easy,rest)
      Solve for p.

    Runner's mixing (q) makes coach indifferent between hard and easy:
      q·C(hard,push) + (1-q)·C(hard,rest) = q·C(easy,push) + (1-q)·C(easy,rest)
      Solve for q.
    """
    # Payoff values
    R_hp = matrix.get("hard", "push")[1]   # runner payoff: hard+push
    R_hr = matrix.get("hard", "rest")[1]   # runner payoff: hard+rest
    R_ep = matrix.get("easy", "push")[1]   # runner payoff: easy+push
    R_er = matrix.get("easy", "rest")[1]   # runner payoff: easy+rest

    C_hp = matrix.get("hard", "push")[0]   # coach payoff: hard+push
    C_hr = matrix.get("hard", "rest")[0]   # coach payoff: hard+rest
    C_ep = matrix.get("easy", "push")[0]   # coach payoff: easy+push
    C_er = matrix.get("easy", "rest")[0]   # coach payoff: easy+rest

    # Solve for p (coach's probability of playing "hard")
    denom_p = (R_hp - R_hr) - (R_ep - R_er)
    p = 0.5 if abs(denom_p) < 1e-9 else max(0.0, min(1.0, (R_er - R_ep) / denom_p))

    # Solve for q (runner's probability of playing "push")
    denom_q = (C_hp - C_hr) - (C_ep - C_er)
    q = 0.5 if abs(denom_q) < 1e-9 else max(0.0, min(1.0, (C_er - C_hr) / denom_q))

    coach_strategy  = "hard" if p >= 0.5 else "easy"
    runner_strategy = "push" if q >= 0.5 else "rest"

    return NashResult(
        equilibrium_type="mixed",
        coach_strategy=coach_strategy,
        runner_strategy=runner_strategy,
        coach_mix_prob=round(p, 3),
        runner_mix_prob=round(q, 3),
        explanation=(
            f"Mixed Nash Equilibrium: coach plays 'hard' with probability {p:.1%}, "
            f"runner plays 'push' with probability {q:.1%}. "
            f"Each player's mixing probabilities are chosen to make the opponent "
            f"indifferent between their pure strategies (Indifference Principle)."
        ),
    )