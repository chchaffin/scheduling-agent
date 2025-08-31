# app/workflows/schedule/nodes/act.py
from app.infra.calendar.service import create_event
from app.workflows.schedule.state import ScheduleState

def act_node(state: ScheduleState) -> ScheduleState:
    if not state["conflict"]:
        create_event(state["meeting"])
    return state