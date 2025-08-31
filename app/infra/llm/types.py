# app/infra/llm/types.py
from dataclasses import dataclass
from typing import Optional, List, Protocol, runtime_checkable, Dict, Any

@dataclass(frozen=True, slots=True)
class ExtractOptions:
    system: Optional[str] = None        # workflow/system prompt (optional override)
    instructions: str = ""              # task prompt (e.g., "extract meeting fields…")
    guardrail: str = ""                 # shared JSON-only fragment
    examples: Optional[List[str]] = None  # optional few-shot JSON strings

@runtime_checkable
class LLMClient(Protocol):
    def structured_extract(self, *, user_text: str, schema: Dict[str, Any],
                           options: ExtractOptions) -> Dict[str, Any]: ...
    def repair_to_schema(self, *, previous: Dict[str, Any], errors: List[str],
                         schema: Dict[str, Any], options: ExtractOptions) -> Dict[str, Any]: ...
