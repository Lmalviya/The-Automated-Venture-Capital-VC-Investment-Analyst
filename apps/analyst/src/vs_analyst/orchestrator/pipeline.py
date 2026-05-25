from typing import List, Union, Dict, Any

from langgraph.graph import END, StateGraph

from vs_analyst.schemas.state import PipelineGraphState, AnalysisState
from vs_analyst.schemas.shared_enums import PipelineStatus
from vs_analyst.utility.logs import get_logger
from vs_analyst.nodes import (
    state_router_node,
    intake_extraction_node,
    abort_pipeline_node,
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
    Deterministic routing from the intake router node.
    Checks if raw_deck_text is present. If missing, it routes to intake_extraction
    (loop prevention checks: allows up to 2 attempts max, then aborts).
    Otherwise, branches to the 5 parallel extraction nodes.
    """
    raw_text = state.get("raw_deck_text")
    attempts = state.get("intake_attempts", 0)
    max_attempts = 2  # Max attempts allowed

    if not raw_text:
        if attempts >= max_attempts:
            logger.error("Ingestion failed after maximum attempts. Routing to abort_pipeline.")
            return "abort_pipeline"
        logger.info("Raw deck text missing. Routing to intake_extraction.", attempts=attempts)
        return "intake_extraction"

    logger.info("Raw deck text present. Branching to parallel extraction nodes.")
    return [
        "extract_company",
        "extract_market",
        "extract_founders",
        "extract_financials",
        "extract_competitors"
    ]


def verify_company_gate(state: PipelineGraphState) -> Union[List[str], str]:
    """
    Gatekeeper router checking the extraction of company data.
    If company name or sector is missing, aborts the pipeline to prevent wasted API costs.
    Otherwise, forks parallel research subgraphs.
    """
    analysis_state = state["analysis_state"]
    company = analysis_state.company

    if not company.name or not company.sector or company.sector == "UNKNOWN":
        logger.error("Company Dependency Gate failed: Company name or sector is missing or UNKNOWN. Aborting pipeline.")
        return "abort_pipeline"

    logger.info("Company Dependency Gate passed. Forking parallel research subgraphs.")
    return [
        "market_subgraph",
        "competitor_subgraph",
        "founder_subgraph",
        "due_diligence_subgraph"
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
workflow.add_node("abort_pipeline", abort_pipeline_node)

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
        "abort_pipeline": "abort_pipeline",
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

# Verification gate conditional edge after generate_summary
workflow.add_conditional_edges(
    "generate_summary",
    verify_company_gate,
    {
        "abort_pipeline": "abort_pipeline",
        "market_subgraph": "market_subgraph",
        "competitor_subgraph": "competitor_subgraph",
        "founder_subgraph": "founder_subgraph",
        "due_diligence_subgraph": "due_diligence_subgraph",
    }
)

# Wire parallel subgraphs to merge at Join Coordinator
workflow.add_edge("market_subgraph", "join_coordinator")
workflow.add_edge("competitor_subgraph", "join_coordinator")
workflow.add_edge("founder_subgraph", "join_coordinator")
workflow.add_edge("due_diligence_subgraph", "join_coordinator")

# Join coordinator triggers the final report subgraph
workflow.add_edge("join_coordinator", "report_subgraph")

# Report subgraph completes the pipeline
workflow.add_edge("report_subgraph", END)

# Abort pipeline exits graph immediately
workflow.add_edge("abort_pipeline", END)

# Compile
pipeline = workflow.compile()


# =========================================================
#  Entrypoint
# =========================================================

async def run_pipeline(analysis_state: AnalysisState, checkpointer: Any = None) -> AnalysisState:
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
        "raw_website_text": None,
        "intake_attempts": 0
    }

    if checkpointer is not None:
        logger.info("Compiling StateGraph with persistent checkpointer", run_id=analysis_state.run_id)
        compiled_pipeline = workflow.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": analysis_state.run_id}}
    else:
        logger.info("Running StateGraph with default in-memory compilation", run_id=analysis_state.run_id)
        compiled_pipeline = pipeline
        config = {}

    final_state = await compiled_pipeline.ainvoke(initial_state, config=config)

    logger.info("Pipeline completed", run_id=analysis_state.run_id)
    return final_state["analysis_state"]
