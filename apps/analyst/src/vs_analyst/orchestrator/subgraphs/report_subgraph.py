# report_subgraph.py
from typing import Any, Dict
from langgraph.graph import END, StateGraph

from vs_analyst.nodes.report import (
    state_assembler_node,
    executive_summary_writer_node,
    market_section_writer_node,
    competitor_section_writer_node,
    founder_section_writer_node,
    dd_section_writer_node,
    investment_advocate_node,
    investment_adversary_node,
    growth_strategist_node,
    hazard_mitigator_node,
    venture_partner_ic_agent_node,
    memo_reviewer_node,
    vector_diagram_generator_node,
    document_compiler_node,
)
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

# Thin transition / coordinator nodes
def drafting_fork_node(state: PipelineGraphState) -> Dict[str, Any]:
    """Helper transition node to split flow into parallel section writers."""
    return {}

def draft_join_coordinator(state: PipelineGraphState) -> Dict[str, Any]:
    """Helper transition node to join parallel drafts."""
    return {}

def debate_fork_node(state: PipelineGraphState) -> Dict[str, Any]:
    """Helper transition node to split flow into parallel advisory debate agents."""
    return {}

def debate_join_coordinator(state: PipelineGraphState) -> Dict[str, Any]:
    """Helper transition node to join parallel debate briefs."""
    return {}


def route_after_review(state: PipelineGraphState) -> str:
    """
    Conditional routing function after the memo reviewer audit.
    If rejected and review_attempts < 2, loops back to section writers.
    Otherwise, proceeds to the diagram generator.
    """
    analysis_state = state["analysis_state"]
    memo = analysis_state.memo
    
    if (memo.review_decision and 
        memo.review_decision.status == "REJECTED" and 
        memo.review_attempts < 2):
        logger.info(
            "Memo rejected by auditor. Attempt count is below cap. Routing back to drafting phase.",
            run_id=analysis_state.run_id,
            attempts=memo.review_attempts
        )
        return "drafting_fork"
    else:
        logger.info(
            "Memo approved or review attempts capped. Routing to diagram generator.",
            run_id=analysis_state.run_id,
            attempts=memo.review_attempts
        )
        return "vector_diagram_generator"


# Build the report StateGraph
workflow = StateGraph(PipelineGraphState)

# 1. Add all nodes
workflow.add_node("state_assembler", state_assembler_node)
workflow.add_node("drafting_fork", drafting_fork_node)

# Section Writers (Phase 1)
workflow.add_node("executive_summary_writer", executive_summary_writer_node)
workflow.add_node("market_section_writer", market_section_writer_node)
workflow.add_node("competitor_section_writer", competitor_section_writer_node)
workflow.add_node("founder_section_writer", founder_section_writer_node)
workflow.add_node("dd_section_writer", dd_section_writer_node)

workflow.add_node("draft_join", draft_join_coordinator)
workflow.add_node("debate_fork", debate_fork_node)

# Advisory Debate (Phase 2)
workflow.add_node("investment_advocate", investment_advocate_node)
workflow.add_node("investment_adversary", investment_adversary_node)
workflow.add_node("growth_strategist", growth_strategist_node)
workflow.add_node("hazard_mitigator", hazard_mitigator_node)

workflow.add_node("debate_join", debate_join_coordinator)
workflow.add_node("venture_partner_ic", venture_partner_ic_agent_node)
workflow.add_node("memo_reviewer", memo_reviewer_node)

# Compilation (Phase 3)
workflow.add_node("vector_diagram_generator", vector_diagram_generator_node)
workflow.add_node("document_compiler", document_compiler_node)

# 2. Wire edges
workflow.set_entry_point("state_assembler")
workflow.add_edge("state_assembler", "drafting_fork")

# Fork drafting phase to parallel section writers
workflow.add_edge("drafting_fork", "executive_summary_writer")
workflow.add_edge("drafting_fork", "market_section_writer")
workflow.add_edge("drafting_fork", "competitor_section_writer")
workflow.add_edge("drafting_fork", "founder_section_writer")
workflow.add_edge("drafting_fork", "dd_section_writer")

# Join drafting phase
workflow.add_edge("executive_summary_writer", "draft_join")
workflow.add_edge("market_section_writer", "draft_join")
workflow.add_edge("competitor_section_writer", "draft_join")
workflow.add_edge("founder_section_writer", "draft_join")
workflow.add_edge("dd_section_writer", "draft_join")

workflow.add_edge("draft_join", "debate_fork")

# Fork debate phase to parallel advisory agents
workflow.add_edge("debate_fork", "investment_advocate")
workflow.add_edge("debate_fork", "investment_adversary")
workflow.add_edge("debate_fork", "growth_strategist")
workflow.add_edge("debate_fork", "hazard_mitigator")

# Join debate phase to IC partner chairperson
workflow.add_edge("investment_advocate", "debate_join")
workflow.add_edge("investment_adversary", "debate_join")
workflow.add_edge("growth_strategist", "debate_join")
workflow.add_edge("hazard_mitigator", "debate_join")

workflow.add_edge("debate_join", "venture_partner_ic")
workflow.add_edge("venture_partner_ic", "memo_reviewer")

# Reviewer LLM-as-a-Judge Loopback or Proceed edge
workflow.add_conditional_edges(
    "memo_reviewer",
    route_after_review,
    {
        "drafting_fork": "drafting_fork",
        "vector_diagram_generator": "vector_diagram_generator"
    }
)

# Compile & exit sub-graph
workflow.add_edge("vector_diagram_generator", "document_compiler")
workflow.add_edge("document_compiler", END)

report_subgraph = workflow.compile()
