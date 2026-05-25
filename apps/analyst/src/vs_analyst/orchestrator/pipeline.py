from typing import List, Union, Dict, Any

from langgraph.graph import END, StateGraph

from vs_analyst.schemas.state import PipelineGraphState, AnalysisState
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
from vs_analyst.orchestrator.subgraphs.founder_subgraph import founder_subgraph
from vs_analyst.orchestrator.subgraphs.due_diligence_subgraph import due_diligence_subgraph
from vs_analyst.orchestrator.subgraphs.report_subgraph import report_subgraph

logger = get_logger(__name__)


def route_from_router(state: PipelineGraphState) -> Union[List[str], str]:
    """
    Dynamic routing edge that directs flow based on the completeness of AnalysisState.
    If raw deck text is missing, directs flow to intake_extraction.
    Otherwise, forks to all 5 extraction nodes in parallel.
    """
    raw_text = state.get("raw_deck_text")

    if not raw_text:
        logger.info("Raw deck text missing. Routing to intake_extraction.")
        return "intake_extraction"

    logger.info("Raw deck text present. Branching to parallel extraction nodes.")
    return [
        "extract_company",
        "extract_market",
        "extract_founders",
        "extract_financials",
        "extract_competitors"
    ]


def research_fork_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Transition node that acts as a fork point to launch all 4 research subgraphs
    in parallel: market, competitor, founder, and due-diligence.
    """
    logger.info("Research Fork: Launching parallel subgraphs.")
    return {}


def join_coordinator_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Join coordinator node that waits for all 4 parallel research subgraphs to complete
    before passing the consolidated state to the report subgraph.
    """
    logger.info("Join Coordinator: All parallel subgraphs completed and merged.")
    return {}


# =========================================================
# StateGraph Compilation
# =========================================================

workflow = StateGraph(PipelineGraphState)

# 1. Add all Nodes
workflow.add_node("state_router", state_router_node)
workflow.add_node("intake_extraction", intake_extraction_node)

# Extraction nodes
workflow.add_node("extract_company", extract_company_node)
workflow.add_node("extract_market", extract_market_node)
workflow.add_node("extract_founders", extract_founders_node)
workflow.add_node("extract_financials", extract_financials_node)
workflow.add_node("extract_competitors", extract_competitors_node)
workflow.add_node("generate_summary", generate_summary_node)

# Research parallel fork and subgraphs
workflow.add_node("research_fork", research_fork_node)
workflow.add_node("market_subgraph", market_subgraph)
workflow.add_node("competitor_subgraph", competitor_subgraph)
workflow.add_node("founder_subgraph", founder_subgraph)
workflow.add_node("due_diligence_subgraph", due_diligence_subgraph)

# Join Coordinator & Report
workflow.add_node("join_coordinator", join_coordinator_node)
workflow.add_node("report_subgraph", report_subgraph)

# 2. Wire Entry Point & Intake routing
# Entry point starts at the state coordinator router
workflow.set_entry_point("state_router")

# Router dynamic routing
workflow.add_conditional_edges(
    "state_router",
    route_from_router,
    {
        "intake_extraction": "intake_extraction",
        "extract_company": "extract_company",
        "extract_market": "extract_market",
        "extract_founders": "extract_founders",
        "extract_financials": "extract_financials",
        "extract_competitors": "extract_competitors",
    }
)

# Wire intake_extraction back to state_router to check completeness
workflow.add_edge("intake_extraction", "state_router")

# Wire parallel extraction nodes to merge at generate_summary
workflow.add_edge("extract_company", "generate_summary")
workflow.add_edge("extract_market", "generate_summary")
workflow.add_edge("extract_founders", "generate_summary")
workflow.add_edge("extract_financials", "generate_summary")
workflow.add_edge("extract_competitors", "generate_summary")

# Summary node writes to the research parallel fork node
workflow.add_edge("generate_summary", "research_fork")

# Research Fork splits flow to parallel research subgraphs
workflow.add_edge("research_fork", "market_subgraph")
workflow.add_edge("research_fork", "competitor_subgraph")
workflow.add_edge("research_fork", "founder_subgraph")
workflow.add_edge("research_fork", "due_diligence_subgraph")

# Wire parallel subgraphs to merge at Join Coordinator
workflow.add_edge("market_subgraph", "join_coordinator")
workflow.add_edge("competitor_subgraph", "join_coordinator")
workflow.add_edge("founder_subgraph", "join_coordinator")
workflow.add_edge("due_diligence_subgraph", "join_coordinator")

# Join coordinator triggers the final report subgraph
workflow.add_edge("join_coordinator", "report_subgraph")

# Report subgraph completes the pipeline
workflow.add_edge("report_subgraph", END)

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
