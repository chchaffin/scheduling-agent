# app/workflows/schedule/nodes/review.py
from __future__ import annotations
from typing import Dict, Any
from zoneinfo import ZoneInfo
from app.workflows.schedule.state import ScheduleState

class ReviewNode:
    """
    Produces a small, human-friendly summary of the normalized meeting.
    This does NOT book anything and has no external deps.
    It returns a PATCH: {"review": {...}}.
    """

    def __call__(self, state: ScheduleState) -> Dict[str, Any]:
        meeting = state.get("meeting")
        if not meeting:
            # Nothing to summarize; return an empty patch
            return {}

        tzname = state.get("tz", "America/Chicago")
        start_local = meeting.starts_at.astimezone(ZoneInfo(tzname))

        summary = {
            "title": meeting.title,
            "when": start_local.isoformat(timespec="minutes"),
            "duration_min": meeting.duration_min,
            "location": meeting.location,
        }

        return {"review": summary}
