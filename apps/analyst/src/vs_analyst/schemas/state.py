from pydantic import BaseModel, Field
from typing import Annotated, List, Optional, Dict, Any, Sequence
from datetime import datetime, timezone
import operator

from langchain_core.messages import BaseMessage

from .company import CompanySchema
from .user_inputs import UserInputSchema
from .founder import FounderSchema
from .market import MarketSchema
from .competitive import CompetitiveSchema, CompetitorSchema
from .due_diligence import DueDiligenceSchema
from .memo import MemoSchema

from .shared_enums import PipelineStatus, AgentStatus
from .shared_models import PipelineError


class AnalysisState(BaseModel):
    run_id: str = Field(..., description="uuid4 run identifier")
    raw_extraction: List[Any] = Field(default=list, description="raw extracted data from the pitch deck")
    raw_deck_text: Optional[str] = Field(default=None, description="Raw extracted text from the startup pitch deck")
    raw_website_text: Optional[str] = Field(default=None, description="Raw scraped text from the startup website")
    status: PipelineStatus = Field(default=PipelineStatus.PENDING, description="Overall pipeline status")
    agent_statuses: Optional[Dict[str, AgentStatus]] = Field(default_factory=dict, description="Status map per agent type")
    
    errors: List[PipelineError] = Field(default_factory=list, description="Errors logged during pipeline run")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of when the run was created")
    completed_at: Optional[datetime] = Field(default=None, description="Timestamp of when the run completed")

    user_input: UserInputSchema = Field(description="Initial user settings and deck path")
    company: CompanySchema = Field(default_factory=CompanySchema, description="Company profile: sector, business model, traction, red flags")
    founders: List[FounderSchema] = Field(default_factory=list, description="Verified founder backgrounds, education, career history, and personal red flags")
    market: MarketSchema = Field(default_factory=MarketSchema, description="Verified market sizing (TAM/SAM/SOM), CAGR, trends, and confidence levels")
    competitive: CompetitiveSchema = Field(default_factory=CompetitiveSchema, description="Competitor profiles, moat assessment, and competitive risk analysis")
    due_diligence: DueDiligenceSchema = Field(default_factory=DueDiligenceSchema, description="Regulatory/legal signals, traction verifications, press mentions, and org GitHub stats")
    memo: MemoSchema = Field(default_factory=MemoSchema, description="Investment memo sections, advisory recommendation (verdict/conviction/do/stop lists), SVG diagrams, and compiled PDF paths")


def merge_competitor_records(current: CompetitorSchema, update: CompetitorSchema) -> CompetitorSchema:
    """
    In-place merges fields from update competitor into current competitor.
    """
    for field in [
        "funding_stage", "funding_amount", "geography", "business_model",
        "founding_year", "positioning"
    ]:
        val = getattr(update, field, None)
        if val is not None and val != "":
            setattr(current, field, val)
            
    # Merge custom dimensions dict
    if update.custom_dimensions:
        current.custom_dimensions.update(update.custom_dimensions)
        
    # Merge key strengths list without duplicates
    for item in update.key_strengths:
        if item not in current.key_strengths:
            current.key_strengths.append(item)
            
    # Merge key weaknesses list without duplicates
    for item in update.key_weaknesses:
        if item not in current.key_weaknesses:
            current.key_weaknesses.append(item)
            
    # Merge profiling notes without duplicates
    for item in update.profiling_notes:
        if item not in current.profiling_notes:
            current.profiling_notes.append(item)
            
    # Merge sources list
    existing_urls = {src.url for src in current.sources if src.url}
    for src in update.sources:
        if src.url and src.url not in existing_urls:
            current.sources.append(src)
            existing_urls.add(src.url)
            
    return current


