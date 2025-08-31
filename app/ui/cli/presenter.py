# app/ui/cli/presenter.py
from typing import Iterable
from zoneinfo import ZoneInfo

def meeting_summary_lines(meeting, tz: str) -> list[str]:
    tzinfo = ZoneInfo(tz)
    start_local = meeting.starts_at.astimezone(tzinfo)
    return [
        f"Title:    {meeting.title}",
        f"When:     {start_local.isoformat()}  ({meeting.duration_min} min)",
        f"Location: {meeting.location or '—'}",
    ]

def print_events(events: Iterable, tz: str) -> None:
    tzinfo = ZoneInfo(tz)
    evs = list(events)
    if not evs:
        print("\nCalendar is empty.")
        return
    print("\nCurrent in-memory events:")
    for e in evs:
        s = e.starts_at.astimezone(tzinfo).isoformat()
        en = e.ends_at.astimezone(tzinfo).isoformat()
        print(f"- #{e.id} {e.title} @ {s} – {en} ({e.location or 'no location'})")
