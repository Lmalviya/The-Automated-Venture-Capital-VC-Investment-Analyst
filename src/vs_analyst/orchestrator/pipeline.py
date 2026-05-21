from typing import Any, Dict

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from vs_analyst.managers.intake import IntakeManager, intake_agent_node
from vs_analyst.managers.market import MarketManager, market_agent_node

from vs_analyst.orchestrator.routing_helper import should_continue

from vs_analyst.schemas.competitive import CompetitorSchema
from vs_analyst.schemas.founder import Education, FounderSchema
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.schemas.state import AnalysisState, PipelineGraphState


from vs_analyst.orchestrator.helper import _map_intake_output_to_state

from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

# =========================================================
# Tool Nodes (separate per agent for clean isolation)
# =========================================================
intake_tools_node = ToolNode(IntakeManager.tools)
market_tools_node = ToolNode(MarketManager.tools)


# =========================================================
# Mapping & Completion Nodes
# =========================================================

async def map_intake_complete_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Runs after the intake agent finishes all tool calls.
    Maps the full extraction result into AnalysisState and marks intake COMPLETE.
    """
    analysis_state = state["analysis_state"]
    logger.info("Mapping intake output to AnalysisState", run_id=analysis_state.run_id)

    _map_intake_output_to_state(analysis_state.run_id, analysis_state)
    analysis_state.agent_statuses["intake"] = AgentStatus.COMPLETE

    return {"analysis_state": analysis_state}


async def map_market_complete_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Runs after the market agent finishes.
    Marks market as COMPLETE.
    (Phase 2: will map structured market research results to AnalysisState.)
    """
    analysis_state = state["analysis_state"]
    logger.info("Market agent complete (stub)", run_id=analysis_state.run_id)

    analysis_state.agent_statuses["market"] = AgentStatus.COMPLETE
    return {"analysis_state": analysis_state}


# =========================================================
# StateGraph Compilation
# =========================================================

workflow = StateGraph(PipelineGraphState)

# Nodes
workflow.add_node("intake_agent", intake_agent_node)
workflow.add_node("intake_tools", intake_tools_node)
workflow.add_node("map_intake_complete", map_intake_complete_node)
workflow.add_node("market_agent", market_agent_node)
workflow.add_node("market_tools", market_tools_node)
workflow.add_node("map_market_complete", map_market_complete_node)

# Entry point
workflow.set_entry_point("intake_agent")

# Intake agent routing
workflow.add_conditional_edges(
    "intake_agent",
    should_continue,
    {"tools": "intake_tools", "complete": "map_intake_complete"},
)
workflow.add_edge("intake_tools", "intake_agent")
workflow.add_edge("map_intake_complete", "market_agent")

# Market agent routing
workflow.add_conditional_edges(
    "market_agent",
    should_continue,
    {"tools": "market_tools", "complete": "map_market_complete"},
)
workflow.add_edge("market_tools", "market_agent")
workflow.add_edge("map_market_complete", END)

# Compile
pipeline = workflow.compile()


# =========================================================
# Public Entrypoint
# =========================================================

async def run_pipeline(analysis_state: AnalysisState) -> AnalysisState:
    """
    Public entrypoint to execute the full VC analysis pipeline.

    Runs the Intake Manager and Market Research Manager sequentially.
    Returns the fully populated AnalysisState after all agents complete.

    Usage:
        from vs_analyst.orchestrator.pipeline import run_pipeline
        result = await run_pipeline(analysis_state)
    """
    logger.info("Pipeline started", run_id=analysis_state.run_id)

    initial_state: PipelineGraphState = {
        "messages": [],
        "analysis_state": analysis_state,
    }

    final_state = await pipeline.ainvoke(initial_state)

    logger.info("Pipeline completed", run_id=analysis_state.run_id)
    return final_state["analysis_state"]
