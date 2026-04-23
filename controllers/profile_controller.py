import json
import os
from datetime import datetime, date, timedelta
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from src.module2_plan_generator.search import a_star_search
from src.module2_plan_generator.states import TrainingState
from src.module3_NPL_search.parser import RunLogParser
from src.module4_motivation_selector.selector import select_motivation_strategy_detailed
from src.module5_adaptive_progression.adaptor import adapt_progression_detailed
from src.module6_race_predictor.predictor import predict_race_readiness
from src.module6_race_predictor.charts import make_interval_chart_b64

_parser = RunLogParser()


def _json_safe(obj):
    """Recursively convert numpy/non-serialisable types to Python natives."""
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    try:
        import numpy as np
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
    except ImportError:
        pass
    return obj


def _parse_goal_time(t: str):
    try:
        parts = [float(p) for p in t.split(":")]
        return parts[0] * 60 + parts[1] + (parts[2] / 60 if len(parts) == 3 else 0)
    except Exception:
        return None


_SENTIMENT_MAP = {
    "positive": "good", "negative": "struggled", "moderate": "neutral",
    "neutral": "neutral", "struggled": "struggled", "good": "good",
}


def _compute_motivation(profile: dict) -> dict | None:
    run_history = profile.get("run_history", [])
    if not run_history:
        return None

    # recent_sentiments: last 5 runs mapped to module4 format
    recent_sentiments = [
        _SENTIMENT_MAP.get(r.get("sentiment", "neutral"), "neutral")
        for r in run_history[:5]
    ]

    # terrain_last_week: runs in last 7 days, fall back to last 3 runs
    today = date.today()
    week_ago = (today - timedelta(days=7)).isoformat()
    week_runs = [r for r in run_history if r.get("logged_at", "")[:10] >= week_ago]
    if not week_runs:
        week_runs = run_history[:3]
    terrain_last_week = [r.get("terrain") or "road" for r in week_runs]
    if not terrain_last_week:
        terrain_last_week = profile.get("available_terrain", ["road"])

    # current_streak: consecutive *scheduled training days* completed without a miss
    _weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    training_days = set(profile.get("training_days", []))
    run_dates = {r.get("logged_at", "")[:10] for r in run_history if r.get("logged_at")}
    streak, check = 0, today
    for _ in range(365):
        day_name = _weekday_names[check.weekday()]
        if day_name in training_days:
            if check.isoformat() in run_dates:
                streak += 1
            else:
                break  # missed a scheduled day — streak ends
        check -= timedelta(days=1)

    # adherence_percent: runs logged vs expected based on training days and time since creation
    days_per_week = len(profile.get("training_days", []))
    try:
        created = date.fromisoformat(profile.get("created_at", today.isoformat()))
    except ValueError:
        created = today
    weeks_elapsed = max(1, (today - created).days / 7)
    expected = days_per_week * weeks_elapsed
    adherence = round(min(len(run_history) / expected * 100, 100.0), 1) if expected > 0 else 50.0

    # days_to_race
    days_to_race = 0
    active_plan = profile.get("active_plan")
    if active_plan and active_plan.get("race_date"):
        try:
            days_to_race = max(0, (date.fromisoformat(active_plan["race_date"]) - today).days)
        except ValueError:
            days_to_race = 0

    context = {
        "current_streak": streak,
        "recent_sentiments": recent_sentiments,
        "terrain_last_week": terrain_last_week,
        "adherence_percent": adherence,
        "days_to_race": days_to_race,
    }

    try:
        result = select_motivation_strategy_detailed(context)
        result["context"] = context
        return result
    except Exception:
        return None


def get_motivation_history(request: Request, slug: str, run_index: int) -> JSONResponse:
    profiles = _load_profiles()
    profile = profiles.get(slug)
    if not profile:
        return JSONResponse({"error": "Profile not found"}, status_code=404)
    sliced = dict(profile)
    sliced["run_history"] = profile.get("run_history", [])[run_index:]
    result = _compute_motivation(sliced)
    if not result:
        return JSONResponse({"error": "No run history for that entry"}, status_code=400)
    return JSONResponse(result)


