import uuid
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
from typing import List, Optional
from datetime import datetime
from .shared_enums import DDStatus

class FounderRole(str, Enum):
    CEO = "ceo"
    CTO = "cto"
    COO = "coo"
    CPO = "cpo"
    OTHER = "other" # co-founder with no named C-role
    UNKNOWN = "unknown"


class Education(BaseModel):
    collage: str = Field(..., description="College or university name")
    level: str = Field(..., description="Education level, e.g. undergraduate, PG, PhD, post-doctoral")
    branch: str = Field(..., description="Field of study or branch, e.g. computer science")
    passing_year: Optional[int] = Field(default=None, ge=1900, le=datetime.now().year, description="Graduation year")


class FounderSchema(BaseModel):
    founder_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Full name of the founder")
    role: FounderRole = Field(default=FounderRole.UNKNOWN, description="Role of the founder, possible values are CEO, CTO, COO, other")
    linkedin_url: Optional[HttpUrl] = Field(default=None, description="LinkedIn profile URL")

    bio_from_deck: Optional[str] = Field(default=None, description="Founder biography extracted from the pitch deck")
    past_companies: List[str] = Field(default_factory=list, description="List of past companies the founder worked at")
    past_roles: List[str] = Field(default_factory=list, description="List of past roles held by the founder")
    education: Optional[List[Education]] = Field(default=None, description="Educational background of the founder")
    linkedin_summary: Optional[str] = Field(default=None, description="LinkedIn profile summary scraped via agent")
    verified_background: Optional[str] = Field(default=None, description="Verified background details")
    notable_achievements: Optional[List[str]] = Field(default=None, description="Notable achievements of the founder")
    
    # things wrong with a specific individual (employment gap, false claim about past role, undisclosed conflict)
    red_flags: Optional[List[str]] = Field(default=None, description="Identified inconsistencies, gaps, or concerns")

    # ── Personal GitHub signals (DD Manager) ──────────
    github_url          : Optional[HttpUrl] = None
    github_public_repos : Optional[int] = None
    github_languages    : list[str] = []     # ["Python", "Go"]
    github_oss_notable  : list[str] = []     # notable OSS projects/contributions
    github_account_age  : Optional[str] = None # e.g. "8 years"
    github_active       : Optional[bool] = None # commits in last 6 months