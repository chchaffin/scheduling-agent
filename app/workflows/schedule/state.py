from typing import TypedDict, Optional, Dict, Any, List
from datetime import datetime
from app.domain.models import Meeting
from typing_extensions import Annotated
import operator

class ScheduleState(TypedDict):
    user_text: str             # NL input
    now: datetime              # anchor "today/now"
    tz: str                    # e.g. "America/Chicago"
    draft: Optional[Dict[str, Any]]   # raw JSON from the LLM
    meeting: Optional[Meeting]        # normalized domain object
    errors: List[str]          # validation errors (replace semantics)
    attempts: Annotated[int, operator.add]  # <-- additive merge
    conflict: Optional[str]    # text description or None
    clarify: Optional[str]     # when we need more info, nodes set a short, direct question here
    review: Optional[Dict[str, Any]]