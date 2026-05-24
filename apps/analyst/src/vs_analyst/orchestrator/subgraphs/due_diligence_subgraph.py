from langgraph.graph import StateGraph, END
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.nodes.due_diligence import (
    dd_extractor_node,
    dd_legal_verifier_node,
    dd_traction_verifier_node,
    dd_press_verifier_node,
    dd_synthesizer_node,
)

workflow = StateGraph(PipelineGraphState)

# 1. Add Nodes
workflow.add_node("dd_extractor", dd_extractor_node)
workflow.add_node("dd_legal_verifier", dd_legal_verifier_node)
workflow.add_node("dd_traction_verifier", dd_traction_verifier_node)
workflow.add_node("dd_press_verifier", dd_press_verifier_node)
workflow.add_node("dd_synthesizer", dd_synthesizer_node)

# 2. Set Entry Point
workflow.set_entry_point("dd_extractor")

# 3. Parallel Fork: Link dd_extractor to verifiers
workflow.add_edge("dd_extractor", "dd_legal_verifier")
workflow.add_edge("dd_extractor", "dd_traction_verifier")
workflow.add_edge("dd_extractor", "dd_press_verifier")

# 4. Parallel Join: Link verifiers back to dd_synthesizer
workflow.add_edge("dd_legal_verifier", "dd_synthesizer")
workflow.add_edge("dd_traction_verifier", "dd_synthesizer")
workflow.add_edge("dd_press_verifier", "dd_synthesizer")

# 5. Exit Sub-Graph
workflow.add_edge("dd_synthesizer", END)

# Compile due_diligence_subgraph
due_diligence_subgraph = workflow.compile()
