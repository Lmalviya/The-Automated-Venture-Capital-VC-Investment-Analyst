# assembler.py
from typing import Any, Dict
from vs_analyst.schemas.state import PipelineGraphState, AnalysisState
from vs_analyst.schemas.memo import MemoCaveat
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

async def state_assembler_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    State Assembler Node.
    Validates upstream namespaces (company, market, competitive, founders, due_diligence)
    and populates MemoCaveats for any incomplete/missing segments.
    Ensures safe execution down-stream.
    """
    analysis_state = state["analysis_state"]
    logger.info("State Assembler node started", run_id=analysis_state.run_id)

    # Scrape warnings/caveats
    caveats = []

    # 1. Company Profile
    if not analysis_state.company or not analysis_state.company.name:
        caveats.append(MemoCaveat(
            source="state_assembler",
            message="Company profile is empty or incomplete."
        ))

    # 2. Market Sizing
    if not analysis_state.market or not analysis_state.market.tam or not analysis_state.market.tam.value:
        caveats.append(MemoCaveat(
            source="state_assembler",
            message="Market analysis details are empty or unverified."
        ))

    # 3. Competitive Landscape
    if not analysis_state.competitive or not analysis_state.competitive.competitors:
        caveats.append(MemoCaveat(
            source="state_assembler",
            message="Competitive landscape is empty or unverified."
        ))

    # 4. Founders Team
    if not analysis_state.founders:
        caveats.append(MemoCaveat(
            source="state_assembler",
            message="Team assessment is empty or unverified."
        ))

    # 5. Due Diligence
    # Check if due_diligence is empty, has no traction checks, or hasn't finished
    if not analysis_state.due_diligence or not analysis_state.due_diligence.traction_checks:
        caveats.append(MemoCaveat(
            source="state_assembler",
            message="Due-Diligence verification was skipped — section will be based on deck claims only."
        ))

    # Build updates for the parent state
    # We create a clean parent_update to hold the caveats
    parent_update = AnalysisState(
        run_id=analysis_state.run_id,
        user_input=analysis_state.user_input,
        created_at=analysis_state.created_at
    )
    
    # Pre-populate caveats on the update
    parent_update.memo.caveats = caveats

    logger.info("State Assembler node completed", run_id=analysis_state.run_id, caveat_count=len(caveats))
    
    return {"analysis_state": parent_update}
