from typing import List
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from controllers.plans_controller import show_form, handle_form, generate_for_user

router = APIRouter()


@router.get("/plans", response_class=HTMLResponse)
def get_form(request: Request):
    return show_form(request)


@router.post("/plans", response_class=HTMLResponse)
def submit_form(
    request: Request,
    race_type: str = Form(...),
    race_date: str = Form(...),
    training_days: List[str] = Form(...),
    current_weekly_miles: float = Form(...),
    experience: str = Form(...),
    terrain: List[str] = Form(...)
):
    form_data = {
        "race_type": race_type,
        "race_date": race_date,
        "training_days": training_days,
        "days_per_week": len(training_days),  # Calculate from selected days
        "current_weekly_miles": current_weekly_miles,
        "experience": experience,
        "available_terrain": terrain,
    }
    return handle_form(request, form_data)


@router.get("/user/{name}", response_class=HTMLResponse)
def user_plan(request: Request, name: str):
    return generate_for_user(request, name)
