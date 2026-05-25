# section_writers.py
from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.state import PipelineGraphState, AnalysisState
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

def _get_critique_extension(analysis_state: Any, section_field: str) -> str:
    """Helper to check for previous reviewer critiques and build a prompt correction directive."""
    if (analysis_state.memo and 
        analysis_state.memo.review_decision and 
        analysis_state.memo.review_decision.status == "REJECTED" and 
        analysis_state.memo.review_decision.critiques):
        
        section_critiques = [c for c in analysis_state.memo.review_decision.critiques if c.section_name == section_field]
        if section_critiques:
            logger.info("Injecting previous reviewer critiques into prompt", section=section_field, count=len(section_critiques))
            critique_text = "\n\n=== CRITICAL REVISION FEEDBACK ===\nYour previous draft was REJECTED by the auditor for factual issues/omissions. You MUST correct the following and revise your text accordingly:\n"
            for c in section_critiques:
                critique_text += f"- ISSUE: {c.issue}\n  CORRECTION DIRECTIVE: {c.correction_instruction}\n"
            critique_text += "==================================\n"
            return critique_text
    return ""


# 1. Executive Summary Writer Node
async def executive_summary_writer_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Parallel Executive Summary Writer Node.
    Synthesizes general information from all namespaces into a concise narrative overview.
    Conforms to report_sub_graph.md specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Executive Summary Writer node started", run_id=analysis_state.run_id)

    # 1. Build context
    company = analysis_state.company
    market = analysis_state.market
    competitive = analysis_state.competitive
    founders = analysis_state.founders
    due_diligence = analysis_state.due_diligence

    context = (
        f"--- Company Profile ---\n"
        f"Name: {company.name or 'N/A'}\n"
        f"Sector: {company.sector or 'N/A'}\n"
        f"Business Model: {company.business_model.value if company.business_model else 'N/A'}\n"
        f"Value Proposition: {company.value_proposition or 'N/A'}\n"
        f"Stated Company Summary: {getattr(company, 'summary', None) or getattr(company, 'problem_statement', 'N/A')}\n\n"
        f"--- Market Highlight ---\n"
        f"TAM: {market.tam.value if market.tam else 'N/A'} (Growth: {market.growth_rate or 'N/A'})\n\n"
        f"--- Competitive & Moat Summary ---\n"
        f"Moat Assessment: {competitive.moat_assessment or 'N/A'}\n"
        f"Landscape Summary: {competitive.summary or 'N/A'}\n\n"
        f"--- Founders List ---\n"
        f"{', '.join([f.name for f in founders]) or 'None listed'}\n\n"
        f"--- Due Diligence summary ---\n"
        f"DD Audit Summary: {due_diligence.summary or 'N/A'}\n"
    )

    # 2. Add Critique if present
    system_prompt = PromptRegistry.executive_summary_writer_system.value
    critique_ext = _get_critique_extension(analysis_state, "executive_summary")
    if critique_ext:
        system_prompt += critique_ext

    # 3. Call LLM
    try:
        draft = await AgentRegistry.executive_summary_writer.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ])
        
        draft.status = AgentStatus.COMPLETE
        draft.word_count = len(draft.content.split())
        
        # 4. Write back to temporary update state
        parent_update = AnalysisState(
            run_id=analysis_state.run_id,
            user_input=analysis_state.user_input,
            created_at=analysis_state.created_at
        )
        parent_update.memo.executive_summary = draft
        parent_update.agent_statuses = {"executive_summary_writer": AgentStatus.COMPLETE}
        
        logger.info("Executive Summary Writer node successfully completed", run_id=analysis_state.run_id)
        return {"analysis_state": parent_update}

    except Exception as e:
        logger.error("Error in executive_summary_writer_node", run_id=analysis_state.run_id, error=str(e))
        raise e


