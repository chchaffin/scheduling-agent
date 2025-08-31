# app/workflows/schedule/nodes/routing.py
from app.workflows.schedule.state import ScheduleState

def route_after_validate(state: ScheduleState) -> str:
    if state["meeting"] is not None:
        return "conflict"
    blob = " ".join(state["errors"]).lower()
    structural = any(k in blob for k in ["extra fields", "field required", "type_error"])
    return "repair" if structural and state["attempts"] < 2 else "clarify"

def route_after_conflict(state: ScheduleState) -> str:
    return "act" if not state["conflict"] else "__END__"
