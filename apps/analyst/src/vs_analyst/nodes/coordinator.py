from typing import Any, Dict
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


def state_router_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    A simple pass-through coordinator node that triggers the dynamic routing decision.
    """
    return {}