# 2. Market Section Writer Node
async def market_section_writer_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Parallel Market Section Writer Node.
    Produces rich Markdown TAM/SAM/SOM tables, CAGRs, and shape trends.
    Conforms to report_sub_graph.md specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Market Section Writer node started", run_id=analysis_state.run_id)

    market = analysis_state.market
    context = (
        f"--- Verified Market Segment Data ---\n"
        f"TAM: {market.tam.value if market.tam else 'N/A'} (Year: {market.tam.year if market.tam else 'N/A'}, Source: {market.tam.source if market.tam else 'N/A'})\n"
        f"SAM: {market.sam.value if market.sam else 'N/A'} (Year: {market.sam.year if market.sam else 'N/A'}, Source: {market.sam.source if market.sam else 'N/A'})\n"
        f"SOM: {market.som.value if market.som else 'N/A'} (Year: {market.som.year if market.som else 'N/A'}, Source: {market.som.source if market.som else 'N/A'})\n"
        f"CAGR/Growth Rate: {market.growth_rate or 'N/A'} (Source: {market.growth_source or 'N/A'})\n"
        f"Key Industry Trends: {market.key_trends}\n"
        f"Research Sources Used: {[src.url for src in market.research_sources]}\n"
    )

    system_prompt = PromptRegistry.market_section_writer_system.value
    critique_ext = _get_critique_extension(analysis_state, "market_analysis")
    if critique_ext:
        system_prompt += critique_ext

    try:
        draft = await AgentRegistry.market_section_writer.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ])
        
        draft.status = AgentStatus.COMPLETE
        draft.word_count = len(draft.content.split())

        parent_update = AnalysisState(
            run_id=analysis_state.run_id,
            user_input=analysis_state.user_input,
            created_at=analysis_state.created_at
        )
        parent_update.memo.market_analysis = draft
        parent_update.agent_statuses = {"market_section_writer": AgentStatus.COMPLETE}
        
        logger.info("Market Section Writer node successfully completed", run_id=analysis_state.run_id)
        return {"analysis_state": parent_update}

    except Exception as e:
        logger.error("Error in market_section_writer_node", run_id=analysis_state.run_id, error=str(e))
        raise e


# 3. Competitor Section Writer Node
async def competitor_section_writer_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Parallel Competitor Section Writer Node.
    Drafts competitive landscape narratives, moat scoring, and competitor threat lists.
    Conforms to report_sub_graph.md specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Competitor Section Writer node started", run_id=analysis_state.run_id)

    comp = analysis_state.competitive
    competitors_text = ""
    for c in comp.competitors:
        competitors_text += (
            f"- Name: {c.name}\n"
            f"  Funding: {c.funding_amount or 'N/A'} (Stage: {c.funding_stage or 'N/A'})\n"
            f"  Positioning/Model: {c.positioning or 'N/A'} ({c.business_model or 'N/A'})\n"
            f"  Strengths: {c.key_strengths}\n"
            f"  Weaknesses: {c.key_weaknesses}\n"
            f"  Profiling Notes: {c.profiling_notes}\n\n"
        )

    context = (
        f"--- Competitive Landscape Ground Truth ---\n"
        f"Moat Assessment Narrative: {comp.moat_assessment or 'N/A'}\n"
        f"Competitive Risk Rating: {comp.competitive_risk or 'N/A'}\n"
        f"Global Landscape Summary: {comp.summary or 'N/A'}\n"
        f"Custom Dimension Keys under Audit: {comp.custom_dimension_keys}\n\n"
        f"--- Detailed Competitor List ---\n"
        f"{competitors_text}"
    )

    system_prompt = PromptRegistry.competitor_section_writer_system.value
    critique_ext = _get_critique_extension(analysis_state, "competitive_landscape")
    if critique_ext:
        system_prompt += critique_ext

    try:
        draft = await AgentRegistry.competitor_section_writer.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ])
        
        draft.status = AgentStatus.COMPLETE
        draft.word_count = len(draft.content.split())

        parent_update = AnalysisState(
            run_id=analysis_state.run_id,
            user_input=analysis_state.user_input,
            created_at=analysis_state.created_at
        )
        parent_update.memo.competitive_landscape = draft
        parent_update.agent_statuses = {"competitor_section_writer": AgentStatus.COMPLETE}
        
        logger.info("Competitor Section Writer node successfully completed", run_id=analysis_state.run_id)
        return {"analysis_state": parent_update}

    except Exception as e:
        logger.error("Error in competitor_section_writer_node", run_id=analysis_state.run_id, error=str(e))
        raise e


# 4. Founder Section Writer Node
async def founder_section_writer_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Parallel Founder Section Writer Node.
    Writes background summaries, fit evaluations, and audit discrepancy red flags per founder.
    Conforms to report_sub_graph.md specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Founder Section Writer node started", run_id=analysis_state.run_id)

    founders = analysis_state.founders
    founders_text = ""
    for idx, f in enumerate(founders, 1):
        edu_text = ""
        if f.education:
            for e in f.education:
                edu_text += f"    * {e.level} in {e.branch} from {e.collage} (Grad: {e.passing_year or 'N/A'})\n"
        else:
            edu_text = "    * No verified education recorded\n"

        founders_text += (
            f"Founder {idx}: {f.name}\n"
            f"  Role: {f.role.value if f.role else 'N/A'}\n"
            f"  Stated bio: '{f.bio_from_deck or 'N/A'}'\n"
            f"  LinkedIn Summary: {f.linkedin_summary or 'N/A'}\n"
            f"  Verified Background: {f.verified_background or 'N/A'}\n"
            f"  Verified Education:\n{edu_text}"
            f"  Past Companies: {f.past_companies}\n"
            f"  Past Roles: {f.past_roles}\n"
            f"  Notable Achievements: {f.notable_achievements}\n"
            f"  GitHub Repo Stats: Age {f.github_account_age or 'N/A'} days, {f.github_public_repos or 'N/A'} repos, active: {f.github_active or 'N/A'}\n"
            f"  Audited Discrepancies / Red Flags: {f.red_flags}\n\n"
        )

    context = (
        f"--- Audited Founder Backgrounds ---\n"
        f"{founders_text}"
    )

    system_prompt = PromptRegistry.founder_section_writer_system.value
    critique_ext = _get_critique_extension(analysis_state, "team_assessment")
    if critique_ext:
        system_prompt += critique_ext

    try:
        draft = await AgentRegistry.founder_section_writer.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ])
        
        draft.status = AgentStatus.COMPLETE
        draft.word_count = len(draft.content.split())

        parent_update = AnalysisState(
            run_id=analysis_state.run_id,
            user_input=analysis_state.user_input,
            created_at=analysis_state.created_at
        )
        parent_update.memo.team_assessment = draft
        parent_update.agent_statuses = {"founder_section_writer": AgentStatus.COMPLETE}
        
        logger.info("Founder Section Writer node successfully completed", run_id=analysis_state.run_id)
        return {"analysis_state": parent_update}

    except Exception as e:
        logger.error("Error in founder_section_writer_node", run_id=analysis_state.run_id, error=str(e))
        raise e


