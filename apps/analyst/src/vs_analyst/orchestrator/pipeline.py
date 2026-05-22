from typing import List, Union

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from vs_analyst.managers.intake import IntakeManager, intake_agent_node
from vs_analyst.managers.market import MarketManager, market_agent_node

from vs_analyst.orchestrator.routing_helper import should_continue
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.schemas.state import AnalysisState, PipelineGraphState

# Decoupled Graph Nodes
from vs_analyst.nodes import (
    state_router_node,
    extract_company_node,
    extract_market_node,
    extract_founders_node,
    extract_financials_node,
    extract_competitors_node,
    generate_summary_node,
    map_market_complete_node
)

from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

# Tool Nodes
intake_tools_node = ToolNode(IntakeManager.tools)
market_tools_node = ToolNode(MarketManager.tools)


def route_from_router(state: PipelineGraphState) -> Union[List[str], str]:
    """
    Dynamic routing edge that directs flow based on the completeness of AnalysisState.
    Supports parallel branching by returning a list of node names.
    """
    analysis = state["analysis_state"]
    raw_text = state.get("raw_deck_text")

    # 1. If basic raw text is missing, we must direct flow to the Intake Agent
    if not raw_text:
        return "intake_agent"

    # 2. If raw text is extracted, but the intake phase has not been structured/completed
    if analysis.agent_statuses.get("intake") != AgentStatus.COMPLETE:
        # Branch to all 5 extraction nodes in parallel!
        return [
            "extract_company",
            "extract_market",
            "extract_founders",
            "extract_financials",
            "extract_competitors"
        ]

    # 3. If intake is complete, but market research has not started/completed
    if analysis.agent_statuses.get("market") != AgentStatus.COMPLETE:
        return "market_agent"

    # 4. Everything is complete!
    return END


# =========================================================
# StateGraph Compilation
# =========================================================

workflow = StateGraph(PipelineGraphState)

# Define Nodes
workflow.add_node("state_router", state_router_node)
workflow.add_node("intake_agent", intake_agent_node)
workflow.add_node("intake_tools", intake_tools_node)

# Extraction nodes
workflow.add_node("extract_company", extract_company_node)
workflow.add_node("extract_market", extract_market_node)
workflow.add_node("extract_founders", extract_founders_node)
workflow.add_node("extract_financials", extract_financials_node)
workflow.add_node("extract_competitors", extract_competitors_node)
workflow.add_node("generate_summary", generate_summary_node)

workflow.add_node("market_agent", market_agent_node)
workflow.add_node("market_tools", market_tools_node)
workflow.add_node("map_market_complete", map_market_complete_node)

# Entry point starts at the state coordinator router
workflow.set_entry_point("state_router")

# Router dynamic routing
workflow.add_conditional_edges(
    "state_router",
    route_from_router,
    {
        "intake_agent": "intake_agent",
        "extract_company": "extract_company",
        "extract_market": "extract_market",
        "extract_founders": "extract_founders",
        "extract_financials": "extract_financials",
        "extract_competitors": "extract_competitors",
        "market_agent": "market_agent",
        "__end__": END
    }
)

# Intake agent routing
workflow.add_conditional_edges(
    "intake_agent",
    should_continue,
    {"tools": "intake_tools", "complete": "state_router"},
)
workflow.add_edge("intake_tools", "intake_agent")

# Wire parallel extraction nodes to merge at generate_summary
workflow.add_edge("extract_company", "generate_summary")
workflow.add_edge("extract_market", "generate_summary")
workflow.add_edge("extract_founders", "generate_summary")
workflow.add_edge("extract_financials", "generate_summary")
workflow.add_edge("extract_competitors", "generate_summary")

# Summary node loops back to the router to decide the next phase
workflow.add_edge("generate_summary", "state_router")

# Market agent routing
workflow.add_conditional_edges(
    "market_agent",
    should_continue,
    {"tools": "market_tools", "complete": "map_market_complete"},
)
workflow.add_edge("market_tools", "market_agent")
workflow.add_edge("map_market_complete", "state_router")

# Compile
pipeline = workflow.compile()


# =========================================================
#  Entrypoint
# =========================================================

async def run_pipeline(analysis_state: AnalysisState) -> AnalysisState:
    """
    Public entrypoint to execute the full VC analysis pipeline.

    Uses a dynamic State-Driven Workflow Coordinator to orchestrate agents
    and parallel structured extraction nodes.
    Returns the fully populated AnalysisState after all agents complete.
    """
    logger.info("Pipeline started", run_id=analysis_state.run_id)

    initial_state: PipelineGraphState = {
        "messages": [],
        "analysis_state": analysis_state,
        "raw_deck_text": None,
        "raw_website_text": None
    }

    final_state = await pipeline.ainvoke(initial_state)

    logger.info("Pipeline completed", run_id=analysis_state.run_id)
    return final_state["analysis_state"]



