from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from controllers.adaptive_progression_controller import show_demo, handle_custom

router = APIRouter()


@router.get("/progression/demo", response_class=HTMLResponse)
def get_demo(request: Request):
    return show_demo(request)


@router.post("/progression/custom", response_class=HTMLResponse)
async def post_custom(request: Request):
    form = await request.form()
    form_data = dict(form)
    return handle_custom(request, form_data)
