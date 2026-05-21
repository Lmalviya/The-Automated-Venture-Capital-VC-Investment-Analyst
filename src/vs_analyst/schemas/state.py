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
    status: PipelineStatus = Field(default=PipelineStatus.PENDING, description="Overall pipeline status")
    agent_statuses: Optional[Dict[str, AgentStatus]] = Field(default_factory=dict, description="Status map per agent type")
    
    errors: List[PipelineError] = Field(default_factory=list, description="Errors logged during pipeline run")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of when the run was created")
    completed_at: Optional[datetime] = Field(default=None, description="Timestamp of when the run completed")

    user_input: UserInputSchema = Field(description="Initial user settings and deck path")
    company: CompanySchema = Field(default_factory=CompanySchema, description="Company traction, sector, and red flags")
    founders: List[FounderSchema] = Field(default_factory=list, description="Founder backgrounds and personal verification status")
    market: MarketSchema = Field(default_factory=MarketSchema, description="Market size estimates (TAM/SAM/SOM) and dynamics")
    competitive: CompetitiveSchema = Field(default_factory=CompetitiveSchema, description="Competitors and overall competitive positioning")
    due_diligence: DueDiligenceSchema = Field(default_factory=DueDiligenceSchema, description="Due diligence, org GitHub stats, and press mentions")
    memo: MemoSchema = Field(default_factory=MemoSchema, description="Venture investment recommendation memo")


class PipelineGraphState(dict):
    """
    The single shared global state for the LangGraph pipeline.
    Shared across ALL agents (Intake, Market Research, and future agents).

    Fields:
      - messages:        LangGraph conversation history. Uses operator.add
                         so each agent node appends to the list rather than
                         replacing it. Only light summaries go here (token safety).
      - analysis_state:  The central Pydantic AnalysisState holding all domain
                         data (company, founders, market, competitive, etc.).
                         Written to directly by the orchestrator's mapping node.
    """

    messages: Annotated[Sequence[BaseMessage], operator.add]
    analysis_state: AnalysisState