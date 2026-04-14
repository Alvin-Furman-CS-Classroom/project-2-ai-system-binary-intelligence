"""
Thin orchestration layer for Long Run: wires Module 3 history, Module 2 planning,
Module 1 safety profile, and Module 5 adaptive progression without changing those modules.

Uses a JSON runner profile (paths + planner config + Module 1 dict) as the single
place to read settings. Run history stays in the Module 3 log file; the Q-table JSON
is written only by ``train_on_run`` / ``pipeline_train_on_run`` when they save.
The default file is ``DEFAULT_Q_TABLE_PATH`` (``data/q_table.json``); override with
``paths.q_table`` in the profile or ``q_table_path=...`` when building context.

**Feedback from Module 5 → Module 2 plan**

- ``apply_module5_to_plan_workout`` patches one workout in a generated plan using
  ``adapt_progression`` output (distance + terrain; optional Module 5 notes in metadata).
- ``pipeline_plan_adjusted_by_progression`` generates a plan, gets the next-session
  recommendation, and returns the plan with that slot updated.
- ``regenerate_plan_with_estimated_weekly_load`` re-runs ``generate_plan`` using
  ``estimate_weekly_miles`` from recent runs so the *macro* plan tracks actual load.

**Plan vs log adherence** (``src/pipeline/adherence.py``)

- Pass ``plan_week`` into ``build_module5_context`` (or use ``pipeline_recommend_*`` /
  ``train_on_run`` with ``plan_week=...``) to compute adherence vs the Module 3 log and
  merge a **Module 4** ``motivation`` dict (including ``adherence_percent``) into
  Module 5's context.
- ``pipeline_plan_adjusted_by_progression`` passes the selected plan week automatically
  and adds an ``adherence`` breakdown to its return value.

**Module 6 race prediction** (``src.module6_race_predictor``)

- ``pipeline_predict_race_readiness`` builds a snapshot from the profile (optional
  ``age``, ``race_goal`` / ``goal_race`` block) and Module 5-shaped history from the
  run log, then returns predicted finish, interval, readiness score, and recommendations.
"""

from __future__ import annotations

import copy
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.module5_adaptive_progression.input_validation import VALID_WORKOUT_TYPES
from src.module5_adaptive_progression.mdp import VALID_TERRAINS

from .adherence import (
    compute_week_adherence,
    fetch_module3_entries,
    motivation_with_plan_adherence,
)
from .constants import (
    DEFAULT_ADHERENCE_DAYS_WINDOW,
    DEFAULT_Q_TABLE_PATH,
    DEFAULT_RUNNER_PROFILE_PATH,
    PROFILE_SCHEMA_VERSION,
)


def _pop_plan_adherence_kwargs(overrides: dict[str, Any]) -> tuple[dict[str, Any] | None, int, dict[str, Any]]:
    """Split ``plan_week`` / ``adherence_days_window`` from other Module 5 overrides."""
    o = dict(overrides)
    plan_week = o.pop("plan_week", None)
    raw_days = o.pop("adherence_days_window", DEFAULT_ADHERENCE_DAYS_WINDOW)
    try:
        adherence_days_window = max(1, int(raw_days))
    except (TypeError, ValueError):
        adherence_days_window = DEFAULT_ADHERENCE_DAYS_WINDOW
    return plan_week, adherence_days_window, o


def load_runner_profile(path: str | Path = DEFAULT_RUNNER_PROFILE_PATH) -> dict[str, Any]:
    """Load runner profile JSON. Raises FileNotFoundError if missing, ValueError if invalid."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Runner profile not found: {p.resolve()}")
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Runner profile is not valid JSON ({p}): {exc.msg} (line {exc.lineno} col {exc.colno})"
        ) from exc
    ver = data.get("schema_version", 0)
    if ver != PROFILE_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported runner_profile schema_version {ver}; expected {PROFILE_SCHEMA_VERSION}"
        )
    return data


def save_runner_profile(profile: dict[str, Any], path: str | Path = DEFAULT_RUNNER_PROFILE_PATH) -> None:
    """Write runner profile JSON (creates parent dirs if needed)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)