# 5. Due Diligence Section Writer Node
async def dd_section_writer_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Parallel Due Diligence Section Writer Node.
    Synthesizes traction checks tables, news footprints, and compliance logs.
    Conforms to report_sub_graph.md specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Due Diligence Section Writer node started", run_id=analysis_state.run_id)

    dd = analysis_state.due_diligence

    # Format checks table
    checks_text = ""
    for c in dd.traction_checks:
        checks_text += (
            f"- Claim: '{c.claim}'\n"
            f"  Verified: {c.verified}\n"
            f"  Evidence: {c.evidence or 'N/A'}\n"
            f"  Source URL: {c.source_url or 'N/A'}\n\n"
        )

    # Format press mentions
    press_text = ""
    for p in dd.press_mentions:
        press_text += (
            f"- Title: {p.title}\n"
            f"  Source/Date: {p.source or 'N/A'} ({p.date or 'N/A'})\n"
            f"  URL: {p.url or 'N/A'}\n"
            f"  Snippet: {p.snippet or 'N/A'}\n"
            f"  Sentiment: {p.sentiment or 'N/A'}\n\n"
        )

    github_text = "N/A"
    if dd.github:
        github_text = (
            f"Org URL: {dd.github.org_url or 'N/A'}\n"
            f"Total Repos: {dd.github.total_repos or 'N/A'}\n"
            f"Primary Language: {dd.github.primary_language or 'N/A'}\n"
            f"Stars: {dd.github.stars_primary_repo or 'N/A'}\n"
            f"Contributors: {dd.github.contributor_count or 'N/A'}\n"
            f"Commits last 90 days: {dd.github.commits_last_90d or 'N/A'}\n"
            f"License Type: {dd.github.license_type or 'N/A'}\n"
        )

    context = (
        f"--- Due Diligence Verification Ground Truth ---\n"
        f"Legal Notes: {dd.legal_notes}\n"
        f"Regulatory Standing & Flags: {dd.regulatory_flags}\n"
        f"Patent & IP Filings: {dd.patent_mentions}\n"
        f"General Red Flags Discovered: {dd.red_flags}\n"
        f"Press Summary Narrative: {dd.press_summary or 'N/A'}\n"
        f"Due Diligence Cohesive Summary: {dd.summary or 'N/A'}\n\n"
        f"--- GitHub Org Technical Audit ---\n"
        f"{github_text}\n"
        f"--- Traction Checks Audited ---\n"
        f"{checks_text}\n"
        f"--- Stated/Discovered Press Coverage ---\n"
        f"{press_text}"
    )

    system_prompt = PromptRegistry.dd_section_writer_system.value
    critique_ext = _get_critique_extension(analysis_state, "due_diligence_notes")
    if critique_ext:
        system_prompt += critique_ext

    try:
        draft = await AgentRegistry.dd_section_writer.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ])
        
        draft.status = AgentStatus.COMPLETE
        draft.word_count = len(draft.content.split())

        parent_update = AnalysisState(
            run_id=analysis_state.run_id,
            user_input=analysis_state.user_input,
            created_at=analysis_state.created_at
        )
        parent_update.memo.due_diligence_notes = draft
        parent_update.agent_statuses = {"dd_section_writer": AgentStatus.COMPLETE}
        
        logger.info("Due Diligence Section Writer node successfully completed", run_id=analysis_state.run_id)
        return {"analysis_state": parent_update}

    except Exception as e:
        logger.error("Error in dd_section_writer_node", run_id=analysis_state.run_id, error=str(e))
        raise e
