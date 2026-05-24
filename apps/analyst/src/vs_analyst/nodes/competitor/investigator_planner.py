from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.adapters import CompetitorInvestigatorDecision
from vs_analyst.config import settings
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


async def competitor_investigator_planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parallel Competitor Investigator Planner Node.
    Analyzes a single competitor for fixed and custom dimension gaps.
    Conforms to competitor_investigator_planner.md spec.
    """
    analysis_state = state["analysis_state"]
    competitor = state["competitor"]
    attempts = state.get("competitor_research_attempts", 0)
    
    logger.info(
        "Parallel Competitor Investigator Planner started", 
        run_id=analysis_state.run_id, 
        competitor_name=competitor.name,
        attempts=attempts
    )

    # 1. Attempts Check
    max_attempts = getattr(settings, "competitor_research_max_attempts", 2)
    if attempts >= max_attempts:
        logger.info(
            "Max research attempts reached for competitor.",
            run_id=analysis_state.run_id,
            competitor_name=competitor.name,
            attempts=attempts
        )
        return {
            "competitor": competitor,
            "competitor_planner_decision": CompetitorInvestigatorDecision(status="COMPLETE", queries=[]),
            "competitor_research_attempts": attempts
        }

    # 2. Context Setup
    company = analysis_state.company
    custom_dimension_keys = analysis_state.competitive.custom_dimension_keys

    context = (
        f"--- Target Startup Company Profile ---\n"
        f"Name: {company.name or 'N/A'}\n"
        f"Sector: {company.sector or 'N/A'}\n"
        f"Business Model: {company.business_model.value if company.business_model else 'N/A'}\n\n"
        f"--- Competitor Profile Under Investigation ---\n"
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
        f"Custom Dimensions Filled: {competitor.custom_dimensions}\n"
        f"Custom Dimension Keys Required: {custom_dimension_keys}\n\n"
        f"--- Queries Already Run ---\n"
        f"{competitor.queries_used}\n"
    )

    # 3. Invoke LLM Gap Assessment
    try:
        planner_agent = AgentRegistry.competitor_investigator_planner.with_structured_output(CompetitorInvestigatorDecision)
        decision = await planner_agent.ainvoke([
            SystemMessage(content=PromptRegistry.competitor_investigator_planner_system.value),
            HumanMessage(content=context)
        ])
        
        logger.info(
            "Competitor Investigator planning completed", 
            run_id=analysis_state.run_id, 
            competitor_name=competitor.name,
            status=decision.status, 
            query_count=len(decision.queries)
        )

        # 4. State Writing (Branch-Local)
        if decision.status == "INCOMPLETE" and decision.queries:
            for q in decision.queries:
                if q.query not in competitor.queries_used:
                    competitor.queries_used.append(q.query)
            
            # Increment attempts
            attempts += 1

        return {
            "competitor": competitor,
            "competitor_planner_decision": decision,
            "competitor_research_attempts": attempts
        }

    except Exception as e:
        logger.error(
            "Error in competitor investigator planner node", 
            run_id=analysis_state.run_id, 
            competitor_name=competitor.name, 
            error=str(e)
        )
        return {
            "competitor": competitor,
            "competitor_planner_decision": CompetitorInvestigatorDecision(status="COMPLETE", queries=[]),
            "competitor_research_attempts": attempts
        }
