from typing import List
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from controllers.profile_controller import (
    show_create_form, create_profile, show_profile, generate_plan,
    list_profiles, log_run, delete_run, compute_readiness, get_progression_json, check_safety,
    get_motivation_history,
)

router = APIRouter()


@router.get("/profiles", response_class=HTMLResponse)
def get_profiles(request: Request):
    return list_profiles(request)


@router.get("/profile/new", response_class=HTMLResponse)
def get_create_form(request: Request):
    return show_create_form(request)


@router.post("/profile/new")
def post_create_form(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    experience: str = Form(...),
    current_weekly_miles: float = Form(...),
    available_terrain: List[str] = Form(...),
    training_days: List[str] = Form(...),
):
    return create_profile(request, {
        "name": name,
        "age": age,
        "experience": experience,
        "current_weekly_miles": current_weekly_miles,
        "available_terrain": available_terrain,
        "training_days": training_days,
    })


@router.get("/user/{slug}", response_class=HTMLResponse)
def get_profile(request: Request, slug: str):
    return show_profile(request, slug)


@router.post("/user/{slug}/plan", response_class=HTMLResponse)
def post_generate_plan(
    request: Request,
    slug: str,
    race_type: str = Form(...),
    race_date: str = Form(...),
):
    return generate_plan(request, slug, {"race_type": race_type, "race_date": race_date})


@router.delete("/user/{slug}/runlog/{index}")
def delete_run_entry(request: Request, slug: str, index: int):
    return delete_run(request, slug, index)


@router.post("/user/{slug}/runlog")
def post_log_run(
    request: Request,
    slug: str,
    text: str = Form(...),
):
    return log_run(request, slug, text)


@router.get("/user/{slug}/progression")
def get_progression(request: Request, slug: str):
    return get_progression_json(request, slug)


@router.post("/user/{slug}/safety")
async def post_safety_check(request: Request, slug: str):
    body = await request.json()
    return check_safety(request, slug, body)


@router.get("/user/{slug}/motivation")
def get_motivation_history_route(request: Request, slug: str, run_index: int = 0):
    return get_motivation_history(request, slug, run_index)


@router.post("/user/{slug}/readiness")
def post_compute_readiness(
    request: Request,
    slug: str,
    age: float = Form(...),
    target_time: str = Form(...),
):
    return compute_readiness(request, slug, {"age": age, "target_time": target_time})
