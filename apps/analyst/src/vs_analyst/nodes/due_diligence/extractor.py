from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.adapters import DueDiligenceAdaptor
from vs_analyst.schemas.due_diligence import TractionVerification
from vs_analyst.schemas.shared_models import PressMention
from vs_analyst.schemas.state import PipelineGraphState, AnalysisState
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


async def dd_extractor_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Due-Diligence Seed Extraction Node.
    Reads deck and website text, extracts claims to verify via structured LLM,
    and initializes work items inside DueDiligenceSchema.
    Conforms to dd_extractor.md and Phase 6 specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Due-Diligence extractor node started", run_id=analysis_state.run_id)

    raw_text = state.get("raw_deck_text") or ""
    raw_web = state.get("raw_website_text") or ""
    
    if not raw_text and not raw_web:
        logger.info("No raw deck or website text in state. Skipping extraction.", run_id=analysis_state.run_id)
        return {"analysis_state": analysis_state}

    # 1. Context Synthesis
    context = (
        f"--- Pitch Deck Extracted Text ---\n"
        f"{raw_text}\n\n"
        f"--- Website Scraped Text ---\n"
        f"{raw_web}\n"
    )

    # 2. Invoke LLM structured extraction
    try:
        structured_extractor = AgentRegistry.dd_extractor.with_structured_output(DueDiligenceAdaptor)
        result = await structured_extractor.ainvoke([
            SystemMessage(content=PromptRegistry.dd_extractor_system.value),
            HumanMessage(content=context)
        ])

        if result:
            logger.info(
                "Due-Diligence seed extraction complete", 
                run_id=analysis_state.run_id,
                traction_claims_count=len(result.traction_claims),
                press_claims_count=len(result.press_claims),
                patent_claims_count=len(result.patents),
                regulatory_flags_count=len(result.regulatory_flags),
                legal_notes_count=len(result.legal_notes)
            )

            # 3. State Syncing
            due_diligence = analysis_state.due_diligence
            
            # Map traction_claims into traction_checks
            due_diligence.traction_checks = []
            for claim in result.traction_claims:
                due_diligence.traction_checks.append(
                    TractionVerification(claim=claim, verified=None, evidence=None)
                )

            # Map press_claims into press_mentions
            due_diligence.press_mentions = []
            for claim in result.press_claims:
                due_diligence.press_mentions.append(
                    PressMention(title=claim, url=None, source=None, date=None, sentiment=None, snippet=None)
                )

            # Map patents directly
            due_diligence.patent_mentions = list(set(result.patents))

            # Set regulatory_flags and legal_notes
            due_diligence.regulatory_flags = list(set(result.regulatory_flags))
            due_diligence.legal_notes = list(set(result.legal_notes))

    except Exception as e:
        logger.error("Error in Due-Diligence extractor node", run_id=analysis_state.run_id, error=str(e))

    return {"analysis_state": analysis_state}
