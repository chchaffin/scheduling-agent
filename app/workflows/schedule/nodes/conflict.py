# app/workflows/schedule/nodes/conflict.py
from app.workflows.schedule.state import ScheduleState
from app.infra.calendar.service import first_conflict

def conflict_node(state: ScheduleState) -> ScheduleState:
    conflict = first_conflict(state["meeting"])
    return {**state, "conflict": conflict}