_WORKOUT_TYPE_MAP = {
    "easy": "easy run", "easy run": "easy run",
    "long": "long run", "long run": "long run",
    "tempo": "tempo run", "tempo run": "tempo run",
    "interval": "interval", "intervals": "interval",
    "recovery": "recovery run", "recovery run": "recovery run",
    "hill": "hill workout", "hill workout": "hill workout",
    "fartlek": "fartlek",
    "race": "race",
    "time trial": "time trial",
    "cross training": "cross training", "cross": "cross training",
}

_TERRAIN_NORM_M5 = {
    "road": "road", "track": "track", "treadmill": "treadmill", "trail": "trail",
    "grass": "trail", "mixed": "road",
}


def _compute_progression(profile: dict, motivation_ctx: dict | None) -> dict | None:
    run_history = profile.get("run_history", [])
    valid_runs = [r for r in run_history if r.get("distance") and r.get("pace_minutes")]
    if not valid_runs:
        return None

    history = []
    for r in valid_runs:
        raw_terrain = (r.get("terrain") or "road").lower().strip()
        terrain = _TERRAIN_NORM_M5.get(raw_terrain, "road")
        history.append({
            "distance":  float(r["distance"]),
            "pace":      float(r["pace_minutes"]),
            "terrain":   terrain,
            "sentiment": r.get("sentiment") or "neutral",
            "date":      r.get("logged_at", "")[:10],
        })

    last_type = (valid_runs[0].get("type") or "easy").lower().strip()
    workout_type = _WORKOUT_TYPE_MAP.get(last_type, "easy run")

    raw_terrain = (valid_runs[0].get("terrain") or "road").lower().strip()
    terrain = _TERRAIN_NORM_M5.get(raw_terrain, "road")
    if terrain not in {"road", "track", "treadmill", "trail"}:
        terrain = "road"

    recent_sentiments = [r.get("sentiment", "neutral") for r in valid_runs[:5]]
    neg_count = sum(1 for s in recent_sentiments if s in {"negative", "struggled", "bad"})
    fatigue_score = round(min(0.9, neg_count / max(len(recent_sentiments), 1) * 0.8 + 0.1), 2)

    context: dict = {
        "workout_type":  workout_type,
        "terrain":       terrain,
        "fatigue_score": fatigue_score,
        "history":       history,
    }

    if motivation_ctx and "context" in motivation_ctx:
        context["motivation"] = {k: motivation_ctx["context"][k]
                                 for k in ("current_streak", "recent_sentiments",
                                           "terrain_last_week", "adherence_percent",
                                           "days_to_race")}

    try:
        return adapt_progression_detailed(context)
    except Exception:
        return None


templates = Jinja2Templates(directory="templates")

PROFILES_FILE = "data/user_profiles.json"


def _load_profiles() -> dict:
    if not os.path.exists(PROFILES_FILE):
        return {}
    with open(PROFILES_FILE) as f:
        return json.load(f)


def _save_profiles(profiles: dict):
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)


def show_create_form(request: Request):
    return templates.TemplateResponse("profile_create.html", {"request": request})


def create_profile(request: Request, form_data: dict):
    profiles = _load_profiles()
    slug = form_data["name"].strip().lower().replace(" ", "-")
    profiles[slug] = {
        "name": form_data["name"].strip(),
        "slug": slug,
        "age": int(form_data.get("age", 30)),
        "experience": form_data["experience"],
        "current_weekly_miles": float(form_data["current_weekly_miles"]),
        "available_terrain": form_data["available_terrain"],
        "training_days": form_data["training_days"],
        "created_at": date.today().isoformat(),
        "active_plan": None,
        "run_history": [],
    }
    _save_profiles(profiles)
    return RedirectResponse(url=f"/user/{slug}", status_code=303)


