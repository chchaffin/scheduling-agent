# nodes/extract.py
from app.infra.llm.types import LLMClient, ExtractOptions
from app.contracts.extraction import MeetingRequest

class ExtractNode:
    def __init__(self, llm: LLMClient, options: ExtractOptions):
        self.llm = llm
        self.options = options

    def __call__(self, state):
        data = self.llm.structured_extract(
            user_text=state["user_text"],
            schema=MeetingRequest.model_json_schema(),
            options=self.options,
        )
        return {"draft": data}
