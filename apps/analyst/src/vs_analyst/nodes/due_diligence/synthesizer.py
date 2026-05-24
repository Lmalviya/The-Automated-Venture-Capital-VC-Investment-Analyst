from typing import Any, Dict, List
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.schemas.state import AnalysisState
from vs_analyst.utility.llm import llm
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


class DueDiligenceSynthesis(BaseModel):
    red_flags: List[str] = Field(
        default_factory=list,
        description="Isolated due diligence red flags e.g. uncorroborated metrics, compliance violations, lawsuits."
    )
    summary: str = Field(
        ...,
        description="Comprehensive 2-3 paragraph narrative due-diligence memo summary."
    )


async def dd_synthesizer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Due-Diligence Synthesizer Node.
    Reads verified metrics, regulatory checks, press mentions, and GitHub signals.
    Isolates external red flags and authors memo summary.
    Conforms to due_diligence_sub_graph.md and Phase 6 specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Due-Diligence Synthesizer node started", run_id=analysis_state.run_id)

    due_diligence = analysis_state.due_diligence

    # 1. Compile verified context
    context = (
        f"Verified Traction Checks:\n"
        f"{[{'claim': c.claim, 'verified': c.verified, 'evidence': c.evidence} for c in due_diligence.traction_checks]}\n\n"
        f"Verified Press Footprint:\n"
        f"Press Summary: {due_diligence.press_summary}\n"
        f"Mentions: {[{'title': m.title, 'source': m.source, 'sentiment': m.sentiment} for m in due_diligence.press_mentions]}\n\n"
        f"Verified Regulatory Standing: {due_diligence.regulatory_flags}\n"
        f"Verified Patents & IP: {due_diligence.patent_mentions}\n"
        f"Verified Legal Disputes & Notes: {due_diligence.legal_notes}\n"
    )

    # 2. Invoke structured LLM synthesis
    try:
        structured_synthesizer = AgentRegistry.dd_synthesizer.with_structured_output(DueDiligenceSynthesis)
        result = await structured_synthesizer.ainvoke([
            SystemMessage(content=PromptRegistry.dd_synthesizer_system.value),
            HumanMessage(content=f"Synthesize the following research findings and isolate external red flags:\n\n{context}")
        ])

        if result:
            logger.info("Due-diligence final synthesis completed successfully", run_id=analysis_state.run_id)
            
            # Map back to state
            due_diligence.red_flags = list(set(due_diligence.red_flags + result.red_flags))
            due_diligence.summary = result.summary

    except Exception as e:
        logger.error("Error in Due-Diligence Synthesizer node", run_id=analysis_state.run_id, error=str(e))

    # 3. Mark agent status COMPLETE
    parent_update = AnalysisState(
        run_id=analysis_state.run_id,
        user_input=analysis_state.user_input,
        created_at=analysis_state.created_at
    )
    parent_update.due_diligence = due_diligence
    parent_update.agent_statuses = {"due_diligence": AgentStatus.COMPLETE}

    return {"analysis_state": parent_update}
