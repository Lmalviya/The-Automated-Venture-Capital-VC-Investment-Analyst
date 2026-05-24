from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.adapters import MarketRiskAdaptor
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


async def market_risk_analyst_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Market Risk Analyst Node.
    Analyzes the startup and synthesized market landscape to identify critical market-level and company-specific risks.
    Conforms to market_risk_analyst.md spec.
    """
    analysis_state = state["analysis_state"]
    logger.info("Market Risk Analyst node started", run_id=analysis_state.run_id)

    company = analysis_state.company
    market = analysis_state.market

    # Context setup
    context = (
        f"--- Company Profile ---\n"
        f"Name: {company.name or 'N/A'}\n"
        f"Sector: {company.sector or 'N/A'}\n"
        f"Business Model: {company.business_model.value if company.business_model else 'N/A'}\n"
        f"Value Proposition: {company.value_proposition or 'N/A'}\n"
        f"Geography: {company.geography or 'N/A'}\n"
        f"Employee Count: {company.employee_count or 'N/A'}\n"
        f"Product Stage: {company.product_stage or 'N/A'}\n\n"
        f"--- Synthesized Market Landscape ---\n"
        f"TAM: {market.tam.value if market.tam else 'N/A'} (Source: {market.tam.source if market.tam else 'N/A'}, Notes: {market.tam.notes if market.tam else 'N/A'})\n"
        f"SAM: {market.sam.value if market.sam else 'N/A'} (Source: {market.sam.source if market.sam else 'N/A'})\n"
        f"SOM: {market.som.value if market.som else 'N/A'} (Source: {market.som.source if market.som else 'N/A'})\n"
        f"Growth Rate (CAGR): {market.growth_rate or 'N/A'} (Source: {market.growth_source or 'N/A'})\n"
        f"Key Trends: {market.key_trends}\n"
        f"Summary Synthesis: {market.summary or 'N/A'}\n"
    )

    try:
        risk_agent = AgentRegistry.market_risk_analyst.with_structured_output(MarketRiskAdaptor)
        result = await risk_agent.ainvoke([
            SystemMessage(content=PromptRegistry.market_risk_analyst_system.value),
            HumanMessage(content=context)
        ])

        logger.info(
            "Market Risk analysis completed successfully", 
            run_id=analysis_state.run_id, 
            risk_count=len(result.market_risks)
        )

        # Write market_risks to the state
        market.market_risks = result.market_risks

    except Exception as e:
        logger.error("Error in market risk analyst node", run_id=analysis_state.run_id, error=str(e))
        # Fallback to structural risks based on business model & sector
        logger.info("Falling back to basic structural risks", run_id=analysis_state.run_id)
        fallback_risks = [
            f"Regulatory friction due to compliance overhead in the {company.sector or 'relevant'} sector.",
            f"Adoption barriers from potential switching costs and sales cycle complexity.",
            f"Competitive defensibility risk if entry barriers are low or incumbents react aggressively."
        ]
        market.market_risks = fallback_risks

    # Set market agent status to COMPLETE directly (replaces coordinator map_market_complete_node)
    logger.info("Marking market agent status as COMPLETE", run_id=analysis_state.run_id)
    analysis_state.agent_statuses["market"] = AgentStatus.COMPLETE

    return {"analysis_state": analysis_state}