def _compute_progress_chart(profile: dict) -> dict:
    """Return {labels, actual, planned} lists for the progress chart."""
    run_history = profile.get("run_history") or []
    saved_plan  = profile.get("saved_plan")
    active_plan = profile.get("active_plan")

    # Bucket actual runs by calendar week (Monday-anchored)
    week_actual: dict = {}
    for r in run_history:
        if not r.get("distance") or not r.get("logged_at"):
            continue
        d   = date.fromisoformat(r["logged_at"][:10])
        mon = d - timedelta(days=d.weekday())
        week_actual[mon] = week_actual.get(mon, 0.0) + r["distance"]

    # Build plan week map covering all plan weeks
    plan_week_map: dict = {}
    if saved_plan and active_plan and active_plan.get("generated_at"):
        try:
            gen = date.fromisoformat(active_plan["generated_at"])
        except ValueError:
            gen = None
        if gen:
            for i, week in enumerate(saved_plan.get("plan", [])):
                w_start = gen + timedelta(weeks=i)
                w_mon   = w_start - timedelta(days=w_start.weekday())
                plan_week_map[w_mon] = float(week.get("total_miles", 0))

    # Union of all weeks (actual runs + all plan weeks)
    all_weeks = sorted(set(week_actual) | set(plan_week_map))
    if not all_weeks:
        return {"labels": [], "actual": [], "planned": []}

    labels  = [k.strftime("%b %-d") for k in all_weeks]
    actual  = [round(week_actual[k], 1) if k in week_actual else None for k in all_weeks]
    planned = [round(plan_week_map[k], 1) if k in plan_week_map else None for k in all_weeks]

    return {"labels": labels, "actual": actual, "planned": planned}


def _compute_safety_overview(profile: dict, progression: dict | None) -> dict | None:
    from src.module1_safety_validator.validator import validate_workout

    today = date.today()
    run_history = profile.get("run_history", [])
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    this_week_runs = [r for r in run_history if r.get("logged_at", "")[:10] >= week_start]
    days_trained = len(this_week_runs)
    rest_days = max(0, today.weekday() + 1 - days_trained)

    runner_profile = {
        "injuries": [],
        "symptoms": [],
        "weekly_mileage":         profile.get("current_weekly_miles", 0),
        "rest_days_this_week":    rest_days,
        "days_trained_this_week": days_trained,
        "available_terrain":      profile.get("available_terrain", ["road"]),
        "experience_level":       profile.get("experience", "beginner"),
        "hydrated": True, "proper_footwear": True,
        "weather": "normal", "fully_recovered": True, "sleep_quality": "good",
    }

    if progression:
        distance = round(float(progression.get("next_distance", 5.0)), 1)
        terrain  = progression.get("suggested_terrain", (profile.get("available_terrain") or ["road"])[0])
        workout_type = "easy run"
    else:
        distance = round(max(3.0, profile.get("current_weekly_miles", 20) / 4), 1)
        terrain  = (profile.get("available_terrain") or ["road"])[0]
        workout_type = "easy run"

    proposed = {"type": workout_type, "distance": distance, "terrain": terrain}

    try:
        result = validate_workout(runner_profile, proposed)
        return {"result": _json_safe(result), "proposed": proposed}
    except Exception:
        return None


def show_profile(request: Request, slug: str):
    profiles = _load_profiles()
    profile = profiles.get(slug)
    if not profile:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    motivation  = _compute_motivation(profile)
    progression = _compute_progression(profile, motivation)
    safety      = _compute_safety_overview(profile, progression)

    interval_chart = None
    rr = profile.get("race_readiness")
    if rr:
        try:
            res = rr["result"]
            interval_chart = make_interval_chart_b64(
                pred_min=res["predicted_finish_minutes"],
                lo_min=res["confidence_interval_minutes"][0],
                hi_min=res["confidence_interval_minutes"][1],
                goal_min=_parse_goal_time(rr["target_time"]),
            )
        except Exception:
            interval_chart = None

    progress_chart = _compute_progress_chart(profile)

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "profile": profile,
        "motivation":     motivation,
        "progression":    progression,
        "safety":         safety,
        "interval_chart": interval_chart,
        "progress_chart": progress_chart,
    })