def merge_competitors_reducer(current: List[CompetitorSchema], updates: List[CompetitorSchema]) -> List[CompetitorSchema]:
    """
    Merges updates into the current list of competitors without duplication based on competitor name.
    """
    competitor_map = {c.name.lower(): c for c in current}
    for updated_competitor in updates:
        key = updated_competitor.name.lower()
        if key in competitor_map:
            competitor_map[key] = merge_competitor_records(competitor_map[key], updated_competitor)
        else:
            competitor_map[key] = updated_competitor
    return list(competitor_map.values())


def merge_founder_records(current: FounderSchema, update: FounderSchema) -> FounderSchema:
    """
    In-place merges fields from update founder into current founder.
    """
    for field in [
        "role", "linkedin_url", "linkedin_summary", "verified_background", "github_url",
        "github_public_repos", "github_account_age", "github_active"
    ]:
        val = getattr(update, field, None)
        if val is not None and val != "":
            setattr(current, field, val)

    # Merge bio_from_deck (only if current doesn't have it)
    if not current.bio_from_deck and update.bio_from_deck:
        current.bio_from_deck = update.bio_from_deck

    # Merge simple lists
    for item in update.past_companies:
        if item not in current.past_companies:
            current.past_companies.append(item)
            
    for item in update.past_roles:
        if item not in current.past_roles:
            current.past_roles.append(item)
            
    if update.notable_achievements:
        if not current.notable_achievements:
            current.notable_achievements = update.notable_achievements
        else:
            for item in update.notable_achievements:
                if item not in current.notable_achievements:
                    current.notable_achievements.append(item)

    if update.red_flags:
        if not current.red_flags:
            current.red_flags = update.red_flags
        else:
            for item in update.red_flags:
                if item not in current.red_flags:
                    current.red_flags.append(item)

    # Github list fields
    for item in update.github_languages:
        if item not in current.github_languages:
            current.github_languages.append(item)
    for item in update.github_oss_notable:
        if item not in current.github_oss_notable:
            current.github_oss_notable.append(item)

    # Merge education sub-models list without duplicates based on collage/level/branch
    if update.education:
        if not current.education:
            current.education = update.education
        else:
            existing_edu = {
                (e.collage.lower() if e.collage else "", 
                 e.level.lower() if e.level else "", 
                 e.branch.lower() if e.branch else "") 
                for e in current.education
            }
            for e in update.education:
                key = (
                    e.collage.lower() if e.collage else "", 
                    e.level.lower() if e.level else "", 
                    e.branch.lower() if e.branch else ""
                )
                if key not in existing_edu:
                    current.education.append(e)
                    existing_edu.add(key)

    return current


def merge_founders_reducer(current: List[FounderSchema], updates: List[FounderSchema]) -> List[FounderSchema]:
    """
    Merges updates into the current list of founders without duplication based on founder name.
    """
    founder_map = {f.name.lower(): f for f in current}
    for updated_founder in updates:
        key = updated_founder.name.lower()
        if key in founder_map:
            founder_map[key] = merge_founder_records(founder_map[key], updated_founder)
        else:
            founder_map[key] = updated_founder
    return list(founder_map.values())


