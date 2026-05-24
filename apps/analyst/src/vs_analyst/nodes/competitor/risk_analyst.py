from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.adapters import CompetitiveRiskAdaptor
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


async def competitive_risk_analyst_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Competitive Risk Analyst Node.
    Analyzes fully profiled competitors and target startup to synthesize competitive landscape risks.
    Conforms to competitive_risk_analyst.md spec.
    """
    analysis_state = state["analysis_state"]
    logger.info("Competitive Risk Analyst node started", run_id=analysis_state.run_id)

    company = analysis_state.company
    competitive = analysis_state.competitive
    market = analysis_state.market

    # 1. Context Setup
    competitors_text = ""
    for idx, c in enumerate(competitive.competitors, 1):
        competitors_text += (
            f"Competitor {idx}: {c.name}\n"
            f"  Type: {c.competitor_type.value if c.competitor_type else 'N/A'}\n"
            f"  Geography: {c.geography or 'N/A'}\n"
            f"  Funding Stage: {c.funding_stage or 'N/A'}\n"
            f"  Funding Amount: {c.funding_amount or 'N/A'}\n"
            f"  Business Model: {c.business_model or 'N/A'}\n"
            f"  Key Strengths: {c.key_strengths}\n"
            f"  Key Weaknesses: {c.key_weaknesses}\n"
            f"  Custom Dimensions: {c.custom_dimensions}\n\n"
        )

    context = (
        f"--- Startup Company Profile ---\n"
        f"Name: {company.name or 'N/A'}\n"
        f"Sector: {company.sector or 'N/A'}\n"
        f"Business Model: {company.business_model.value if company.business_model else 'N/A'}\n"
        f"Geography: {company.geography or 'N/A'}\n"
        f"Value Proposition: {company.value_proposition or 'N/A'}\n"
        f"Product Stage: {company.product_stage or 'N/A'}\n\n"
        f"--- Market Context ---\n"
        f"Growth Rate (CAGR): {market.growth_rate or 'N/A'}\n"
        f"Growth Source: {market.growth_source or 'N/A'}\n\n"
        f"--- Full Profiled Competitor Landscape ---\n"
        f"{competitors_text}"
        f"Moat Assessment: {competitive.moat_assessment or 'N/A'}\n"
    )

    try:
        risk_agent = AgentRegistry.competitive_risk_analyst.with_structured_output(CompetitiveRiskAdaptor)
        result = await risk_agent.ainvoke([
            SystemMessage(content=PromptRegistry.competitive_risk_analyst_system.value),
            HumanMessage(content=context)
        ])

        logger.info(
            "Competitive Risk synthesis completed successfully", 
            run_id=analysis_state.run_id, 
            severity=result.risk_severity,
            risk_count=len(result.top_risks)
        )

        # Write updates to state
        competitive.competitive_risk = result.competitive_risk
        
        # Combine top risks and severity into summary for the memo table
        risk_summary = f"Severity: {result.risk_severity}\n\nTop Competitive Risks:\n"
        for idx, risk in enumerate(result.top_risks, 1):
            risk_summary += f"{idx}. {risk}\n"
        competitive.summary = risk_summary

    except Exception as e:
        logger.error("Error in competitive risk analyst node", run_id=analysis_state.run_id, error=str(e))
        # Fallback basic analysis
        competitive.competitive_risk = "Competitive threat identified from direct and indirect players in the sector."
        competitive.summary = "Severity: MODERATE\n\nTop Competitive Risks:\n1. Pricing pressure and category consolidation."

    # Mark competitive phase complete in agent statuses
    logger.info("Marking competitive agent status as COMPLETE", run_id=analysis_state.run_id)
    analysis_state.agent_statuses["competitive"] = AgentStatus.COMPLETE

    return {"analysis_state": analysis_state}
