from __future__ import annotations
import argparse
from pathlib import Path

from app.application.scheduler_runner import SchedulerRunner
# Graph & LLM
from app.workflows.schedule.graph import build_graph
from app.infra.llm.ollama_client import OllamaClient
from app.infra.llm.types import ExtractOptions

# Ports & runner
from app.ui.cli.io import CLIIO
from app.infra.calendar.adapters import InMemoryCalendarAdapter

# ---- prompt loading (assembly-time, not business logic) ----
PROMPTS_DIR = Path("app/prompts")

def _read(p: Path, default: str = "") -> str:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        return default

def load_extract_options() -> ExtractOptions:
    system = _read(PROMPTS_DIR / "schedule" / "system.md",
                   "You are a precise extraction assistant for scheduling.")
    instructions = _read(PROMPTS_DIR / "schedule" / "extract.md",
                         "Extract meeting fields per the provided JSON Schema.")
    guardrail = _read(PROMPTS_DIR / "_fragments" / "json_only.md",
                      "Return ONLY a single JSON object that matches the schema; no extra keys.")
    return ExtractOptions(system=system, instructions=instructions, guardrail=guardrail)

def build_runner(tz: str, model: str, temperature: float) -> SchedulerRunner:
    # LLM + options
    llm = OllamaClient(model=model, temperature=temperature)
    options = load_extract_options()

    # Compile workflow graph with DI
    graph = build_graph(llm, options)

    # IO & Calendar adapters
    io = CLIIO()
    calendar = InMemoryCalendarAdapter()

    return SchedulerRunner(graph=graph, io=io, calendar=calendar, tz=tz)

def main():
    ap = argparse.ArgumentParser(prog="scheduler")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_sched = sub.add_parser("schedule", help="Schedule from natural language")
    p_sched.add_argument("text", nargs="+", help='e.g. "Lunch with Sarah tomorrow 1pm for 90 minutes at the office"')
    p_sched.add_argument("--tz", default="America/Chicago")
    p_sched.add_argument("--model", default="mistral:7b")
    p_sched.add_argument("--temp", type=float, default=0.2)

    sub.add_parser("list", help="List events")

    args = ap.parse_args()
    runner = build_runner(tz=args.tz, model=getattr(args, "model", "mistral:7b"), temperature=getattr(args, "temp", 0.2))

    if args.cmd == "schedule":
        runner.schedule(" ".join(args.text))
    elif args.cmd == "list":
        runner.list_events()

if __name__ == "__main__":
    main()
