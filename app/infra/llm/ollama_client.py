from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any, List, Optional
import json, re
from app.infra.llm.types import LLMClient, ExtractOptions

def _minify_schema(d: Dict[str, Any]) -> str:
    return json.dumps(d, separators=(",", ":"))

def _extract_first_json(text: str) -> str:
    t = text.strip()
    if t.startswith("{") and t.endswith("}"):
        return t
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.IGNORECASE | re.MULTILINE)
    m = re.search(r"\{.*}", t, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON object found in model output")
    return m.group(0)

def _compose_human(*, user_text: str, schema: Dict[str, Any], opt: ExtractOptions) -> str:
    parts: List[str] = []
    if opt.guardrail:
        parts.append(opt.guardrail.strip())
    if opt.instructions:
        parts.append(opt.instructions.strip())
    if opt.examples:
        parts.append("EXAMPLES:\n" + "\n".join(opt.examples))
    parts.append("SCHEMA:\n" + _minify_schema(schema))
    parts.append("TEXT:\n" + user_text)
    return "\n\n".join(parts)

class OllamaClient:
    def __init__(self, default_system: Optional[str] = None,
                 model: str = "mistral:7b", temperature: float = 0.2):
        self._default_system = default_system or ""
        base = ChatOllama(model=model, temperature=temperature)
        try:
            self._llm_json = base.bind(format="json")  # prefer JSON mode if available
        except Exception:
            self._llm_json = base

    def structured_extract(self, *, user_text: str, schema: Dict[str, Any],
                           options: ExtractOptions) -> Dict[str, Any]:
        sys = options.system or self._default_system
        human = _compose_human(user_text=user_text, schema=schema, opt=options)
        resp = self._llm_json.invoke([SystemMessage(content=sys), HumanMessage(content=human)])
        raw = getattr(resp, "content", str(resp))
        return json.loads(_extract_first_json(raw))

    def repair_to_schema(self, *, previous: Dict[str, Any], errors: List[str],
                         schema: Dict[str, Any], options: ExtractOptions) -> Dict[str, Any]:
        sys = options.system or self._default_system
        body = []
        if options.guardrail:
            body.append(options.guardrail.strip())
        body.append("You previously returned this JSON:")
        body.append(json.dumps(previous, separators=(",", ":")))
        body.append("Validation errors:")
        body.append("\n".join(errors))
        body.append("Correct it so it conforms to the following schema (preserve correct fields):")
        body.append(_minify_schema(schema))
        resp = self._llm_json.invoke([SystemMessage(content=sys), HumanMessage(content="\n\n".join(body))])
        raw = getattr(resp, "content", str(resp))
        return json.loads(_extract_first_json(raw))
