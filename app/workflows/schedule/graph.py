# app/workflows/schedule/graph.py
from __future__ import annotations
from functools import partial
from typing import List

from langgraph.graph import StateGraph, START, END

from .state import ScheduleState
from .nodes.extract import ExtractNode          # unchanged
from .nodes.validate import validate_node       # unchanged
from .nodes.repair import RepairNode            # unchanged
from .nodes.clarify import clarify_node         # unchanged
from .nodes.conflict import conflict_node       # unchanged
from .nodes.review import ReviewNode            # <-- NEW import

from app.infra.llm.types import LLMClient, ExtractOptions


# ---------- Routing helpers (unchanged except for target name) ----------

def _is_fixable(errors: List[str]) -> bool:
    blob = " ".join(errors).lower()
    structural = any(k in blob for k in [
        "extra fields", "field required", "type_error", "value is not a valid"
    ])
    semantic = any(k in blob for k in [
        "ambiguous", "date", "duration <= 0", "multiple values", "past"
    ])
    return structural and not semantic

def route_after_validate(state: ScheduleState) -> str:
    # If we have a normalized Meeting, go to REVIEW first (not straight to conflict)
    if state["meeting"] is not None:
        return "review"
    if state["errors"] and _is_fixable(state["errors"]) and state["attempts"] < 2:
        return "repair"
    return "clarify"

def route_after_conflict(state: ScheduleState) -> str:
    return "end" if state["conflict"] else "end"  # we still END after conflict; booking happens outside


# ---------- Graph assembly ----------

def build_graph(llm: LLMClient, options: ExtractOptions):
    g = StateGraph(ScheduleState)

    # Nodes
    g.add_node("extract", ExtractNode(llm, options))
    g.add_node("validate", validate_node)
    g.add_node("repair",  RepairNode(llm, options))
    g.add_node("clarify", clarify_node)
    g.add_node("review",  ReviewNode())
    g.add_node("conflict", conflict_node)

    # Entrypoint
    g.add_edge(START, "extract")

    # Flow: extract -> validate
    g.add_edge("extract", "validate")

    # After validate: review | repair | clarify
    g.add_conditional_edges(
        "validate",
        route_after_validate,
        {
            "review": "review",
            "repair": "repair",
            "clarify": "clarify",
        },
    )

    # After review: always check conflicts
    g.add_edge("review", "conflict")           # <-- NEW edge

    # After conflict: stop (runner handles confirmation/booking)
    g.add_conditional_edges("conflict", route_after_conflict, {"end": END})

    # After repair: validate again or clarify
    def route_after_repair(state: ScheduleState) -> str:
        return "validate" if state["attempts"] < 2 else "clarify"

    g.add_conditional_edges("repair", route_after_repair, {
        "validate": "validate",
        "clarify": "clarify",
    })

    return g.compile()