def reduce_analysis_state(left: AnalysisState, right: AnalysisState) -> AnalysisState:
    """
    State reducer for parallel graph updates.
    Intelligently merges competitive data, sources, and other top-level fields.
    """
    # 1. Merge competitors
    left.competitive.competitors = merge_competitors_reducer(
        left.competitive.competitors,
        right.competitive.competitors
    )
    
    # 2. Merge competitive custom dimensions keys
    if right.competitive.custom_dimension_keys:
        left.competitive.custom_dimension_keys = list(
            set(left.competitive.custom_dimension_keys + right.competitive.custom_dimension_keys)
        )
        
    # 3. Merge competitive analysis strings if updated
    if right.competitive.moat_assessment:
        left.competitive.moat_assessment = right.competitive.moat_assessment
    if right.competitive.competitive_risk:
        left.competitive.competitive_risk = right.competitive.competitive_risk
    if right.competitive.summary:
        left.competitive.summary = right.competitive.summary
        
    # 4. Merge competitive audit trail
    if right.competitive.queries_used:
        left.competitive.queries_used = list(set(left.competitive.queries_used + right.competitive.queries_used))
        
    if right.competitive.research_sources:
        existing_urls = {src.url for src in left.competitive.research_sources if src.url}
        for src in right.competitive.research_sources:
            if src.url and src.url not in existing_urls:
                left.competitive.research_sources.append(src)
                existing_urls.add(src.url)

    # 5. Merge other top-level fields
    if right.company != left.company and right.company.name:
        left.company = right.company
        
    if right.founders:
        left.founders = merge_founders_reducer(left.founders, right.founders)
        
    if right.due_diligence:
        # Merge regulatory_flags
        for item in right.due_diligence.regulatory_flags:
            if item not in left.due_diligence.regulatory_flags:
                left.due_diligence.regulatory_flags.append(item)
                
        # Merge patent_mentions
        for item in right.due_diligence.patent_mentions:
            if item not in left.due_diligence.patent_mentions:
                left.due_diligence.patent_mentions.append(item)
                
        # Merge legal_notes
        for item in right.due_diligence.legal_notes:
            if item not in left.due_diligence.legal_notes:
                left.due_diligence.legal_notes.append(item)
                
        # Merge red_flags
        for item in right.due_diligence.red_flags:
            if item not in left.due_diligence.red_flags:
                left.due_diligence.red_flags.append(item)
                
        # Merge queries_used
        for item in right.due_diligence.queries_used:
            if item not in left.due_diligence.queries_used:
                left.due_diligence.queries_used.append(item)
                
        # Merge research_sources
        existing_sources = {src.url for src in left.due_diligence.research_sources if src.url}
        for src in right.due_diligence.research_sources:
            if src.url and src.url not in existing_sources:
                left.due_diligence.research_sources.append(src)
                existing_sources.add(src.url)
                
        # Merge press_mentions
        existing_press = {m.title.lower() for m in left.due_diligence.press_mentions if m.title}
        for p in right.due_diligence.press_mentions:
            if p.title and p.title.lower() not in existing_press:
                left.due_diligence.press_mentions.append(p)
                existing_press.add(p.title.lower())
            elif p.title:
                # Update existing press details if they are filled in right and empty in left
                for existing_p in left.due_diligence.press_mentions:
                    if existing_p.title and existing_p.title.lower() == p.title.lower():
                        if not existing_p.url and p.url:
                            existing_p.url = p.url
                        if not existing_p.source and p.source:
                            existing_p.source = p.source
                        if not existing_p.date and p.date:
                            existing_p.date = p.date
                        if not existing_p.sentiment and p.sentiment:
                            existing_p.sentiment = p.sentiment
                        if not existing_p.snippet and p.snippet:
                            existing_p.snippet = p.snippet

        # Merge traction_checks
        existing_checks = {c.claim.lower() for c in left.due_diligence.traction_checks if c.claim}
        for c in right.due_diligence.traction_checks:
            if c.claim and c.claim.lower() not in existing_checks:
                left.due_diligence.traction_checks.append(c)
                existing_checks.add(c.claim.lower())
            elif c.claim:
                for existing_c in left.due_diligence.traction_checks:
                    if existing_c.claim and existing_c.claim.lower() == c.claim.lower():
                        if existing_c.verified is None and c.verified is not None:
                            existing_c.verified = c.verified
                        if not existing_c.evidence and c.evidence:
                            existing_c.evidence = c.evidence
                        if not existing_c.source_url and c.source_url:
                            existing_c.source_url = c.source_url
                            
        # Merge summaries
        if right.due_diligence.press_summary:
            left.due_diligence.press_summary = right.due_diligence.press_summary
        if right.due_diligence.summary:
            left.due_diligence.summary = right.due_diligence.summary

        # Merge Github org details if updated
        if right.due_diligence.github:
            for field in [
                "org_url", "total_repos", "primary_language", "stars_primary_repo",
                "contributor_count", "commits_last_90d", "open_issues", "closed_issues",
                "last_commit_date", "license_type", "fetch_status"
            ]:
                val = getattr(right.due_diligence.github, field, None)
                if val is not None and val != "" and val != "pending" and val != DDStatus.PENDING:
                    setattr(left.due_diligence.github, field, val)
            if right.due_diligence.github.fetch_notes:
                for note in right.due_diligence.github.fetch_notes:
                    if note not in left.due_diligence.github.fetch_notes:
                        left.due_diligence.github.fetch_notes.append(note)

    if right.memo:
        # Merge memo sections
        for section_field in ["executive_summary", "company_overview", "market_analysis", "competitive_landscape", "team_assessment", "due_diligence_notes"]:
            r_val = getattr(right.memo, section_field)
            if r_val is not None:
                setattr(left.memo, section_field, r_val)
        
        # Merge advisory briefs/directives
        for brief_field in ["advocate_brief", "adversary_brief", "do_directive", "stop_directive"]:
            r_val = getattr(right.memo, brief_field)
            if r_val is not None:
                setattr(left.memo, brief_field, r_val)

        # Merge recommendation
        if right.memo.recommendation is not None:
            left.memo.recommendation = right.memo.recommendation

        # Merge review state
        if right.memo.review_decision is not None:
            left.memo.review_decision = right.memo.review_decision
        if right.memo.review_attempts != 0:
            left.memo.review_attempts = right.memo.review_attempts

        # Merge caveats without duplicates based on source and message
        existing_caveats = {(c.source.lower(), c.message.lower()) for c in left.memo.caveats}
        for c in right.memo.caveats:
            key = (c.source.lower(), c.message.lower())
            if key not in existing_caveats:
                left.memo.caveats.append(c)
                existing_caveats.add(key)

        # Merge full_markdown, html_pdf_path, typst_pdf_path
        if right.memo.full_markdown:
            left.memo.full_markdown = right.memo.full_markdown
        if right.memo.html_pdf_path:
            left.memo.html_pdf_path = right.memo.html_pdf_path
        if right.memo.typst_pdf_path:
            left.memo.typst_pdf_path = right.memo.typst_pdf_path

        # Merge diagrams dict
        if right.memo.diagrams:
            left.memo.diagrams.update(right.memo.diagrams)

    if right.agent_statuses:
        left.agent_statuses.update(right.agent_statuses)
        
    if right.errors:
        left.errors = list(set(left.errors + right.errors))
        
    return left


def reduce_optional_str(left: Optional[str], right: Optional[str]) -> Optional[str]:
    """
    Pass-through/latest-value reducer for optional strings in parallel updates.
    """
    return right if right is not None else left


class PipelineGraphState(dict):
    """
    The single shared global state for the LangGraph pipeline.
    Shared across ALL nodes and sub-graphs.

    Architecture:
      Intake → Company Sub-Graph → [Market, Competitor, Founder, Due-Diligence] (parallel) → Report Sub-Graph

    Fields:
      - messages:          LangGraph conversation history. Uses operator.add
                           so each node appends rather than replacing.
      - analysis_state:    The central Pydantic AnalysisState holding all domain
                           data (company, founders, market, competitive, due_diligence, memo).
                           Each sub-graph writes strictly to its own namespace.
      - raw_deck_text:     Raw extracted text from the pitch deck (in-memory).
      - raw_website_text:  Raw scraped text from the website (in-memory).
    """

    messages: Annotated[Sequence[BaseMessage], operator.add]
    analysis_state: Annotated[AnalysisState, reduce_analysis_state]
    raw_deck_text: Annotated[Optional[str], reduce_optional_str]
    raw_website_text: Annotated[Optional[str], reduce_optional_str]