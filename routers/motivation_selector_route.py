from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from controllers.motiation_selector import show_demo, handle_custom

router = APIRouter()


@router.get("/motivation/demo", response_class=HTMLResponse)
def get_demo(request: Request):
    return show_demo(request)


@router.post("/motivation/custom", response_class=HTMLResponse)
def post_custom(
    request: Request,
    current_streak: int = Form(...),
    recent_sentiments: str = Form(...),
    terrain_last_week: str = Form(...),
    adherence_percent: float = Form(...),
    days_to_race: int = Form(...),
):
    form_data = {
        "current_streak": current_streak,
        "recent_sentiments": recent_sentiments,
        "terrain_last_week": terrain_last_week,
        "adherence_percent": adherence_percent,
        "days_to_race": days_to_race,
    }
    return handle_custom(request, form_data)
