from pydantic import BaseModel, Field
from typing import Annotated, List, Optional, Dict, Any, Sequence
from datetime import datetime, timezone
import operator

from langchain_core.messages import BaseMessage

from .company import CompanySchema
from .user_inputs import UserInputSchema
from .founder import FounderSchema
from .market import MarketSchema
from .competitive import CompetitiveSchema
from .due_diligence import DueDiligenceSchema
from .memo import MemoSchema

from .shared_enums import PipelineStatus, AgentStatus, DDStatus
from .shared_models import PipelineError

from vs_analyst.map_reducer import (
    merge_company_records,
    merge_competitors_reducer,
    merge_founders_reducer,
    merge_market_records,
)


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
    if right.company:
        left.company = merge_company_records(left.company, right.company)
        
    if right.market:
        left.market = merge_market_records(left.market, right.market)
        
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
