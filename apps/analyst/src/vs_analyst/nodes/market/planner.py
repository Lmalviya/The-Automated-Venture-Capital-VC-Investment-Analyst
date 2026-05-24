from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.adapters import MarketPlannerDecision
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.config import settings
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


async def market_planner_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Market Planner Node.
    Analyzes startup profile and current market data to identify information gaps.
    Conforms to market_planner.md spec.
    """
    analysis_state = state["analysis_state"]
    logger.info("Market Planner node started", run_id=analysis_state.run_id)

    # 1. Attempts Check
    attempts = state.get("market_research_attempts", 0)
    if attempts >= settings.market_research_max_attempts:
        logger.info(
            "Max research attempts reached. Bypassing LLM and marking complete.",
            run_id=analysis_state.run_id,
            attempts=attempts,
        )
        # In a linear graph, we still return the state
        return {"analysis_state": analysis_state}

    # 2. Context Setup
    company = analysis_state.company
    market = analysis_state.market

    # Format the context for the LLM
    context = (
        f"--- Company Profile ---\n"
        f"Name: {company.name or 'N/A'}\n"
        f"Sector: {company.sector or 'N/A'}\n"
        f"Business Model: {company.business_model.value if company.business_model else 'N/A'}\n"
        f"Value Proposition: {company.value_proposition or 'N/A'}\n"
        f"Geography: {company.geography or 'N/A'}\n\n"
        f"--- Pitch Deck Market Claims ---\n"
        f"TAM: {market.tam.value if market.tam else 'N/A'} (Year: {market.tam.year if market.tam else 'N/A'}, Source: {market.tam.source if market.tam else 'N/A'})\n"
        f"SAM: {market.sam.value if market.sam else 'N/A'} (Year: {market.sam.year if market.sam else 'N/A'}, Source: {market.sam.source if market.sam else 'N/A'})\n"
        f"SOM: {market.som.value if market.som else 'N/A'} (Year: {market.som.year if market.som else 'N/A'}, Source: {market.som.source if market.som else 'N/A'})\n"
        f"Growth Rate: {market.growth_rate or 'N/A'}\n"
        f"Growth Source: {market.growth_source or 'N/A'}\n"
        f"Key Trends: {market.key_trends}\n\n"
        f"--- Previous Research Audits ---\n"
        f"Queries Already Used: {market.queries_used}\n"
        f"Research Sources Sourced: {[src.url for src in market.research_sources]}\n"
    )

    # 3. LLM Gap Assessment
    try:
        planner_agent = AgentRegistry.market_planner.with_structured_output(MarketPlannerDecision)
        decision = await planner_agent.ainvoke([
            SystemMessage(content=PromptRegistry.market_planner_system.value),
            HumanMessage(content=context)
        ])
        
        logger.info(
            "Market Planner gap assessment completed", 
            run_id=analysis_state.run_id, 
            status=decision.status, 
            query_count=len(decision.queries)
        )

        # 4. State Writing
        if decision.status == "INCOMPLETE" and decision.queries:
            # Add queries to queries_used
            for q in decision.queries:
                if q.query not in market.queries_used:
                    market.queries_used.append(q.query)
            
            # Increment attempts counter
            state["market_research_attempts"] = attempts + 1
            logger.info("Generated new market gap queries", run_id=analysis_state.run_id, queries=[q.query for q in decision.queries])

    except Exception as e:
        logger.error("Error in market planner node", run_id=analysis_state.run_id, error=str(e))
        # Keep moving forward on error to prevent pipeline freeze
        pass

    return {"analysis_state": analysis_state}
