# app/ui/cli/io.py
from typing import Iterable
from app.application.ports import IO
from app.ui.cli.presenter import meeting_summary_lines, print_events

class CLIIO(IO):
    def ask(self, prompt: str) -> str:
        print(prompt)
        return input("> ").strip()

    def info(self, msg: str) -> None:
        print(msg)

    def warn(self, msg: str) -> None:
        print(f"⚠ {msg}")

    def confirm(self, prompt: str) -> bool:
        ans = self.ask(f"{prompt} (y/N)")
        return ans.lower() in {"y", "yes"}

    def list_events(self, events: Iterable, tz: str) -> None:
        print_events(events, tz)

    def review_summary(self, summary: dict) -> None:
        print("✓ Parsed & normalized meeting (review before booking):")
        title = summary.get("title", "—")
        when = summary.get("when", "—")
        dur  = summary.get("duration_min")
        loc  = summary.get("location") or "—"
        dur_str = f"{dur} min" if dur is not None else "—"
        print(f"  Title:    {title}")
        print(f"  When:     {when}  ({dur_str})")
        print(f"  Location: {loc}")