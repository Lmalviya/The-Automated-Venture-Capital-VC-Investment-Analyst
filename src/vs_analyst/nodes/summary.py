from typing import Any, Dict
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.utility.logs import get_logger
from langchain_core.messages import AIMessage

logger = get_logger(__name__)

async def generate_summary_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Runs after all parallel structured extractions merge.
    Generates a beautiful Markdown summary of the structured data for the UI
    and marks the Intake phase as COMPLETE.
    """
    analysis_state = state["analysis_state"]
    logger.info("Generating final intake summary", run_id=analysis_state.run_id)
    
    # Preserve the raw text inside AnalysisState
    analysis_state.raw_deck_text = state.get("raw_deck_text")
    analysis_state.agent_statuses["intake"] = AgentStatus.COMPLETE
    
    # Compile a beautiful, deterministic Markdown table for the UI (Instant and Free!)
    summary = f"""
### 📊 Pitch Deck Analysis Summary: {analysis_state.company.name or 'Unknown'}
* **Sector**: {analysis_state.company.sector or 'Not specified'}
* **Product Stage**: {analysis_state.company.product_stage or 'Not specified'}
* **Founders**: {", ".join([f.name for f in analysis_state.founders]) if analysis_state.founders else 'None identified'}
* **Funding Ask**: {analysis_state.company.funding.ask_amount or 'Not specified'} (Valuation: {analysis_state.company.funding.valuation or 'Not specified'})

#### Key Traction & Metrics:
* **Monthly Revenue**: {analysis_state.company.traction.revenue_monthly or 'Not specified'}
* **Annual Revenue**: {analysis_state.company.traction.revenue_annual or 'Not specified'}
* **User Count**: {analysis_state.company.traction.user_count or 'Not specified'}

#### Competitive Landscape:
* **Competitors Identified**: {", ".join([c.name for c in analysis_state.competitive.competitors]) if analysis_state.competitive.competitors else 'None listed'}
    """
    
    return {
        "analysis_state": analysis_state,
        "messages": [AIMessage(content=summary)]
    }
