# app/contracts/extraction.py
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict

class AttendeeIn(BaseModel):
    name: str
    email: Optional[str] = None

class MeetingRequest(BaseModel):
    """
    LLM-facing schema (shape only). No date parsing here—keep it simple for the model.
    """
    model_config = ConfigDict(extra='forbid')
    title: str = Field(min_length=3)
    starts_at: str = Field(description="e.g. 'tomorrow 1pm', 'next Tue 9:30'")
    duration_min: int = Field(gt=0)
    location: Optional[str] = None
    attendees: List[AttendeeIn] = []
    priority: Literal["low", "normal", "high"] = "normal"
