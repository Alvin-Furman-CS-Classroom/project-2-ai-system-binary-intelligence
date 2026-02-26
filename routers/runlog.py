from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from schemas.runlog import RunLogParseRequest, RunLogParseResponse
from controllers.runlog_controller import parse_runlog

router = APIRouter(tags=["runlog"])

templates = Jinja2Templates(directory="templates")


@router.get("/runlog", response_class=HTMLResponse)
def runlog_page(request: Request):
    return templates.TemplateResponse("runlog.html", {"request": request})


@router.post("/runlog/parse", response_model=RunLogParseResponse)
def parse_runlog_route(payload: RunLogParseRequest) -> RunLogParseResponse:
    result = parse_runlog(payload.text)
    return RunLogParseResponse(result=result)