from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from routers.plans import  router as plans_router
from routers.safety_validator_router import router as safety_validator_router
from routers.runlog import router as runlog_router
from routers.motivation_selector_route import router as motivation_router
from routers.adaptive_progression_route import router as adaptive_router
from routers.race_predictor_route import router as race_router


app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.include_router(plans_router)
app.include_router(safety_validator_router)
app.include_router(runlog_router)
app.include_router(motivation_router)
app.include_router(adaptive_router)
app.include_router(race_router)

@app.exception_handler(404)
async def not_found_handler(request: Request, _exc: HTTPException):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})