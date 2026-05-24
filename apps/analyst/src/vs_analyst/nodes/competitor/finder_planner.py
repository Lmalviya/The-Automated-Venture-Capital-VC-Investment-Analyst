from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.adapters import CompetitorPlannerDecision
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.config import settings
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


async def competitor_finder_planner_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Competitor Discovery Planner Node.
    Analyzes current competitors and queries to identify gaps.
    Conforms to competitor_finder_planner.md spec.
    """
    analysis_state = state["analysis_state"]
    logger.info("Competitor Finder Planner node started", run_id=analysis_state.run_id)

    # 1. Attempts Check
    attempts = state.get("competitor_search_attempts", 0)
    max_attempts = getattr(settings, "competitor_search_max_attempts", 2)
    if attempts >= max_attempts:
        logger.info(
            "Max competitor search attempts reached. Bypassing LLM.",
            run_id=analysis_state.run_id,
            attempts=attempts,
        )
        state["competitor_planner_decision"] = CompetitorPlannerDecision(status="COMPLETE", queries=[])
        return {"analysis_state": analysis_state}

    # 2. Context Setup
    company = analysis_state.company
    competitive = analysis_state.competitive

    context = (
        f"--- Startup Company Profile ---\n"
        f"Name: {company.name or 'N/A'}\n"
        f"Sector: {company.sector or 'N/A'}\n"
        f"Business Model: {company.business_model.value if company.business_model else 'N/A'}\n"
        f"Value Proposition: {company.value_proposition or 'N/A'}\n"
        f"ICP/Target Audience: {company.solution or 'N/A'}\n\n"
        f"--- Currently Identified Competitors ---\n"
        f"{[{'name': c.name, 'type': c.competitor_type.value if c.competitor_type else 'N/A'} for c in competitive.competitors]}\n\n"
        f"--- Previous Search Queries Used ---\n"
        f"{competitive.queries_used}\n"
    )

    # 3. Invoke LLM Gap Assessment
    try:
        planner_agent = AgentRegistry.competitor_finder_planner.with_structured_output(CompetitorPlannerDecision)
        decision = await planner_agent.ainvoke([
            SystemMessage(content=PromptRegistry.competitor_finder_planner_system.value),
            HumanMessage(content=context)
        ])
        
        logger.info(
            "Competitor Finder planning completed", 
            run_id=analysis_state.run_id, 
            status=decision.status, 
            query_count=len(decision.queries)
        )

        # 4. State Writing
        if decision.status == "INCOMPLETE" and decision.queries:
            # Append generated queries to competitive.queries_used
            for q in decision.queries:
                if q.query not in competitive.queries_used:
                    competitive.queries_used.append(q.query)
            
            # Increment attempts counter
            state["competitor_search_attempts"] = attempts + 1
        
        state["competitor_planner_decision"] = decision

    except Exception as e:
        logger.error("Error in competitor finder planner", run_id=analysis_state.run_id, error=str(e))
        state["competitor_planner_decision"] = CompetitorPlannerDecision(status="COMPLETE", queries=[])

    return {"analysis_state": analysis_state}