def get_progression_json(request: Request, slug: str):
    profiles = _load_profiles()
    profile  = profiles.get(slug)
    if not profile:
        return JSONResponse({"ok": False, "error": "Profile not found"}, status_code=404)

    motivation  = _compute_motivation(profile)
    progression = _compute_progression(profile, motivation)

    if not progression:
        return JSONResponse({"ok": False, "error": "Log at least one run with distance and pace first."})

    # Build chart data from run history (oldest→newest for chart x-axis)
    valid_runs = [
        r for r in profile.get("run_history", [])
        if r.get("distance") and r.get("pace_minutes")
    ][:15]
    valid_runs = list(reversed(valid_runs))

    def _fmt_date(iso):
        try:
            return date.fromisoformat(iso[:10]).strftime("%b %-d")
        except Exception:
            return iso[:10]

    chart_data = {
        "labels":    [_fmt_date(r.get("logged_at", "")) for r in valid_runs],
        "distances": [round(float(r["distance"]), 1)    for r in valid_runs],
        "paces":     [round(float(r["pace_minutes"]), 2) for r in valid_runs],
        "sentiments": [r.get("sentiment", "neutral")    for r in valid_runs],
        "types":     [(r.get("type") or "run").title()  for r in valid_runs],
    }

    return JSONResponse({"ok": True, "progression": _json_safe(progression), "chart_data": chart_data})


