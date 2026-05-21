from typing import Literal
from vs_analyst.schemas.state import PipelineGraphState

# =========================================================
# Routing Logic
# =========================================================

def should_continue(state: PipelineGraphState) -> Literal["tools", "complete"]:
    """
    Generic routing edge used by both agents.
    If the last message has tool_calls → route to tools node.
    Otherwise → route to the completion/mapping node.
    """
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return "complete"