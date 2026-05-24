from typing import Any, Dict, List
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.founder import FounderSchema
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.schemas.state import AnalysisState
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


class FounderRiskAssessment(BaseModel):
    red_flags: List[str] = Field(
        default_factory=list,
        description="Concise concern strings identifying inconsistencies, unexplained gaps, title inflation, or other risks found during audit."
    )


async def founder_risk_analyst_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parallel Founder Risk Analyst Node.
    Audits a single founder's stated pitch deck bio against verified findings.
    Appends generated red flags to the FounderSchema and updates status.
    Conforms to founder_sub_graph.md and Phase 5 specs.
    """
    analysis_state = state["analysis_state"]
    founder = state["founder"]

    logger.info(
        "Parallel Founder Risk Auditor started",
        run_id=analysis_state.run_id,
        founder_name=founder.name
    )

    # 1. Compile verified details context
    edu_text = ""
    if founder.education:
        for idx, edu in enumerate(founder.education, 1):
            edu_text += f"  Degree {idx}: {edu.level} in {edu.branch} from {edu.collage} (Grad: {edu.passing_year or 'N/A'})\n"
    else:
        edu_text = "  None verified\n"

    context = (
        f"Founder Profile under Audit:\n"
        f"Name: {founder.name}\n"
        f"Role: {founder.role.value if founder.role else 'unknown'}\n\n"
        f"--- Stated Bio Claim from Pitch Deck ---\n"
        f"'{founder.bio_from_deck or 'No deck bio claim provided.'}'\n\n"
        f"--- Verified Third-Party Findings ---\n"
        f"LinkedIn URL: {founder.linkedin_url or 'None found'}\n"
        f"LinkedIn Summary: {founder.linkedin_summary or 'N/A'}\n"
        f"Verified Background Details: {founder.verified_background or 'N/A'}\n"
        f"Verified Education:\n{edu_text}"
        f"Verified Past Companies: {founder.past_companies}\n"
        f"Verified Past Roles: {founder.past_roles}\n"
        f"Notable Achievements: {founder.notable_achievements}\n"
    )

    # 2. Invoke LLM structured audit
    try:
        structured_risk_agent = AgentRegistry.founder_risk_analyst.with_structured_output(FounderRiskAssessment)
        assessment = await structured_risk_agent.ainvoke([
            SystemMessage(content=PromptRegistry.founder_risk_analyst_system.value),
            HumanMessage(content=context)
        ])

        # 3. Append discovered red flags
        if assessment and assessment.red_flags:
            logger.info(
                "Discovered background discrepancies/red flags during audit", 
                founder_name=founder.name, 
                flag_count=len(assessment.red_flags)
            )
            
            if not founder.red_flags:
                founder.red_flags = []
            
            for flag in assessment.red_flags:
                if flag not in founder.red_flags:
                    founder.red_flags.append(flag)
        else:
            logger.info("Background audit completed with clean record", founder_name=founder.name)

    except Exception as e:
        logger.error(
            "Error in founder risk analyst node",
            run_id=analysis_state.run_id,
            founder_name=founder.name,
            error=str(e)
        )

    # 4. Build parent update and mark status COMPLETE
    parent_update = AnalysisState(
        run_id=analysis_state.run_id,
        user_input=analysis_state.user_input,
        created_at=analysis_state.created_at
    )
    parent_update.founders = [founder]
    parent_update.agent_statuses = {"founder": AgentStatus.COMPLETE}

    return {"analysis_state": parent_update}
