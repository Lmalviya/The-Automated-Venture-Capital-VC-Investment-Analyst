# reviewer.py
from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.state import PipelineGraphState, AnalysisState
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

async def memo_reviewer_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Memo Reviewer Node (LLM-as-a-Judge).
    Performs factual pinning, omission checks, and verdict coherence audits.
    Outputs a ReviewDecision and increments the review attempts counter.
    Conforms to report_sub_graph.md specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Memo Reviewer node started", run_id=analysis_state.run_id)

    # 1. Compile Drafts Context
    memo = analysis_state.memo
    
    exec_summary_text = memo.executive_summary.content if memo.executive_summary else "N/A"
    market_text = memo.market_analysis.content if memo.market_analysis else "N/A"
    competitive_text = memo.competitive_landscape.content if memo.competitive_landscape else "N/A"
    team_text = memo.team_assessment.content if memo.team_assessment else "N/A"
    dd_text = memo.due_diligence_notes.content if memo.due_diligence_notes else "N/A"

    rec_verdict = memo.recommendation.verdict.value if (memo.recommendation and memo.recommendation.verdict) else "N/A"
    rec_score = memo.recommendation.conviction_score if memo.recommendation else "N/A"
    rec_thesis = memo.recommendation.investment_thesis if memo.recommendation else "N/A"
    rec_strengths = memo.recommendation.key_strengths if memo.recommendation else []
    rec_risks = memo.recommendation.key_risks if memo.recommendation else []

    # 2. Compile Ground Truth Context
    company = analysis_state.company
    market = analysis_state.market
    competitive = analysis_state.competitive
    founders = analysis_state.founders
    due_diligence = analysis_state.due_diligence

    # Ground truth red flags
    all_ground_truth_red_flags = []
    if company.red_flags:
        all_ground_truth_red_flags.extend([f"Company: {f}" for f in company.red_flags])
    for f in founders:
        if f.red_flags:
            all_ground_truth_red_flags.extend([f"Founder {f.name}: {flag}" for flag in f.red_flags])
    if due_diligence.red_flags:
        all_ground_truth_red_flags.extend([f"Due Diligence: {f}" for f in due_diligence.red_flags])

    # Ground truth TAM/SAM/SOM
    tam_val = market.tam.value if market.tam else "N/A"
    sam_val = market.sam.value if market.sam else "N/A"
    som_val = market.som.value if market.som else "N/A"
    cagr_val = market.growth_rate or "N/A"

    # Founders
    founder_details = ", ".join([f"{f.name} ({f.role.value if f.role else 'N/A'})" for f in founders])

    context = (
        f"================ DRAFTED SECTIONS UNDER AUDIT ================\n\n"
        f"--- 1. Executive Summary Draft ---\n{exec_summary_text}\n\n"
        f"--- 2. Market Analysis Draft ---\n{market_text}\n\n"
        f"--- 3. Competitive Landscape Draft ---\n{competitive_text}\n\n"
        f"--- 4. Team Assessment Draft ---\n{team_text}\n\n"
        f"--- 5. Due Diligence Notes Draft ---\n{dd_text}\n\n"
        f"--- Chairperson Final Recommendation ---\n"
        f"Verdict: {rec_verdict} (Score: {rec_score}/10)\n"
        f"Thesis:\n{rec_thesis}\n"
        f"Strengths: {rec_strengths}\n"
        f"Risks: {rec_risks}\n\n"
        f"================ GROUND TRUTH REFERENCE DATA ================\n\n"
        f"Company Name: {company.name or 'N/A'}\n"
        f"Market Sizing Ground Truth: TAM={tam_val}, SAM={sam_val}, SOM={som_val}, CAGR={cagr_val}\n"
        f"Founding Team List: {founder_details}\n"
        f"All Collected Red Flags:\n" + "\n".join([f"- {flag}" for flag in all_ground_truth_red_flags]) + "\n\n"
        f"Competitors Count: {len(competitive.competitors)}\n"
        f"=============================================================\n"
    )

    try:
        decision = await AgentRegistry.memo_reviewer.ainvoke([
            SystemMessage(content=PromptRegistry.memo_reviewer_system.value),
            HumanMessage(content=context)
        ])

        # Increment attempts counter
        attempts = memo.review_attempts + 1

        # Write to state update
        parent_update = AnalysisState(
            run_id=analysis_state.run_id,
            user_input=analysis_state.user_input,
            created_at=analysis_state.created_at
        )
        parent_update.memo.review_decision = decision
        parent_update.memo.review_attempts = attempts
        parent_update.agent_statuses = {"memo_reviewer": AgentStatus.COMPLETE}

        logger.info(
            "Memo Reviewer completed audit",
            run_id=analysis_state.run_id,
            status=decision.status,
            critique_count=len(decision.critiques),
            attempt=attempts
        )
        return {"analysis_state": parent_update}

    except Exception as e:
        logger.error("Error in memo_reviewer_node", run_id=analysis_state.run_id, error=str(e))
        raise e
