from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

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
    run_id: str = Field(..., description="uuid4 ")
    status: PipelineStatus = Field(defauld_factory=PipelineStatus, description="")
    agent_statuses: dict[str, AgentStatus]=None
    
    errors: List[PipelineError] = Field(default_factory=PipelineError, description="")
    created_at: datetime = Field(default_factory=datetime, description="")
    completed_at: datetime = Field(default_factory=datetime, description="")

    user_input: UserInputSchema = Field()
    company: CompanySchema = Field()
    founders: List[FounderSchema] = Field()
    market: MarketSchema = Field()
    competitive: CompetitiveSchema = Field()
    due_diligence: DueDiligenceSchema = Field()
    memo: MemoSchema = Field()
    

    class AnalysisState(BaseModel):
        # ── User input ────────────────────────────────────────
        user_input    : UserInputSchema            

        # ── Intake Manager ────────────────────────────────────
        company       : CompanySchema        
        founders      : list[FounderSchema]   

        # ── Agent outputs (None until manager runs) ───────────
        market        : Optional[MarketSchema]       = None 
        competitive   : Optional[CompetitiveSchema]   = None 
        due_diligence : Optional[DueDiligenceSchema]  = None 
        memo          : Optional[MemoSchema]         = None 