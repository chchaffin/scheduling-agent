# app/domain/models.py
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator, ValidationInfo
from zoneinfo import ZoneInfo
from dateutil import parser as dateparse

class Attendee(BaseModel):
    name: str
    email: Optional[str] = None

class Meeting(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str
    starts_at: datetime
    duration_min: int
    location: Optional[str] = None
    attendees: List[Attendee] = []
    priority: Literal["low", "normal", "high"] = "normal"

    @field_validator("starts_at", mode="before")
    @classmethod
    def parse_human_time(cls, v, info: ValidationInfo):
        """
        Parse human time strings anchored to 'now'/'tz', but:
        - use a midnight baseline so unspecified fields don't inherit current mm:ss.us
        - force tz
        - zero out seconds/microseconds for clean scheduling slots
        """
        ctx = info.context or {}
        tzname = ctx.get("tz", "America/Chicago")
        now = ctx.get("now") or datetime.now(ZoneInfo(tzname))
        tz = ZoneInfo(tzname)

        raw = str(v)

        # 1) Midnight baseline prevents leaking current minutes/seconds into the result
        baseline = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # 2) Parse with dateutil (still accepts e.g. "12pm", "next Tue 9:30" if supported)
        dt = dateparse.parse(raw, default=baseline, fuzzy=True)

        # 3) Ensure timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        else:
            dt = dt.astimezone(tz)

        # 4) Normalize to minute precision (drop seconds/microseconds)
        dt = dt.replace(second=0, microsecond=0)
        return dt
