from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
from typing import Optional

from .shared_enums import DDStatus
from .shared_models import ResearchSource,PressMention

class OrgGithubSignals(BaseModel):
    # ── Company / org-level GitHub data ───────────────────
    org_url           : Optional[HttpUrl] = None
    total_repos       : Optional[int] = None
    primary_language  : Optional[str] = None
    stars_primary_repo : Optional[int] = None
    contributor_count : Optional[int] = None
    commits_last_90d  : Optional[int] = None
    open_issues       : Optional[int] = None
    closed_issues     : Optional[int] = None
    last_commit_date  : Optional[str] = None
    license_type      : Optional[str] = None # e.g. "MIT", "Apache 2.0", "None"
    fetch_status      : DDStatus = DDStatus.PENDING
    fetch_notes       : list[str] = [] # e.g. "Private org, limited data"


class TractionVerification(BaseModel):
    # ── Cross-checks deck claims against external evidence ─
    claim         : str                    # exact claim from deck
    verified      : Optional[bool] = None   # True/False/None (couldn't check)
    evidence      : Optional[str] = None    # what was found to support/refute
    source_url    : Optional[HttpUrl] = None


class DueDiligenceSchema(BaseModel):
    # ── GitHub (org-level) ────────────────────────────────

    github            : OrgGithubSignals = OrgGithubSignals()

    # ── Press & media ─────────────────────────────────────
    press_mentions    : list[PressMention] = []
    press_summary     : Optional[str] = None # LLM synthesis of press coverage

    # ── Traction cross-checks ─────────────────────────────
    traction_checks   : list[TractionVerification] = []
    # e.g. deck says "500 customers" → agent searches for corroboration


    # ── Legal & regulatory signals ────────────────────────
    regulatory_flags  : list[str] = [] # known compliance concerns
    patent_mentions   : list[str] = [] # found patents or IP filings
    legal_notes       : list[str] = [] # lawsuits, disputes found in search

    # ── Company-level red flags ───────────────────────────
    red_flags         : list[str] = [] # DD-discovered, not deck-level
    # distinct from company.red_flags (those are deck inconsistencies)
    # these are externally discovered concerns

    # ── Summary ───────────────────────────────────────────
    summary           : Optional[str] = None # 2–3 para, Memo Writer reads this

    # ── Audit trail ───────────────────────────────────────
    research_sources  : list[ResearchSource] = []
    queries_used      : list[str] = []