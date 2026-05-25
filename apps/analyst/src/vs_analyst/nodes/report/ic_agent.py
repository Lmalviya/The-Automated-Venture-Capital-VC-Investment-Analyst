# ic_agent.py
from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.state import PipelineGraphState, AnalysisState
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

async def venture_partner_ic_agent_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Venture Partner IC Chairperson Node.
    Weighs the Advocate's Bull brief against the Adversary's Bear brief,
    integrates the Growth Strategist's DO and Hazard Mitigator's STOP directives,
    and produces the final, balanced InvestmentRecommendation.
    Conforms to report_sub_graph.md specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Venture Partner IC Chairperson node started", run_id=analysis_state.run_id)

    # 1. Access briefs & directives
    memo = analysis_state.memo
    advocate = memo.advocate_brief
    adversary = memo.adversary_brief
    do_dir = memo.do_directive
    stop_dir = memo.stop_directive

    # Compile the debates context block
    advocate_thesis = advocate.thesis if advocate else "No thesis provided."
    advocate_evidence = "\n".join([f"  - {e}" for e in advocate.supporting_evidence]) if advocate else "  - None"

    adversary_thesis = adversary.thesis if adversary else "No thesis provided."
    adversary_evidence = "\n".join([f"  - {e}" for e in adversary.supporting_evidence]) if adversary else "  - None"

    do_actions = "\n".join([f"  - {a}" for a in do_dir.actions]) if do_dir else "  - None"
    stop_actions = "\n".join([f"  - {a}" for a in stop_dir.actions]) if stop_dir else "  - None"

    context = (
        f"Target Startup: {analysis_state.company.name or 'N/A'}\n"
        f"Sector / Value Proposition: {analysis_state.company.sector or 'N/A'} | {analysis_state.company.value_proposition or 'N/A'}\n\n"
        f"================= BATTLE OF THE PERSÓNAS =================\n\n"
        f"--- INVESTMENT ADVOCATE BRIEF (The Bull) ---\n"
        f"Thesis Narrative:\n{advocate_thesis}\n"
        f"Key Supporting Evidence:\n{advocate_evidence}\n\n"
        f"--- INVESTMENT ADVERSARY BRIEF (The Bear) ---\n"
        f"Thesis Narrative:\n{adversary_thesis}\n"
        f"Key Structural Concerns:\n{adversary_evidence}\n\n"
        f"--- GROWTH STRATEGIC DIRECTIVES (DO LIST) ---\n"
        f"{do_actions}\n\n"
        f"--- HAZARD MITIGATION DIRECTIVES (STOP LIST) ---\n"
        f"{stop_actions}\n"
        f"==========================================================\n"
    )

    try:
        recommendation = await AgentRegistry.venture_partner_ic.ainvoke([
            SystemMessage(content=PromptRegistry.venture_partner_ic_system.value),
            HumanMessage(content=context)
        ])

        # Write to state update
        parent_update = AnalysisState(
            run_id=analysis_state.run_id,
            user_input=analysis_state.user_input,
            created_at=analysis_state.created_at
        )
        parent_update.memo.recommendation = recommendation
        parent_update.agent_statuses = {"venture_partner_ic": AgentStatus.COMPLETE}

        logger.info(
            "Venture Partner IC Chairperson successfully produced recommendation",
            run_id=analysis_state.run_id,
            verdict=recommendation.verdict.value if recommendation.verdict else "N/A",
            conviction=recommendation.conviction_score
        )
        return {"analysis_state": parent_update}

    except Exception as e:
        logger.error("Error in venture_partner_ic_agent_node", run_id=analysis_state.run_id, error=str(e))
        raise e
