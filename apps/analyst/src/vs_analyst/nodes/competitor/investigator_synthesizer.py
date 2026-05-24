from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.competitive import CompetitorSchema
from vs_analyst.schemas.state import AnalysisState
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


async def competitor_investigator_synthesizer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parallel Competitor Investigator Synthesizer Node.
    Consolidates research findings for a single competitor into a fully populated CompetitorSchema.
    Conforms to competitor_investigator_synthesizer.md spec.
    """
    analysis_state = state["analysis_state"]
    competitor = state["competitor"]
    
    logger.info(
        "Parallel Competitor Investigator Synthesizer started", 
        run_id=analysis_state.run_id, 
        competitor_name=competitor.name
    )

    company = analysis_state.company
    custom_dimension_keys = analysis_state.competitive.custom_dimension_keys

    # 1. Source Aggregation & Serialization
    sources_text = ""
    if competitor.sources:
        for idx, src in enumerate(competitor.sources, 1):
            sources_text += (
                f"Source {idx}:\n"
                f"  Title: {src.title or 'N/A'}\n"
                f"  URL: {src.url or 'N/A'}\n"
                f"  Snippet: {src.snippet or 'N/A'}\n\n"
            )
    else:
        sources_text = "No crawling research sources found for this competitor.\n"

    context = (
        f"--- Target Startup Company Profile ---\n"
        f"Name: {company.name or 'N/A'}\n"
        f"Sector: {company.sector or 'N/A'}\n"
        f"Business Model: {company.business_model.value if company.business_model else 'N/A'}\n\n"
        f"--- Competitor Existing Fields under Profiling ---\n"
        f"Competitor Name: {competitor.name}\n"
        f"Website: {str(competitor.website_url) if competitor.website_url else 'N/A'}\n"
        f"Type: {competitor.competitor_type.value if competitor.competitor_type else 'N/A'}\n"
        f"Positioning: {competitor.positioning or 'N/A'}\n"
        f"Geography: {competitor.geography or 'N/A'}\n"
        f"Founding Year: {competitor.founding_year or 'N/A'}\n"
        f"Funding Stage: {competitor.funding_stage or 'N/A'}\n"
        f"Funding Amount: {competitor.funding_amount or 'N/A'}\n"
        f"Key Strengths: {competitor.key_strengths}\n"
        f"Key Weaknesses: {competitor.key_weaknesses}\n"
        f"Custom Dimensions Required keys: {custom_dimension_keys}\n\n"
        f"--- Accumulated Crawled Research Sources ---\n"
        f"{sources_text}"
    )

    # 2. Invoke LLM for single competitor profiling
    try:
        synthesizer_agent = AgentRegistry.competitor_investigator_synthesizer.with_structured_output(CompetitorSchema)
        result = await synthesizer_agent.ainvoke([
            SystemMessage(content=PromptRegistry.competitor_investigator_synthesizer_system.value),
            HumanMessage(content=context)
        ])

        logger.info(
            "Competitor Investigator Synthesis completed successfully", 
            run_id=analysis_state.run_id, 
            competitor_name=competitor.name
        )

        # Merge findings back into competitor in-place
        competitor.funding_stage = result.funding_stage
        competitor.funding_amount = result.funding_amount
        competitor.geography = result.geography
        competitor.business_model = result.business_model
        competitor.founding_year = result.founding_year
        competitor.positioning = result.positioning
        competitor.key_strengths = result.key_strengths
        competitor.key_weaknesses = result.key_weaknesses
        
        # Populate custom dimensions (write 'Not found' if missing)
        competitor.custom_dimensions = {}
        for key in custom_dimension_keys:
            val = result.custom_dimensions.get(key, "Not found")
            competitor.custom_dimensions[key] = val

        # Profiling notes and sources
        if result.profiling_notes:
            competitor.profiling_notes = list(set(competitor.profiling_notes + result.profiling_notes))
            
        for src in result.sources:
            if src not in competitor.sources:
                competitor.sources.append(src)

    except Exception as e:
        logger.error(
            "Error in competitor investigator synthesizer node", 
            run_id=analysis_state.run_id, 
            competitor_name=competitor.name, 
            error=str(e)
        )
        # Fallback to defaults
        for key in custom_dimension_keys:
            if key not in competitor.custom_dimensions:
                competitor.custom_dimensions[key] = "Not found"

    # Construct the update to parent state. Merged by reduce_analysis_state reducer.
    parent_update = AnalysisState(
        run_id=analysis_state.run_id,
        user_input=analysis_state.user_input,
        created_at=analysis_state.created_at
    )
    parent_update.competitive.competitors = [competitor]

    return {"analysis_state": parent_update}
