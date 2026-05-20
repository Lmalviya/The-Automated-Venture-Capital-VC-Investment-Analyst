from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional
from .shared_enums import ErrorType

class ResearchSource(BaseModel):
    # ── One search result snippet, stored as-is ───────────
    url : HttpUrl
    title : str
    snippet : str # hard cap: 500 chars — set in tool, not here
    fetched_at : datetime = Field(default_factory=datetime.utcnow)

class PressMention(BaseModel):
    title      : str
    url        : Optional[HttpUrl] = None
    source     : Optional[str] = None # e.g. "TechCrunch", "YourStory"
    date       : Optional[str] = None
    sentiment  : Optional[str] = None # "positive" / "neutral" / "negative"
    snippet    : Optional[str] = None # 300 char cap

class PipelineError(BaseModel):
    run_id : str
    agent_name : str
    tool_name : Optional[str] = None
    error_type : ErrorType = ErrorType.UNKNOWN
    error_message : str # short, shown in UI
    detailed_message : str # full context, for debugging
    is_fatal : bool = False # False = continue, True = stop
    timestamp : datetime = Field(default_factory=datetime.utcnow)