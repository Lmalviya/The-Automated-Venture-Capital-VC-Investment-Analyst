# advisory.py
from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.state import PipelineGraphState, AnalysisState
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

def _build_global_context(analysis_state: Any) -> str:
    """Helper to compile the full compiled state of all namespaces into a single domain context."""
    company = analysis_state.company
    market = analysis_state.market
    competitive = analysis_state.competitive
    founders = analysis_state.founders
    due_diligence = analysis_state.due_diligence

    # Founders
    founders_text = ""
    for idx, f in enumerate(founders, 1):
        founders_text += (
            f"Founder {idx}: {f.name} ({f.role.value if f.role else 'N/A'})\n"
            f"  Stated bio: {f.bio_from_deck or 'N/A'}\n"
            f"  LinkedIn summary: {f.linkedin_summary or 'N/A'}\n"
            f"  Verified background: {f.verified_background or 'N/A'}\n"
            f"  Achievements: {f.notable_achievements}\n"
            f"  Red Flags: {f.red_flags}\n\n"
        )

    # Competitors
    competitors_text = ""
    for c in competitive.competitors:
        competitors_text += (
            f"- Name: {c.name}\n"
            f"  Funding: {c.funding_amount or 'N/A'} (Stage: {c.funding_stage or 'N/A'})\n"
            f"  Positioning: {c.positioning or 'N/A'}\n"
            f"  Strengths: {c.key_strengths}\n"
            f"  Weaknesses: {c.key_weaknesses}\n\n"
        )

    # DD Traction checks
    checks_text = ""
    for c in due_diligence.traction_checks:
        checks_text += (
            f"- Traction claim: '{c.claim}'\n"
            f"  Verified? {c.verified}\n"
            f"  Evidence/Source: {c.evidence or 'N/A'} ({c.source_url or 'N/A'})\n\n"
        )

    return (
        f"================ STARTUP PROFILE GROUND TRUTH ================\n"
        f"Company Name: {company.name or 'N/A'}\n"
        f"Sector / Industry: {company.sector or 'N/A'}\n"
        f"Business Model: {company.business_model.value if company.business_model else 'N/A'}\n"
        f"Value Proposition: {company.value_proposition or 'N/A'}\n"
        f"Global Product/Biz Summary: {company.summary or 'N/A'}\n"
        f"Global Red Flags: {company.red_flags}\n\n"
        f"---------------- Market Dynamics ----------------\n"
        f"TAM: {market.tam.value if market.tam else 'N/A'} (Year: {market.tam.year if market.tam else 'N/A'}, Source: {market.tam.source if market.tam else 'N/A'})\n"
        f"SAM: {market.sam.value if market.sam else 'N/A'}\n"
        f"SOM: {market.som.value if market.som else 'N/A'}\n"
        f"CAGR/Growth: {market.growth_rate or 'N/A'} (Source: {market.growth_source or 'N/A'})\n"
        f"Key Trends: {market.key_trends}\n\n"
        f"---------------- Competitive Advantage ----------------\n"
        f"Moat Assessment: {competitive.moat_assessment or 'N/A'}\n"
        f"Competitive Landscape Summary: {competitive.summary or 'N/A'}\n"
        f"Competitors:\n{competitors_text}"
        f"---------------- Team Assessment ----------------\n"
        f"{founders_text}"
        f"---------------- Due Diligence & Verification ----------------\n"
        f"Legal standing notes: {due_diligence.legal_notes}\n"
        f"Regulatory standing & flags: {due_diligence.regulatory_flags}\n"
        f"Patent & IP Mentions: {due_diligence.patent_mentions}\n"
        f"Discovered Red Flags: {due_diligence.red_flags}\n"
        f"Traction Claim Verification Checks:\n{checks_text}"
        f"Press mentions summary: {due_diligence.press_summary or 'N/A'}\n"
        f"==============================================================\n"
    )


