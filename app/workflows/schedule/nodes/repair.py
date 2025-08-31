from typing import Dict, Any
from app.infra.llm.types import LLMClient, ExtractOptions
from app.contracts.extraction import MeetingRequest
from app.workflows.schedule.state import ScheduleState

class RepairNode:
    def __init__(self, llm: LLMClient, options: ExtractOptions):
        self.llm = llm
        self.options = options

    def __call__(self, state: ScheduleState) -> Dict[str, Any]:
        """
        Called when validate_node failed. We feed the previous 'draft' JSON and
        the Pydantic error messages back to the LLM, along with the SAME prompt
        framing (system + guardrail) so it can correct the JSON to the schema.
        """
        # 1) Build/obtain the same schema used in extract
        schema = MeetingRequest.model_json_schema()

        # 2) Call adapter's repair using the injected prompts
        fixed = self.llm.repair_to_schema(
            previous=state["draft"] or {},  # last LLM JSON (might be None on weird runs)
            errors=state["errors"],  # Pydantic errors from validate_node
            schema=schema,
            options=self.options,  # <- this carries system + guardrail (+ examples/instructions if you want)
        )

        # 3) Return a *patch*: bump attempts by +1 and replace the draft
        #    (attempts is Annotated[int, operator.add] in the TypedDict, so +1 is merged additively)
        return {"attempts": 1, "draft": fixed}