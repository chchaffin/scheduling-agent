# app/application/scheduler_runner.py
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any

from app.application.ports import IO, Calendar
from app.workflows.schedule.state_ops import prepare_retry_patch


class SchedulerRunner:
    """
    Orchestrates the schedule workflow end-to-end:
      - builds initial state
      - runs the graph with a clarify loop
      - asks for confirmation before booking
      - creates the event via the Calendar port

    This class has no printing/input logic of its own; it delegates to IO.
    """

    def __init__(self, graph, io: IO, calendar: Calendar, tz: str = "America/Chicago"):
        """
        Args:
            graph: compiled LangGraph (must expose .invoke(state) -> state)
            io: UI-agnostic I/O port (CLI/web/etc.)
            calendar: Calendar port (in-memory today; swappable later)
            tz: IANA timezone string used for display and time anchoring
        """
        self.graph = graph
        self.io = io
        self.calendar = calendar
        self.tz = tz

    def _initial_state(self, user_text: str) -> Dict[str, Any]:
        """Build a fresh ScheduleState dict."""
        now = datetime.now(ZoneInfo(self.tz))
        return {
            "user_text": user_text,
            "now": now,
            "tz": self.tz,
            "draft": None,
            "meeting": None,
            "errors": [],
            "attempts": 0,
            "conflict": None,
            "clarify": None,
        }

    def schedule(self, user_text: str, *, max_clarify: int = 3) -> Dict[str, Any]:
        """
        Run the scheduling flow. Returns the final state from the graph.
        Side-effects (confirmation prompt, booking, listing events) go through IO/Calendar.

        Flow:
          1) invoke graph
          2) if clarify question present (and no meeting), ask user, update state, retry
          3) once we have a meeting, check conflict (graph already set it)
          4) if no conflict, ask to confirm; create event only on yes
        """
        state = self._initial_state(user_text)
        tries = 0

        # ---- Clarify loop ----
        while True:
            result = self.graph.invoke(state)

            # Need clarification? Ask and retry.
            if result.get("clarify") and not result.get("meeting"):
                tries += 1
                question = result["clarify"]
                answer = self.io.ask(f"🤔 {question}")
                if not answer or answer.lower() in {"q", "quit", "cancel"}:
                    self.io.info("Aborted by user.")
                    return result

                patch = prepare_retry_patch(state["user_text"], answer)
                state = {**state, **patch}

                if tries >= max_clarify:
                    self.io.warn("Too many clarification attempts. Try rephrasing your request.")
                    return result
                continue

            # No clarification requested → proceed
            break

        meeting = result.get("meeting")
        conflict = result.get("conflict")
        errors = result.get("errors")

        # ---- No meeting extracted → report and exit ----
        if not meeting:
            self.io.warn("Could not extract a valid meeting.")
            if result.get("clarify"):
                self.io.info(f"Clarify: {result['clarify']}")
            if errors:
                self.io.info("Errors:")
                for e in errors:
                    self.io.info(f"  {str(e)[:500]}")
            return result

        summary = result.get("review")
        if not summary:
            # Hard fail is fine for a greenfield project; it protects the invariant.
            raise RuntimeError("Graph invariant violated: meeting present but review missing")

        # ---- Conflict present → show summary + events; do not book ----
        if conflict:
            self.io.warn(f"Conflict detected:\n  {conflict}")
            self.io.review_summary(summary)
            self.io.list_events(self.calendar.list_all(), self.tz)
            return result

        # ---- Confirm before booking ----
        self.io.review_summary(summary)
        if self.io.confirm("Book this on the calendar?"):
            self.calendar.create_event(meeting)
            self.io.info("📅 Event created.")
        else:
            self.io.info("Okay — not booked.")

        # Show current calendar (for CLI UX)
        self.io.list_events(self.calendar.list_all(), self.tz)
        return result

    def list_events(self) -> None:
        """Convenience for the CLI 'list' command."""
        self.io.list_events(self.calendar.list_all(), self.tz)
