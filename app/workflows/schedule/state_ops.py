# app/workflows/schedule/state_ops.py
"""
Pure, reusable helpers for ScheduleState updates.
Each function returns a PATCH (dict of keys to update), not a whole state.
"""

from __future__ import annotations
from typing import Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo
from app.domain.models import Meeting

# ----- Clarify / retry helpers -----

def append_answer_to_text(user_text: str, answer: str) -> Dict[str, Any]:
    """
    Combine the user's original request with a clarification answer.
    Keep this dumb/simple: append with a space.
    """
    answer = (answer or "").strip()
    if not answer:
        return {}
    return {"user_text": (user_text + " " + answer).strip()}

def clear_transients_for_retry() -> Dict[str, Any]:
    """
    Reset fields that should not carry across a new extract attempt.
    """
    return {
        "draft": None,
        "meeting": None,
        "errors": [],
        "attempts": 0,
        "clarify": None,
    }

def prepare_retry_patch(user_text: str, answer: str) -> Dict[str, Any]:
    """
    One-stop shop for the clarify loop: append the answer and clear transients.
    """
    patch = {}
    patch.update(append_answer_to_text(user_text, answer))
    patch.update(clear_transients_for_retry())
    return patch

# ----- Optional: confirmation / review helpers -----

def summarize_for_review(meeting: Meeting, tz: str = "America/Chicago") -> Dict[str, Any]:
    """
    Build a lightweight, human-friendly summary you can print in CLI/UI.
    Kept here so nodes or main can both use it.
    """
    tzinfo = ZoneInfo(tz)
    start_local = meeting.starts_at.astimezone(tzinfo)
    return {
        "review": {
            "title": meeting.title,
            "when_iso": start_local.isoformat(),
            "duration_min": meeting.duration_min,
            "location": meeting.location,
        }
    }

def mark_confirmation_needed() -> Dict[str, Any]:
    return {"needs_confirmation": True}

def mark_confirmed() -> Dict[str, Any]:
    return {"confirmed": True}