def generate_plan(request: Request, slug: str, form_data: dict):
    profiles = _load_profiles()
    profile = profiles.get(slug)
    if not profile:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    race_date = datetime.strptime(form_data["race_date"], "%Y-%m-%d").date()
    today = date.today()
    total_weeks = max(1, (race_date - today).days // 7)

    race_distances = {
        "full_marathon": {"name": "Full Marathon", "distance_km": 42.2, "distance_miles": 26.2},
        "half_marathon": {"name": "Half Marathon", "distance_km": 21.1, "distance_miles": 13.1},
        "10k":           {"name": "10K",           "distance_km": 10,   "distance_miles": 6.2},
    }
    race_info = race_distances.get(form_data["race_type"], race_distances["full_marathon"])

    start = TrainingState.create_start(
        total_weeks=total_weeks,
        days_per_week=len(profile["training_days"]),
        current_weekly_miles=profile["current_weekly_miles"],
        available_terrain=profile["available_terrain"],
        experience=profile["experience"],
    )
    result = a_star_search(start)

    # Assign days
    training_days = profile["training_days"]
    if result.get("plan") and training_days:
        for week in result["plan"]:
            workouts = week.get("workouts", [])
            long_runs = [w for w in workouts if w.get("type") == "long run"]
            others = [w for w in workouts if w.get("type") != "long run"]
            sorted_days = sorted(training_days, key=lambda d: (
                d not in ["Saturday", "Sunday"],
                ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].index(d),
            ))
            i = 0
            for w in others:
                if i < len(sorted_days): w["day"] = sorted_days[i]; i += 1
            for w in long_runs:
                if i < len(sorted_days): w["day"] = sorted_days[i]; i += 1

    # Attach week dates and calendar days
    _day_to_weekday = {"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,"Friday":4,"Saturday":5,"Sunday":6}
    if result.get("plan"):
        for week in result["plan"]:
            week_num = week.get("week", 1)
            week_start = today + timedelta(weeks=week_num - 1)
            week["week_start_date"] = week_start.strftime("%b %d")
            start_wd = week_start.weekday()
            for workout in week.get("workouts", []):
                wday = workout.get("day", "")
                if wday in _day_to_weekday:
                    offset = (_day_to_weekday[wday] - start_wd) % 7
                    workout["workout_date"] = (week_start + timedelta(days=offset)).isoformat()
            calendar_days = []
            for i in range(7):
                day_date = week_start + timedelta(days=i)
                day_iso = day_date.isoformat()
                calendar_days.append({
                    "date": day_date.strftime("%-d"),
                    "month": day_date.strftime("%b"),
                    "day_name": day_date.strftime("%a"),
                    "workouts": [w for w in week.get("workouts", []) if w.get("workout_date") == day_iso],
                })
            week["calendar_days"] = calendar_days

    # Persist plan summary + full plan to profile
    profiles[slug]["active_plan"] = {
        "race_type": race_info["name"],
        "race_date": form_data["race_date"],
        "total_weeks": total_weeks,
        "generated_at": date.today().isoformat(),
    }
    profiles[slug]["saved_plan"] = {
        "race_type": race_info["name"],
        "race_date": form_data["race_date"],
        "race_distance": f"{race_info['distance_km']} km / {race_info['distance_miles']} miles",
        "total_weeks": total_weeks,
        "training_days": training_days,
        "generated_at": date.today().isoformat(),
        "rationale": result.get("rationale", ""),
        "plan": result.get("plan", []),
    }
    _save_profiles(profiles)

    result["race_type"] = race_info["name"]
    result["race_distance"] = f"{race_info['distance_km']} km / {race_info['distance_miles']} miles"
    result["race_date"] = form_data["race_date"]
    result["total_weeks"] = total_weeks
    result["training_days"] = ", ".join(training_days)
    result["profile_name"] = profile["name"]
    result["profile_slug"] = slug

    return templates.TemplateResponse("result.html", {"request": request, "result": result})


_RACE_DIST_MAP = {
    "half marathon": "half marathon",
    "full marathon": "marathon",
    "marathon":      "marathon",
    "10k":           "10k",
    "5k":            "5k",
}

_SENTIMENT_PRED_MAP = {
    "positive": "positive", "negative": "negative", "neutral":  "neutral",
    "moderate": "neutral",  "hard":     "negative",  "easy":     "positive",
    "struggled":"negative", "good":     "positive",
}


def compute_readiness(request: Request, slug: str, form_data: dict):
    profiles = _load_profiles()
    profile = profiles.get(slug)
    if not profile:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    age         = float(profile.get("age") or form_data.get("age") or 30)
    target_time = form_data.get("target_time", "2:00:00").strip()

    # Build history from run_history (skip entries with missing distance/pace)
    history = [
        {
            "distance_miles": r["distance"],
            "pace_minutes":   r["pace_minutes"],
            "terrain":        r.get("terrain") or "road",
            "sentiment":      _SENTIMENT_PRED_MAP.get(r.get("sentiment", "neutral"), "neutral"),
        }
        for r in profile.get("run_history", [])
        if r.get("distance") and r.get("pace_minutes")
    ]

    # Derive race info from active plan
    active_plan  = profile.get("active_plan") or {}
    raw_dist     = (active_plan.get("race_type") or "half marathon").lower()
    race_dist    = _RACE_DIST_MAP.get(raw_dist, "half marathon")
    race_terrain = (profile.get("available_terrain") or ["road"])[0]

    today        = date.today()
    days_to_race = 0
    if active_plan.get("race_date"):
        try:
            days_to_race = max(0, (date.fromisoformat(active_plan["race_date"]) - today).days)
        except ValueError:
            pass

    # Adherence (reuse same logic as motivation)
    days_per_week  = len(profile.get("training_days", []))
    try:
        created = date.fromisoformat(profile.get("created_at", today.isoformat()))
    except ValueError:
        created = today
    weeks_elapsed  = max(1, (today - created).days / 7)
    adherence      = round(min(len(profile.get("run_history", [])) / max(days_per_week * weeks_elapsed, 1) * 100, 100.0), 1)

    snapshot = {
        "age":               age,
        "experience_level":  profile["experience"],
        "days_to_race":      days_to_race,
        "adherence_percent": adherence,
        "goal_race": {
            "distance":    race_dist,
            "target_time": target_time,
            "terrain":     race_terrain,
        },
        "history": history,
    }

    result = predict_race_readiness(snapshot, auto_train=True)

    profiles[slug]["race_readiness"] = {
        "age":         age,
        "target_time": target_time,
        "snapshot":    _json_safe(snapshot),
        "result":      _json_safe(result),
        "computed_at": today.isoformat(),
    }
    _save_profiles(profiles)
    return RedirectResponse(url=f"/user/{slug}#readiness", status_code=303)


def check_safety(request: Request, slug: str, body: dict):
    from src.module1_safety_validator.validator import validate_workout

    profiles = _load_profiles()
    profile = profiles.get(slug)
    if not profile:
        return JSONResponse({"ok": False, "error": "Profile not found"}, status_code=404)

    today = date.today()
    run_history = profile.get("run_history", [])

    week_start = (today - timedelta(days=today.weekday())).isoformat()
    this_week_runs = [r for r in run_history if r.get("logged_at", "")[:10] >= week_start]
    days_trained = len(this_week_runs)
    rest_days = max(0, today.weekday() + 1 - days_trained)

    _known_injury_keywords = [
        "shin splint", "knee", "plantar", "achilles", "it band", "itb",
        "stress fracture", "fracture", "hip", "hamstring", "calf", "ankle", "back",
    ]
    raw_injuries = body.get("injuries", [])
    injuries = [i for i in raw_injuries if any(k in i.lower() for k in _known_injury_keywords)]

    runner_profile = {
        "injuries":               injuries,
        "symptoms":               [],
        "weekly_mileage":         profile.get("current_weekly_miles", 0),
        "rest_days_this_week":    rest_days,
        "days_trained_this_week": days_trained,
        "available_terrain":      profile.get("available_terrain", ["road"]),
        "experience_level":       profile.get("experience", "beginner"),
        "hydrated":               True,
        "proper_footwear":        True,
        "weather":                "normal",
        "fully_recovered":        True,
        "sleep_quality":          "good",
    }

    proposed_workout = {
        "type":     body.get("workout_type", "easy run"),
        "distance": float(body.get("distance", 5.0)),
        "terrain":  body.get("terrain", (profile.get("available_terrain") or ["road"])[0]),
    }

    try:
        result = validate_workout(runner_profile, proposed_workout)
        return JSONResponse({"ok": True, "result": _json_safe(result)})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})


def list_profiles(request: Request):
    profiles = _load_profiles()
    return templates.TemplateResponse("profiles_list.html", {"request": request, "profiles": list(profiles.values())})


def delete_run(request: Request, slug: str, index: int):
    profiles = _load_profiles()
    profile = profiles.get(slug)
    if not profile:
        return JSONResponse({"ok": False, "error": "Profile not found"}, status_code=404)

    run_history = profile.get("run_history", [])
    if index < 0 or index >= len(run_history):
        return JSONResponse({"ok": False, "error": "Invalid run index"}, status_code=400)

    run_history.pop(index)
    profiles[slug]["run_history"] = run_history
    _save_profiles(profiles)
    return JSONResponse({"ok": True})


def log_run(request: Request, slug: str, text: str):
    profiles = _load_profiles()
    profile = profiles.get(slug)
    if not profile:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    try:
        parsed = _parser.parse(text)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    parsed["logged_at"] = datetime.now().isoformat(timespec="seconds")

    if "run_history" not in profile:
        profile["run_history"] = []
    profile["run_history"].insert(0, parsed)

    profiles[slug] = profile
    _save_profiles(profiles)
    return RedirectResponse(url=f"/user/{slug}", status_code=303)
