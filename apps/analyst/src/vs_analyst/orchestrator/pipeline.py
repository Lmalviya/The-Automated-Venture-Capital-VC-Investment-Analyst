from typing import List, Union, Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from vs_analyst.agents import AgentRegistry
from vs_analyst.agents.intake import INTAKE_TOOLS
from vs_analyst.orchestrator.routing_helper import should_continue
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.schemas.state import AnalysisState, PipelineGraphState
from vs_analyst.utility.logs import get_logger
from vs_analyst.nodes import (
    state_router_node,
    intake_extraction_node,
    extract_company_node,
    extract_market_node,
    extract_founders_node,
    extract_financials_node,
    extract_competitors_node,
    generate_summary_node,
)
from vs_analyst.orchestrator.subgraphs.market_subgraph import market_subgraph
from vs_analyst.orchestrator.subgraphs.competitor_subgraph import competitor_subgraph

logger = get_logger(__name__)

# NOTE: managers/ has been DELETED. All agent logic now lives in agents/.
# If you encounter any import from vs_analyst.managers.* while implementing
# new nodes or sub-graphs, remove it and use AgentRegistry instead.


async def intake_agent_node(state: PipelineGraphState) -> Dict[str, Any]:
    """Intake agent node. Replaced the deleted managers/intake.py::intake_agent_node."""
    analysis_state = state["analysis_state"]
    messages = list(state["messages"])
    if not messages:
        logger.info("Intake agent: first turn", run_id=analysis_state.run_id)
        human_text = PromptRegistry.intake_human.value.format(
            run_id=analysis_state.run_id,
            deck_path=analysis_state.user_input.pitch_deck_path,
            website_url=analysis_state.user_input.website_url or "None provided",
        )
        messages = [
            SystemMessage(content=PromptRegistry.intake_system.value),
            HumanMessage(content=human_text),
        ]
    response = await AgentRegistry.intake.ainvoke(messages)
    logger.info("Intake agent: LLM responded", run_id=analysis_state.run_id)
    return {"messages": [response]}


# ── Tool Nodes ─────────────────────────────────────────────────────────────────
intake_tools_node = ToolNode(INTAKE_TOOLS)


def route_from_router(state: PipelineGraphState) -> Union[List[str], str]:
    """
    Dynamic routing edge that directs flow based on the completeness of AnalysisState.
    Supports parallel branching by returning a list of node names.
    """
    analysis = state["analysis_state"]
    raw_text = state.get("raw_deck_text")

    # 1. If basic raw deck text is missing, we must direct flow to the Intake Extraction node
    if not raw_text:
        return "intake_extraction"

    # If website URL is provided but website text is missing, run intake agent for scraping
    if (
        analysis.user_input.website_url
        and not state.get("raw_website_text")
        and analysis.agent_statuses.get("intake") != AgentStatus.COMPLETE
    ):
        # Prevent looping: if we already ran the intake agent and it finished (no tool calls left), pass to extraction
        if state.get("messages") and not getattr(state["messages"][-1], "tool_calls", None):
            pass
        else:
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

    # 3. If intake is complete, but market or competitor research has not started/completed
    next_nodes = []
    if analysis.agent_statuses.get("market") != AgentStatus.COMPLETE:
        next_nodes.append("market_subgraph")
    if analysis.agent_statuses.get("competitive") != AgentStatus.COMPLETE:
        next_nodes.append("competitor_subgraph")

    if next_nodes:
        return next_nodes

    # 4. Everything is complete!
    return END


# =========================================================
# StateGraph Compilation
# =========================================================

workflow = StateGraph(PipelineGraphState)

# Define Nodes
workflow.add_node("state_router", state_router_node)
workflow.add_node("intake_extraction", intake_extraction_node)
workflow.add_node("intake_agent", intake_agent_node)
workflow.add_node("intake_tools", intake_tools_node)

# Extraction nodes
workflow.add_node("extract_company", extract_company_node)
workflow.add_node("extract_market", extract_market_node)
workflow.add_node("extract_founders", extract_founders_node)
workflow.add_node("extract_financials", extract_financials_node)
workflow.add_node("extract_competitors", extract_competitors_node)
workflow.add_node("generate_summary", generate_summary_node)

# Market Subgraph node
workflow.add_node("market_subgraph", market_subgraph)

# Competitor Subgraph node
workflow.add_node("competitor_subgraph", competitor_subgraph)

# Entry point starts at the state coordinator router
workflow.set_entry_point("state_router")

# Router dynamic routing
workflow.add_conditional_edges(
    "state_router",
    route_from_router,
    {
        "intake_extraction": "intake_extraction",
        "intake_agent": "intake_agent",
        "extract_company": "extract_company",
        "extract_market": "extract_market",
        "extract_founders": "extract_founders",
        "extract_financials": "extract_financials",
        "extract_competitors": "extract_competitors",
        "market_subgraph": "market_subgraph",
        "competitor_subgraph": "competitor_subgraph",
        "__end__": END
    }
)

# Wire intake_extraction directly to state_router
workflow.add_edge("intake_extraction", "state_router")

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

# Market subgraph transition back to coordinator router
workflow.add_edge("market_subgraph", "state_router")

# Competitor subgraph transition back to coordinator router
workflow.add_edge("competitor_subgraph", "state_router")

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
