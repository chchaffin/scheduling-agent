# app/workflows/schedule/nodes/clarify.py
from __future__ import annotations
from typing import Dict, Any, List
from app.workflows.schedule.state import ScheduleState

MISSING_KEYS_HINTS = {
    "ambiguous_datetime": "The date/time is ambiguous—what should I use?",
    "starts_at": "What date and time should I use?",
    "duration_min": "How long should it be (in minutes)?",
    "title": "What should I title this?",
}

def _pick_clarify_question(errors: List[str]) -> str:
    """
    Very small heuristic: look for 'field required' or 'value is not a valid' on key fields
    and return a single, specific question. Fall back to a generic ask.
    """
    blob = " ".join(errors).lower() if errors else ""
    # required field hints
    for key, q in MISSING_KEYS_HINTS.items():
        if f'"{key}"' in blob and "field required" in blob:
            return q
    # invalid datetime hint
    if "starts_at" in blob and ("not a valid" in blob or "date" in blob or "time" in blob or "ambiguous" in blob):
        return "I couldn’t resolve the date/time—what should I use?"
    # invalid duration hint
    if "duration_min" in blob and ("not a valid" in blob or "<= 0" in blob):
        return "What duration (in minutes) should I use?"
    # generic
    return "I’m missing something—could you clarify the date/time or duration?"

def clarify_node(state: ScheduleState) -> Dict[str, Any]:
    """
    Populate a short 'clarify' question based on validation errors so the caller (CLI/UI)
    can ask the user and re-run the graph with the updated text.
    """
    question = _pick_clarify_question(state.get("errors", []))
    # Return a PATCH (don’t overwrite unrelated keys)
    return {"clarify": question}
