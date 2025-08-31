# app/workflows/schedule/nodes/validate.py
from pydantic import ValidationError
from app.contracts.extraction import MeetingRequest
from app.domain.models import Meeting
from app.workflows.schedule.state import ScheduleState

def validate_node(state: ScheduleState) -> ScheduleState:
    try:
        draft = MeetingRequest.model_validate(state["draft"])
        meeting = Meeting.model_validate(draft.model_dump(), context={"now": state["now"], "tz": state["tz"]})
        return {**state, "meeting": meeting, "errors": []}
    except ValidationError as e:
        return {**state, "meeting": None, "errors": [e.json()]}
