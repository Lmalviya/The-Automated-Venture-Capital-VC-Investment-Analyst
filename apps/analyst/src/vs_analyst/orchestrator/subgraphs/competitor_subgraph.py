from typing import Dict, Any, List, TypedDict
from langgraph.constants import Send
from langgraph.graph import StateGraph, END

from vs_analyst.schemas.state import PipelineGraphState, AnalysisState
from vs_analyst.schemas.competitive import CompetitorSchema
from vs_analyst.schemas.adapters import CompetitorInvestigatorDecision
from vs_analyst.nodes.competitor import (
    competitor_finder_planner_node,
    competitor_finder_synthesizer_node,
    competitor_investigator_planner_node,
    competitor_investigator_synthesizer_node,
    competitive_risk_analyst_node,
)


class CompetitorBranchState(TypedDict):
    """
    Branch-local state used by the parallel investigator nodes during mapping.
    """
    analysis_state: AnalysisState
    competitor: CompetitorSchema
    competitor_research_attempts: int
    competitor_planner_decision: CompetitorInvestigatorDecision


# 1. Compile the Investigator Nested Sub-Graph
# This gives the investigator nodes a dedicated, isolated branch state schema
# so that branch-local fields (like competitor) are not discarded by LangGraph.
_investigator_builder = StateGraph(CompetitorBranchState)
_investigator_builder.add_node("planner", competitor_investigator_planner_node)
_investigator_builder.add_node("synthesizer", competitor_investigator_synthesizer_node)

_investigator_builder.set_entry_point("planner")
_investigator_builder.add_edge("planner", "synthesizer")
_investigator_builder.add_edge("synthesizer", END)

investigator_subgraph = _investigator_builder.compile()


# 2. Compile the Main Competitor Sub-Graph
def route_to_investigators(state: PipelineGraphState) -> List[Send]:
    """
    Dynamic routing edge that splits the workflow.
    Fans out parallel investigator sub-graph branches for each discovered competitor.
    """
    competitors = state["analysis_state"].competitive.competitors
    
    sends = []
    for comp in competitors:
        branch_state: CompetitorBranchState = {
            "analysis_state": state["analysis_state"],
            "competitor": comp,
            "competitor_research_attempts": 0,
            "competitor_planner_decision": None
        }
        # Fan out using the nested investigator sub-graph node
        sends.append(Send("investigator_subgraph", branch_state))
        
    if not sends:
        # Fallback to direct routing if competitor list is empty
        return [Send("competitive_risk_analyst", state)]
        
    return sends


_builder = StateGraph(PipelineGraphState)

# Add nodes
_builder.add_node("competitor_finder_planner", competitor_finder_planner_node)
_builder.add_node("competitor_finder_synthesizer", competitor_finder_synthesizer_node)
_builder.add_node("investigator_subgraph", investigator_subgraph)
_builder.add_node("competitive_risk_analyst", competitive_risk_analyst_node)

# Set entry point
_builder.set_entry_point("competitor_finder_planner")

# Link finder nodes
_builder.add_edge("competitor_finder_planner", "competitor_finder_synthesizer")

# Parallel map phase: Split per competitor
_builder.add_conditional_edges(
    "competitor_finder_synthesizer",
    route_to_investigators,
    ["investigator_subgraph", "competitive_risk_analyst"]
)

# Reduce phase: merge parallel results back into risk synthesis
_builder.add_edge("investigator_subgraph", "competitive_risk_analyst")

# Exit sub-graph
_builder.add_edge("competitive_risk_analyst", END)

# Compile competitor sub-graph
competitor_subgraph = _builder.compile()
