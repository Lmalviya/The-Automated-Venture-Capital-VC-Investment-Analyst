from typing import Any, Dict
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.schemas.shared_enums import PipelineStatus
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


def state_router_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    A simple pass-through coordinator node that triggers the dynamic routing decision.
    """
    return {}


def abort_pipeline_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Logs a critical error and aborts the pipeline execution.
    """
    analysis_state = state["analysis_state"]
    analysis_state.status = PipelineStatus.FAILED
    logger.error("Pipeline aborted due to critical ingestion or validation failure.", run_id=analysis_state.run_id)
    return {"analysis_state": analysis_state}
