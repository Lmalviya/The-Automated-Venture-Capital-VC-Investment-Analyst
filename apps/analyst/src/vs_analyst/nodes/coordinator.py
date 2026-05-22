from typing import Any, Dict
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

async def map_market_complete_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Runs after the market agent finishes.
    Marks market as COMPLETE.
    """
    analysis_state = state["analysis_state"]
    logger.info("Market agent complete", run_id=analysis_state.run_id)
    analysis_state.agent_statuses["market"] = AgentStatus.COMPLETE
    return {"analysis_state": analysis_state}


def state_router_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    A simple pass-through coordinator node that triggers the dynamic routing decision.
    """
    return {}
