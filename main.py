from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from routers.plans import  router as plans_router
from routers.safety_validator_router import router as safety_validator_router
from routers.runlog import router as runlog_router


app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.include_router(plans_router)
app.include_router(safety_validator_router)
app.include_router(runlog_router)

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})