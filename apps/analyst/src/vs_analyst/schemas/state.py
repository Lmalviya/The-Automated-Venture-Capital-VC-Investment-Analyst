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
        left.founders = right.founders
        
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