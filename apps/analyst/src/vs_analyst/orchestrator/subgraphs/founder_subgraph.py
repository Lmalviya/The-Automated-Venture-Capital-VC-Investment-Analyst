from typing import Dict, Any, List, TypedDict
from langgraph.constants import Send
from langgraph.graph import StateGraph, END

from vs_analyst.schemas.state import PipelineGraphState, AnalysisState
from vs_analyst.schemas.founder import FounderSchema
from vs_analyst.nodes.founder import (
    founder_profiler_node,
    founder_risk_analyst_node,
)


class FounderBranchState(TypedDict):
    """
    Branch-local state used by the parallel founder nodes during mapping.
    """
    analysis_state: AnalysisState
    founder: FounderSchema


# 1. Compile the Profiler Nested Branch Graph
# Preserves branch-local keys during parallel execution safely.
_profiler_branch = StateGraph(FounderBranchState)
_profiler_branch.add_node("profiler", founder_profiler_node)
_profiler_branch.set_entry_point("profiler")
_profiler_branch.add_edge("profiler", END)
profiler_branch_graph = _profiler_branch.compile()


# 2. Compile the Risk Nested Branch Graph
# Preserves branch-local keys during risk audit execution safely.
_risk_branch = StateGraph(FounderBranchState)
_risk_branch.add_node("risk", founder_risk_analyst_node)
_risk_branch.set_entry_point("risk")
_risk_branch.add_edge("risk", END)
risk_branch_graph = _risk_branch.compile()


# 3. Compile the Main Founder Sub-Graph
async def entry_node(state: PipelineGraphState) -> Dict[str, Any]:
    """Pass-through coordinator entry point for founder_subgraph."""
    return {"analysis_state": state["analysis_state"]}


async def profiler_join_node(state: PipelineGraphState) -> Dict[str, Any]:
    """Pass-through join node that synchronizes the parallel profiling branches."""
    return {"analysis_state": state["analysis_state"]}


def route_to_profilers(state: PipelineGraphState) -> List[Send]:
    """
    Dynamic routing edge that splits the workflow.
    Fans out parallel profiler branches for each founder.
    """
    founders = state["analysis_state"].founders
    sends = []
    
    for f in founders:
        branch_state: FounderBranchState = {
            "analysis_state": state["analysis_state"],
            "founder": f
        }
        sends.append(Send("profiler_branch_graph", branch_state))
        
    if not sends:
        # Fallback if no founders are registered
        return [Send("profiler_join", state)]
        
    return sends


def route_to_risk_analysts(state: PipelineGraphState) -> List[Send]:
    """
    Dynamic routing edge that splits the workflow for the risk audit.
    Fans out parallel risk analyst branches for each founder.
    """
    founders = state["analysis_state"].founders
    sends = []
    
    for f in founders:
        branch_state: FounderBranchState = {
            "analysis_state": state["analysis_state"],
            "founder": f
        }
        sends.append(Send("risk_branch_graph", branch_state))
        
    if not sends:
        # Fallback if no founders are registered
        return [Send("complete_exit", state)]
        
    return sends


async def complete_exit(state: PipelineGraphState) -> Dict[str, Any]:
    """Final node in founder_subgraph to cleanly terminate graph flow."""
    return {"analysis_state": state["analysis_state"]}


_builder = StateGraph(PipelineGraphState)

# Add Nodes
_builder.add_node("entry", entry_node)
_builder.add_node("profiler_branch_graph", profiler_branch_graph)
_builder.add_node("profiler_join", profiler_join_node)
_builder.add_node("risk_branch_graph", risk_branch_graph)
_builder.add_node("complete_exit", complete_exit)

# Set entry point
_builder.set_entry_point("entry")

# 1. Parallel profiling map phase
_builder.add_conditional_edges(
    "entry",
    route_to_profilers,
    ["profiler_branch_graph", "profiler_join"]
)
_builder.add_edge("profiler_branch_graph", "profiler_join")

# 2. Parallel risk auditing map phase
_builder.add_conditional_edges(
    "profiler_join",
    route_to_risk_analysts,
    ["risk_branch_graph", "complete_exit"]
)
_builder.add_edge("risk_branch_graph", "complete_exit")

# Exit sub-graph
_builder.add_edge("complete_exit", END)

# Compile founder sub-graph
founder_subgraph = _builder.compile()
