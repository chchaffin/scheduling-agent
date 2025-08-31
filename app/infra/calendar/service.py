# app/infra/calendar/service.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import itertools
import threading

from app.domain.models import Meeting

def _to_utc(dt: datetime) -> datetime:
    """Convert any datetime (naive or aware) to aware UTC."""
    if dt.tzinfo is None:
        # If you *prefer* to assume a local TZ for naive inputs, change this line.
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

@dataclass
class Event:
    id: int
    title: str
    starts_at: datetime   # always UTC (tz-aware)
    ends_at: datetime     # always UTC (tz-aware)
    location: Optional[str] = None
    raw: Meeting = field(repr=False, compare=False, default=None)

class InMemoryCalendar:
    def __init__(self):
        self._lock = threading.Lock()
        self._seq = itertools.count(start=1)
        self._events: List[Event] = []

    def list_events(self, start: datetime, end: datetime) -> List[Event]:
        start_utc = _to_utc(start)
        end_utc = _to_utc(end)
        with self._lock:
            return [
                e for e in self._events
                if not (e.ends_at <= start_utc or e.starts_at >= end_utc)
            ]

    def create_event(self, meeting: Meeting) -> Event:
        start_utc = _to_utc(meeting.starts_at)
        end_utc = start_utc + timedelta(minutes=meeting.duration_min)
        with self._lock:
            ev = Event(
                id=next(self._seq),
                title=meeting.title,
                starts_at=start_utc,
                ends_at=end_utc,
                location=meeting.location,
                raw=meeting,
            )
            self._events.append(ev)
            return ev

    def first_conflict(self, meeting: Meeting) -> Optional[str]:
        start_utc = _to_utc(meeting.starts_at)
        end_utc = start_utc + timedelta(minutes=meeting.duration_min)
        with self._lock:
            for e in self._events:
                if start_utc < e.ends_at and e.starts_at < end_utc:
                    return (
                        f"Conflicts with event #{e.id} “{e.title}” "
                        f"{e.starts_at.isoformat()}–{e.ends_at.isoformat()} UTC"
                    )
        return None

# Singleton + helpers
_CAL = InMemoryCalendar()

def first_conflict(meeting: Meeting) -> Optional[str]:
    return _CAL.first_conflict(meeting)

def create_event(meeting: Meeting):
    return _CAL.create_event(meeting)

def list_all() -> List[Event]:
    return _CAL.list_events(
        datetime.min.replace(tzinfo=timezone.utc),
        datetime.max.replace(tzinfo=timezone.utc),
    )
