# app/schemas/runlog.py
from pydantic import BaseModel, Field

class RunLogParseRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Free-form run description text")

class RunLogParseResponse(BaseModel):
    result: dict