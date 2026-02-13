from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class WorkoutInput(BaseModel):
    type: str = Field(..., description='e.g. "easy run"|"long run"|"tempo"|"intervals"')
    distance: float = Field(..., ge=0)
    terrain: str = Field(..., description='e.g. "track"|"road"|"trail"|"treadmill"')


class ProfileInput(BaseModel):
    # Keep as flexible as your validator expects.
    # If you want strict typing, we can tighten this later.
    symptoms: List[str] = []
    injuries: List[str] = []
    pain_level: Optional[str] = None
    cleared_by_doctor: Optional[bool] = None
    fully_recovered: Optional[bool] = None
    sleep_quality: Optional[str] = None
    rest_days_this_week: Optional[int] = None
    days_trained_this_week: Optional[int] = None
    hard_workout_yesterday: Optional[bool] = None
    weekly_mileage: Optional[float] = None
    experience_level: Optional[str] = None
    race_date: Optional[Union[str, None]] = None
    weather: Optional[str] = None
    hydrated: Optional[bool] = None
    proper_footwear: Optional[bool] = None
    available_terrain: Optional[List[str]] = None

    # Allow extra keys without breaking
    model_config = {"extra": "allow"}



class ValidateRequest(BaseModel):
    injuries: List[str]
    weekly_mileage: float
    rest_days_this_week: int
    available_terrain: List[str]
    proposed_workout: Dict[str, Any]
    debug: bool = False


class BatchValidateRequest(BaseModel):
    profile: ProfileInput
    workouts: List[WorkoutInput]
    debug: bool = False


class QuickValidateRequest(BaseModel):
    injuries: List[str] = []
    workout_type: str
    distance: float
    terrain: str
    weekly_mileage: float
