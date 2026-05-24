from langgraph.graph import StateGraph, END
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.nodes.market import (
    market_planner_node,
    market_synthesizer_node,
    market_risk_analyst_node,
)

_builder = StateGraph(PipelineGraphState)

# Add specialized nodes
_builder.add_node("market_planner", market_planner_node)
_builder.add_node("market_synthesizer", market_synthesizer_node)
_builder.add_node("market_risk_analyst", market_risk_analyst_node)

# Entry point and linear transitions
_builder.set_entry_point("market_planner")
_builder.add_edge("market_planner", "market_synthesizer")
_builder.add_edge("market_synthesizer", "market_risk_analyst")
_builder.add_edge("market_risk_analyst", END)

# Compile sub-graph
market_subgraph = _builder.compile()
