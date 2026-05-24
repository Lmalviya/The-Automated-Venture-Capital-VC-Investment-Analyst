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
    analysis_state: AnalysisState
    raw_deck_text: Optional[str]
    raw_website_text: Optional[str]