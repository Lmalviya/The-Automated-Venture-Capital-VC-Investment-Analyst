from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.adapters import MarketSynthesizerAdaptor
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


async def market_synthesizer_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Market Synthesizer Node.
    Consolidates pitch deck claims with independent research sources to produce a verified market profile.
    Conforms to market_synthesizer.md spec.
    """
    analysis_state = state["analysis_state"]
    logger.info("Market Synthesizer node started", run_id=analysis_state.run_id)

    company = analysis_state.company
    market = analysis_state.market

    # 1. Source Aggregation & Serialization
    sources_text = ""
    if market.research_sources:
        for idx, src in enumerate(market.research_sources, 1):
            sources_text += (
                f"Source {idx}:\n"
                f"  Title: {src.title or 'N/A'}\n"
                f"  URL: {src.url or 'N/A'}\n"
                f"  Snippet: {src.snippet or 'N/A'}\n\n"
            )
    else:
        sources_text = "No independent research sources found.\n"

    # Context setup for LLM
    context = (
        f"--- Company Profile ---\n"
        f"Name: {company.name or 'N/A'}\n"
        f"Sector: {company.sector or 'N/A'}\n"
        f"Business Model: {company.business_model.value if company.business_model else 'N/A'}\n"
        f"Value Proposition: {company.value_proposition or 'N/A'}\n\n"
        f"--- Startup Pitch Deck Claims ---\n"
        f"TAM: {market.tam.value if market.tam else 'N/A'} (Year: {market.tam.year if market.tam else 'N/A'}, Source: {market.tam.source if market.tam else 'N/A'})\n"
        f"SAM: {market.sam.value if market.sam else 'N/A'} (Year: {market.sam.year if market.sam else 'N/A'}, Source: {market.sam.source if market.sam else 'N/A'})\n"
        f"SOM: {market.som.value if market.som else 'N/A'} (Year: {market.som.year if market.som else 'N/A'}, Source: {market.som.source if market.som else 'N/A'})\n"
        f"Growth Rate (CAGR): {market.growth_rate or 'N/A'}\n"
        f"Growth Source: {market.growth_source or 'N/A'}\n"
        f"Key Trends: {market.key_trends}\n\n"
        f"--- Collected Independent Research Sources ---\n"
        f"{sources_text}"
    )

    # 2. Invoke LLM for synthesis
    try:
        synthesizer_agent = AgentRegistry.market_synthesizer.with_structured_output(MarketSynthesizerAdaptor)
        result = await synthesizer_agent.ainvoke([
            SystemMessage(content=PromptRegistry.market_synthesizer_system.value),
            HumanMessage(content=context)
        ])

        logger.info("Market synthesis completed successfully", run_id=analysis_state.run_id)

        # 3. Update the state (overwrite verified fields, preserve audit trail)
        market.tam = result.tam
        market.sam = result.sam
        market.som = result.som
        market.growth_rate = result.growth_rate
        market.growth_source = result.growth_source
        market.key_trends = result.key_trends
        market.summary = result.summary
        market.overall_confidence = result.overall_confidence

    except Exception as e:
        logger.error("Error in market synthesizer node", run_id=analysis_state.run_id, error=str(e))
        # Fallback to deck claims if LLM fails
        logger.info("Falling back to startup deck claims due to exception", run_id=analysis_state.run_id)
        if market.tam:
            market.tam.confidence = "low"
            market.tam.notes = "Web verification failed/unavailable due to LLM error. Using initial pitch deck claims."
        if market.sam:
            market.sam.confidence = "low"
            market.sam.notes = "Web verification failed/unavailable due to LLM error. Using initial pitch deck claims."
        if market.som:
            market.som.confidence = "low"
            market.som.notes = "Web verification failed/unavailable due to LLM error. Using initial pitch deck claims."
        
        market.overall_confidence = "low"
        if not market.summary:
            market.summary = "Market profile populated from deck claims. Independent web verification was unavailable."

    return {"analysis_state": analysis_state}
