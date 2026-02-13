from fastapi import FastAPI
from routers.plans import  router as plans_router
from routers.safety_validator_router import router as safety_validator_router

app = FastAPI()

app.include_router(plans_router)
app.include_router(safety_validator_router)

@app.get("/")
def root():
    return {"status": "ok"}