# 1. Investment Advocate Node (Bull)
async def investment_advocate_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Parallel Investment Advocate Node (Bull Case).
    Argues strongly in favor of the deal using verified positives.
    Conforms to report_sub_graph.md specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Investment Advocate node started", run_id=analysis_state.run_id)

    context = _build_global_context(analysis_state)

    try:
        brief = await AgentRegistry.investment_advocate.ainvoke([
            SystemMessage(content=PromptRegistry.investment_advocate_system.value),
            HumanMessage(content=context)
        ])

        # Write to transient update state
        parent_update = AnalysisState(
            run_id=analysis_state.run_id,
            user_input=analysis_state.user_input,
            created_at=analysis_state.created_at
        )
        parent_update.memo.advocate_brief = brief
        parent_update.agent_statuses = {"investment_advocate": AgentStatus.COMPLETE}

        logger.info("Investment Advocate node successfully completed", run_id=analysis_state.run_id)
        return {"analysis_state": parent_update}

    except Exception as e:
        logger.error("Error in investment_advocate_node", run_id=analysis_state.run_id, error=str(e))
        raise e


# 2. Investment Adversary Node (Bear)
async def investment_adversary_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Parallel Investment Adversary Node (Bear Case).
    Identifies all risks, flaws, gaps, and structural issues.
    Conforms to report_sub_graph.md specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Investment Adversary node started", run_id=analysis_state.run_id)

    context = _build_global_context(analysis_state)

    try:
        brief = await AgentRegistry.investment_adversary.ainvoke([
            SystemMessage(content=PromptRegistry.investment_adversary_system.value),
            HumanMessage(content=context)
        ])

        parent_update = AnalysisState(
            run_id=analysis_state.run_id,
            user_input=analysis_state.user_input,
            created_at=analysis_state.created_at
        )
        parent_update.memo.adversary_brief = brief
        parent_update.agent_statuses = {"investment_adversary": AgentStatus.COMPLETE}

        logger.info("Investment Adversary node successfully completed", run_id=analysis_state.run_id)
        return {"analysis_state": parent_update}

    except Exception as e:
        logger.error("Error in investment_adversary_node", run_id=analysis_state.run_id, error=str(e))
        raise e


# 3. Growth Strategist Node (DO list)
async def growth_strategist_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Parallel Growth Strategist Node (DO list).
    Formulates 3-5 immediate strategic actions with state-sourced rationales.
    Conforms to report_sub_graph.md specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Growth Strategist node started", run_id=analysis_state.run_id)

    context = _build_global_context(analysis_state)

    try:
        directive = await AgentRegistry.growth_strategist.ainvoke([
            SystemMessage(content=PromptRegistry.growth_strategist_system.value),
            HumanMessage(content=context)
        ])

        parent_update = AnalysisState(
            run_id=analysis_state.run_id,
            user_input=analysis_state.user_input,
            created_at=analysis_state.created_at
        )
        parent_update.memo.do_directive = directive
        parent_update.agent_statuses = {"growth_strategist": AgentStatus.COMPLETE}

        logger.info("Growth Strategist node successfully completed", run_id=analysis_state.run_id)
        return {"analysis_state": parent_update}

    except Exception as e:
        logger.error("Error in growth_strategist_node", run_id=analysis_state.run_id, error=str(e))
        raise e


# 4. Hazard Mitigator Node (STOP list)
async def hazard_mitigator_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Parallel Hazard Mitigator Node (STOP list).
    Formulates 3-5 critical operational hazard mitigations with state-sourced rationales.
    Conforms to report_sub_graph.md specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Hazard Mitigator node started", run_id=analysis_state.run_id)

    context = _build_global_context(analysis_state)

    try:
        directive = await AgentRegistry.hazard_mitigator.ainvoke([
            SystemMessage(content=PromptRegistry.hazard_mitigator_system.value),
            HumanMessage(content=context)
        ])

        parent_update = AnalysisState(
            run_id=analysis_state.run_id,
            user_input=analysis_state.user_input,
            created_at=analysis_state.created_at
        )
        parent_update.memo.stop_directive = directive
        parent_update.agent_statuses = {"hazard_mitigator": AgentStatus.COMPLETE}

        logger.info("Hazard Mitigator node successfully completed", run_id=analysis_state.run_id)
        return {"analysis_state": parent_update}

    except Exception as e:
        logger.error("Error in hazard_mitigator_node", run_id=analysis_state.run_id, error=str(e))
        raise e
