from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.adapters import CompetitorDiscoveryResult
from vs_analyst.schemas.competitive import CompetitorSchema
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


async def competitor_finder_synthesizer_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Competitor Discovery Synthesizer Node.
    Consolidates the discovered candidate pool, deduplicates, and qualifiers.
    Conforms to competitor_finder_synthesizer.md spec.
    """
    analysis_state = state["analysis_state"]
    logger.info("Competitor Finder Synthesizer node started", run_id=analysis_state.run_id)

    company = analysis_state.company
    competitive = analysis_state.competitive

    # 1. Context Setup
    sources_text = ""
    if competitive.research_sources:
        for idx, src in enumerate(competitive.research_sources, 1):
            sources_text += (
                f"Source {idx}:\n"
                f"  Title: {src.title or 'N/A'}\n"
                f"  URL: {src.url or 'N/A'}\n"
                f"  Snippet: {src.snippet or 'N/A'}\n\n"
            )
    else:
        sources_text = "No discovery research sources accumulated yet.\n"

    context = (
        f"--- Startup Company Profile ---\n"
        f"Name: {company.name or 'N/A'}\n"
        f"Sector: {company.sector or 'N/A'}\n"
        f"Business Model: {company.business_model.value if company.business_model else 'N/A'}\n"
        f"Value Proposition: {company.value_proposition or 'N/A'}\n\n"
        f"--- Seed Competitors in Intake ---\n"
        f"{[{'name': c.name, 'website': str(c.website_url) if c.website_url else 'N/A'} for c in competitive.competitors]}\n\n"
        f"--- Accumulated Discovery Research ---\n"
        f"{sources_text}"
    )

    # 2. Invoke LLM for synthesis
    try:
        synthesizer_agent = AgentRegistry.competitor_finder_synthesizer.with_structured_output(CompetitorDiscoveryResult)
        result = await synthesizer_agent.ainvoke([
            SystemMessage(content=PromptRegistry.competitor_finder_synthesizer_system.value),
            HumanMessage(content=context)
        ])

        logger.info(
            "Competitor Discovery Synthesis completed successfully", 
            run_id=analysis_state.run_id, 
            competitor_count=len(result.qualified_competitors)
        )

        # 3. Merge & Deduplicate candidates into competitive.competitors
        competitor_map = {c.name.lower(): c for c in competitive.competitors}
        
        for entry in result.qualified_competitors:
            name_lower = entry.name.lower()
            if name_lower in competitor_map:
                # Merge into existing record
                existing = competitor_map[name_lower]
                if entry.website_url and not existing.website_url:
                    existing.website_url = entry.website_url
                if entry.competitor_type:
                    existing.competitor_type = entry.competitor_type
            else:
                # Create a new competitor schema record
                new_comp = CompetitorSchema(
                    name=entry.name,
                    website_url=entry.website_url,
                    competitor_type=entry.competitor_type,
                    positioning=entry.rationale
                )
                competitive.competitors.append(new_comp)

        # 4. Save Custom Dimension Keys
        competitive.custom_dimension_keys = result.custom_dimension_keys
        logger.info("Custom dimension keys locked", run_id=analysis_state.run_id, keys=result.custom_dimension_keys)

    except Exception as e:
        logger.error("Error in competitor finder synthesizer node", run_id=analysis_state.run_id, error=str(e))
        # Fallback to seed list if LLM fails
        logger.info("Falling back to initial seed competitor list", run_id=analysis_state.run_id)
        if not competitive.custom_dimension_keys:
            competitive.custom_dimension_keys = ["customer_feedback", "integrations"]

    return {"analysis_state": analysis_state}
