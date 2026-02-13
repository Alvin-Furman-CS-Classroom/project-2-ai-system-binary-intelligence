from fastapi import FastAPI
from routers.plans import  router as plans_router

app = FastAPI()

app.include_router(plans_router)

@app.get("/")
def root():
    return {"status": "ok"}