from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app_templates import templates

from controllers.safety_validator_controller import (
    run_validate,
    run_batch_validate,
    run_quick_validate,
)

from schemas.safety_validator_schemas import (
    ValidateRequest,
    BatchValidateRequest,
    QuickValidateRequest,
)

router = APIRouter(prefix="/safety-validator", tags=["safety-validator"])


# ✅ HTML page route
@router.get("/", response_class=HTMLResponse)
def validator_page(request: Request):
    return templates.TemplateResponse("validator.html", {"request": request})


# ✅ API routes
@router.post("/validate")
def validate(req: ValidateRequest):
    data = req.model_dump()
    proposed_workout = data.pop("proposed_workout")
    debug = data.pop("debug")

    runner_profile = data

    return run_validate(
        runner_profile=runner_profile,
        proposed_workout=proposed_workout,
        debug=debug
    )


@router.post("/batch-validate")
def batch_validate(req: BatchValidateRequest):
    return run_batch_validate(
        profile=req.profile.model_dump(),
        workouts=[w.model_dump() for w in req.workouts],
        debug=req.debug,
    )


@router.post("/quick-validate")
def quick_validate(req: QuickValidateRequest):
    return {
        "safe": run_quick_validate(
            injuries=req.injuries,
            workout_type=req.workout_type,
            distance=req.distance,
            terrain=req.terrain,
            weekly_mileage=req.weekly_mileage,
        )
    }