def _normalize_terrain_m5(terrain: str | None) -> str:
    t = (terrain or "road").strip().lower()
    if t == "grass":
        return "trail"
    if t in VALID_TERRAINS:
        return t
    return "road"


def _normalize_workout_type_m5(wt: str | None) -> str:
    w = (wt or "easy run").strip().lower()
    aliases = {
        "intervals": "interval",
        "tempo": "tempo run",
        "easy": "easy run",
        "recovery": "recovery run",
    }
    w = aliases.get(w, w)
    if w in VALID_WORKOUT_TYPES:
        return w
    return "easy run"


def m3_run_entries_to_m5_history(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convert Module 3 ``get_recent_runs`` / store entries into Module 5 ``history`` rows.

    Each Module 3 entry has ``logged_at`` and ``parsed`` (type, distance, pace_minutes,
    terrain, sentiment, ...). Module 5 requires positive distance and pace; missing
    distance uses a small placeholder (3.0 mi) so interval-only logs still work.
    """
    out: list[dict[str, Any]] = []
    for e in entries:
        parsed = e.get("parsed") or {}
        dist = parsed.get("distance")
        if dist is None:
            dist = 3.0
        else:
            dist = float(dist)
        pace = parsed.get("pace_minutes")
        if pace is None:
            pace = 10.0
        else:
            pace = float(pace)
        logged = e.get("logged_at") or ""
        date_str = logged[:10] if len(logged) >= 10 else ""

        sentiment = parsed.get("sentiment") or "neutral"
        if sentiment not in ("positive", "neutral", "negative"):
            sentiment = "neutral"

        out.append(
            {
                "date": date_str,
                "distance": dist,
                "pace": pace,
                "terrain": _normalize_terrain_m5(parsed.get("terrain")),
                "sentiment": sentiment,
            }
        )
    return out


def fetch_m5_history(profile: dict[str, Any], n: int = 14) -> list[dict[str, Any]]:
    """Load last ``n`` runs from the profile's run log and map them for Module 5."""
    from src.module3_run_logger import get_run_history

    path = profile.get("paths", {}).get("run_log", "data/run_log.json")
    entries = get_run_history(n=n, store_path=path)
    return m3_run_entries_to_m5_history(entries)


def planner_config_from_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Return a dict suitable for ``module2_plan_generator.generate_plan``."""
    p = profile.get("planner") or {}
    return dict(p)


def module1_runner_from_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Return runner dict for ``validate_workout`` / Module 2 optional validation."""
    m1 = profile.get("module1_runner")
    if isinstance(m1, dict) and m1:
        return dict(m1)
    # Minimal fallback from planner + defaults
    pl = profile.get("planner") or {}
    return {
        "experience_level": pl.get("experience", "beginner"),
        "weekly_mileage": float(pl.get("current_weekly_miles", 0)),
        "injuries": [],
        "symptoms": [],
        "pain_level": "none",
        "cleared_by_doctor": True,
        "fully_recovered": True,
        "sleep_quality": "good",
        "hydrated": True,
        "rest_days_this_week": 2,
        "days_trained_this_week": 3,
        "hard_workout_yesterday": False,
        "available_terrain": list(pl.get("available_terrain", ["road"])),
        "weather": "normal",
        "proper_footwear": True,
        "race_date": pl.get("race_date"),
    }


def build_module5_context(
    profile: dict[str, Any],
    *,
    history: list[dict[str, Any]] | None = None,
    plan_week: dict[str, Any] | None = None,
    adherence_days_window: int = DEFAULT_ADHERENCE_DAYS_WINDOW,
    **overrides: Any,
) -> dict[str, Any]:
    """
    Build the context dict for ``adapt_progression`` / ``train_on_run``.

    Pass ``history`` to avoid re-reading the log; otherwise loads via ``fetch_m5_history``.
    Optional overrides: workout_type, terrain, fatigue_score, motivation, alpha, gamma,
    epsilon, validate_fn, q_table_path, etc.

    If ``plan_week`` is set (one week dict from Module 2 ``generate_plan`` output), the
    pipeline computes **plan vs log adherence** and merges **Module 4 motivation**
    (including ``adherence_percent``) so Module 5's motivation adjustments apply.

    A profile loaded only from JSON cannot include ``validate_fn`` (callables); set
    ``profile["validate_fn"]`` in code before calling, or pass ``validate_fn=...`` here.
    """
    extra = dict(overrides)
    prog = profile.get("progression_defaults") or {}
    paths = profile.get("paths") or {}

    if history is None:
        history = fetch_m5_history(profile)

    if plan_week is not None:
        base_mot = extra.pop("motivation", None)
        if base_mot is None:
            base_mot = profile.get("motivation")
        extra["motivation"] = motivation_with_plan_adherence(
            profile,
            history,
            plan_week,
            base_motivation=base_mot,
            days_window=adherence_days_window,
        )

    ctx: dict[str, Any] = {
        "workout_type": _normalize_workout_type_m5(
            extra.pop("workout_type", None) or prog.get("next_workout_type", "easy run")
        ),
        "terrain": _normalize_terrain_m5(
            extra.pop("terrain", None) or prog.get("default_terrain", "road")
        ),
        "fatigue_score": float(
            extra.pop("fatigue_score", prog.get("fatigue_score", 0.3))
        ),
        "history": history,
        "q_table_path": extra.pop("q_table_path", None)
        or paths.get("q_table")
        or DEFAULT_Q_TABLE_PATH,
    }

    if "validate_fn" not in extra and profile.get("validate_fn") is not None:
        ctx["validate_fn"] = profile["validate_fn"]
    if "runner_profile" not in extra and profile.get("module1_runner"):
        ctx["runner_profile"] = module1_runner_from_profile(profile)

    ctx.update(extra)
    return ctx


def pipeline_recommend_next_session(
    profile: dict[str, Any],
    **context_overrides: Any,
) -> dict[str, Any]:
    """Load history from profile paths, then call Module 5 ``adapt_progression``."""
    from src.module5_adaptive_progression import adapt_progression

    plan_week, adherence_days_window, rest = _pop_plan_adherence_kwargs(context_overrides)
    ctx = build_module5_context(
        profile,
        plan_week=plan_week,
        adherence_days_window=adherence_days_window,
        **rest,
    )
    return adapt_progression(ctx)


def pipeline_recommend_next_session_detailed(
    profile: dict[str, Any],
    **context_overrides: Any,
) -> dict[str, Any]:
    from src.module5_adaptive_progression import adapt_progression_detailed

    plan_week, adherence_days_window, rest = _pop_plan_adherence_kwargs(context_overrides)
    ctx = build_module5_context(
        profile,
        plan_week=plan_week,
        adherence_days_window=adherence_days_window,
        **rest,
    )
    return adapt_progression_detailed(ctx)


def pipeline_train_on_run(
    profile: dict[str, Any],
    outcome: dict[str, Any],
    *,
    q_table_path: str | None = None,
    **context_overrides: Any,
) -> dict[str, Any]:
    """Build context from profile and call Module 5 ``train_on_run``."""
    from src.module5_adaptive_progression import train_on_run

    plan_week, adherence_days_window, rest = _pop_plan_adherence_kwargs(context_overrides)
    ctx = build_module5_context(
        profile,
        plan_week=plan_week,
        adherence_days_window=adherence_days_window,
        **rest,
    )
    return train_on_run(ctx, outcome, q_table_path=q_table_path)


def pipeline_generate_plan(
    profile: dict[str, Any],
    validate_fn: Any | None = None,
    **generate_plan_kwargs: Any,
) -> dict[str, Any]:
    """Call Module 2 ``generate_plan`` using profile planner config and optional Module 1."""
    from src.module2_plan_generator import generate_plan

    config = planner_config_from_profile(profile)
    runner = module1_runner_from_profile(profile)
    return generate_plan(
        config,
        validate_fn=validate_fn,
        runner_profile=runner,
        **generate_plan_kwargs,
    )


def _recalculate_week_total_miles(week_data: dict[str, Any]) -> None:
    workouts = week_data.get("workouts") or []
    total = sum(float(w.get("distance", 0) or 0) for w in workouts)
    week_data["total_miles"] = round(total, 2)
    if "weekly_total" in week_data:
        week_data["weekly_total"] = week_data["total_miles"]


def apply_module5_to_plan_workout(
    plan: list[dict[str, Any]],
    week_index: int,
    workout_index: int,
    recommendation: dict[str, Any],
    *,
    update_workout_type: bool = False,
    workout_type: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return a **copy** of the Module 2 ``plan`` with one workout updated from Module 5.

    ``recommendation`` should be the dict from ``adapt_progression`` (keys
    ``next_distance``, ``suggested_terrain``, optionally ``target_pace``).

    If ``update_workout_type`` is True, sets workout ``type`` from ``workout_type``
    (must match Module 2 vocabulary, e.g. ``easy run``, ``long run``).
    """
    out = copy.deepcopy(plan)
    if week_index < 0 or week_index >= len(out):
        raise IndexError(f"week_index {week_index} out of range (len={len(out)})")
    week = out[week_index]
    wlist = week.get("workouts") or []
    if workout_index < 0 or workout_index >= len(wlist):
        raise IndexError(f"workout_index {workout_index} out of range (len={len(wlist)})")

    w = wlist[workout_index]
    w["distance"] = round(float(recommendation["next_distance"]), 2)
    w["terrain"] = _normalize_terrain_m5(recommendation.get("suggested_terrain"))
    if "target_pace" in recommendation:
        w["_module5_target_pace_min_per_mile"] = float(recommendation["target_pace"])
    w["_module5_reasoning"] = recommendation.get("reasoning", "")
    if update_workout_type and workout_type:
        w["type"] = workout_type

    _recalculate_week_total_miles(week)
    return out


def pipeline_plan_adjusted_by_progression(
    profile: dict[str, Any],
    *,
    week_index: int = 0,
    workout_index: int = 0,
    validate_fn: Any | None = None,
    update_workout_type: bool = False,
    **m5_context_overrides: Any,
) -> dict[str, Any]:
    """
    Generate a plan (Module 2), get next-session recommendation (Module 5), and patch
    the chosen workout so the **program reflects the adaptation**.

    Returns the same shape as ``generate_plan`` plus:
    - ``recommendation``: Module 5 dict
    - ``adjustment``: ``{"week_index", "workout_index"}``

    If plan generation fails, returns that result without ``recommendation``.
    """
    base = pipeline_generate_plan(profile, validate_fn=validate_fn)
    if not base.get("success") or not base.get("plan"):
        return base

    week_data = base["plan"][week_index]
    rec = pipeline_recommend_next_session(
        profile,
        plan_week=week_data,
        **m5_context_overrides,
    )
    wt = None
    if update_workout_type:
        pw, adw, rest = _pop_plan_adherence_kwargs(m5_context_overrides)
        ctx = build_module5_context(
            profile,
            plan_week=pw or week_data,
            adherence_days_window=adw,
            **rest,
        )
        wt = ctx.get("workout_type")

    adjusted = apply_module5_to_plan_workout(
        base["plan"],
        week_index,
        workout_index,
        rec,
        update_workout_type=update_workout_type,
        workout_type=wt,
    )
    ad = compute_week_adherence(
        week_data,
        fetch_module3_entries(profile, n=100),
        days_window=7,
    )

    out = dict(base)
    out["plan"] = adjusted
    out["recommendation"] = rec
    out["adjustment"] = {"week_index": week_index, "workout_index": workout_index}
    out["adherence"] = ad
    return out


def _days_to_race_from_profile(profile: dict[str, Any], override: float | None) -> float:
    if override is not None:
        return max(1.0, float(override))
    pl = profile.get("planner") or {}
    rd = pl.get("race_date")
    if not rd or not isinstance(rd, str):
        return 56.0
    raw = rd.strip()[:10]
    try:
        race = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return 56.0
    delta = (race - date.today()).days
    return float(max(1, delta))


def pipeline_predict_race_readiness(
    profile: dict[str, Any],
    *,
    history: list[dict[str, Any]] | None = None,
    days_to_race: float | None = None,
    adherence_percent: float | None = None,
    age: float | None = None,
    goal_race: dict[str, Any] | None = None,
    experience_level: str | None = None,
    module6_dir: str | Path | None = None,
    auto_train: bool = True,
) -> dict[str, Any]:
    """
    Run Module 6 on the runner profile: load history from the log unless ``history`` is
    passed, build ``goal_race`` from ``goal_race=`` or profile keys ``race_goal`` /
    ``goal_race``, and call ``predict_race_readiness``.

    Profile keys (all optional except implicit planner):

    - ``age``: defaults to 32 if missing.
    - ``race_goal`` or ``goal_race``: ``target_time`` (``\"4:30:00\"``), ``terrain``,
      ``distance`` (e.g. ``\"marathon\"``), optional ``adherence_percent`` when not passed
      as an argument.
    - ``planner.race_date``: used to set ``days_to_race`` unless overridden.
    - ``planner.experience`` or ``module1_runner.experience_level``: experience tier.
    """
    from src.module6_race_predictor import predict_race_readiness

    if history is None:
        history = fetch_m5_history(profile)

    pl = profile.get("planner") or {}
    m1 = profile.get("module1_runner") or {}
    rg_prof = profile.get("race_goal") or profile.get("goal_race") or {}

    exp = experience_level or pl.get("experience") or m1.get("experience_level") or "beginner"
    snap_age = float(age) if age is not None else float(profile.get("age", 32))

    if goal_race is not None:
        gr = dict(goal_race)
    else:
        gr = {
            "distance": rg_prof.get("distance", "marathon"),
            "target_time": rg_prof.get("target_time", "4:30:00"),
            "terrain": rg_prof.get("terrain", "road"),
        }

    adh = adherence_percent
    if adh is None and "adherence_percent" in rg_prof:
        adh = float(rg_prof["adherence_percent"])
    if adh is None:
        adh = 85.0

    dtr = _days_to_race_from_profile(profile, days_to_race)

    snapshot = {
        "history": history,
        "age": snap_age,
        "experience_level": str(exp).strip().lower(),
        "days_to_race": dtr,
        "adherence_percent": float(adh),
        "goal_race": gr,
    }
    return predict_race_readiness(
        snapshot,
        module6_dir=module6_dir,
        auto_train=auto_train,
    )


def regenerate_plan_with_estimated_weekly_load(
    profile: dict[str, Any],
    validate_fn: Any | None = None,
    *,
    min_weekly_miles: float = 5.0,
    **generate_plan_kwargs: Any,
) -> dict[str, Any]:
    """
    Re-run ``generate_plan`` using **estimated weekly miles** from recent runs (Module 5
    feature extraction). Updates ``current_weekly_miles`` in the planner config so the
    **initial search** reflects actual load — use after logging several weeks of runs.

    Does not modify the JSON profile file unless you save it yourself.
    """
    from src.module2_plan_generator import generate_plan
    from src.module5_adaptive_progression.features import estimate_weekly_miles

    history = fetch_m5_history(profile)
    estimated = float(estimate_weekly_miles(history))
    config = planner_config_from_profile(profile)
    config["current_weekly_miles"] = max(min_weekly_miles, estimated)

    runner = module1_runner_from_profile(profile)
    runner["weekly_mileage"] = config["current_weekly_miles"]

    return generate_plan(
        config,
        validate_fn=validate_fn,
        runner_profile=runner,
        **generate_plan_kwargs,
    )


__all__ = [
    "DEFAULT_ADHERENCE_DAYS_WINDOW",
    "DEFAULT_RUNNER_PROFILE_PATH",
    "DEFAULT_Q_TABLE_PATH",
    "PROFILE_SCHEMA_VERSION",
    "load_runner_profile",
    "save_runner_profile",
    "m3_run_entries_to_m5_history",
    "fetch_m5_history",
    "planner_config_from_profile",
    "module1_runner_from_profile",
    "build_module5_context",
    "pipeline_recommend_next_session",
    "pipeline_recommend_next_session_detailed",
    "pipeline_train_on_run",
    "pipeline_generate_plan",
    "apply_module5_to_plan_workout",
    "pipeline_plan_adjusted_by_progression",
    "regenerate_plan_with_estimated_weekly_load",
    "compute_week_adherence",
    "fetch_module3_entries",
    "motivation_with_plan_adherence",
    "pipeline_predict_race_readiness",
]
