# app/infra/calendar/adapters.py
from typing import Iterable, Optional
from app.domain.models import Meeting
from app.infra.calendar import service as cal_service

class InMemoryCalendarAdapter:
    def first_conflict(self, meeting: Meeting) -> Optional[str]:
        return cal_service.first_conflict(meeting)

    def create_event(self, meeting: Meeting) -> None:
        cal_service.create_event(meeting)

    def list_all(self) -> Iterable:
        return cal_service.list_all()
