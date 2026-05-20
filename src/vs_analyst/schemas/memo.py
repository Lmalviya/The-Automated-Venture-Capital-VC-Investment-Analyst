from typing import Optional
from enum import Enum
from pydantic import BaseModel

from .shared_enums import AgentStatus


class RecommendationVerdict(str, Enum):
    INVEST = "invest"
    WATCH = "watch"
    PASS = "pass"

class RecommendationSchema(BaseModel):
    # ── Signal ────────────────────────────────────────────
    verdict           : RecommendationVerdict

    # ── Reasoning (required regardless of verdict) ────────
    investment_thesis : str                 # why this could work
    key_risks         : list[str]           # top 3–5 concerns
    key_strengths     : list[str]           # top 3–5 positives


    # ── Conditions & next steps ───────────────────────────
    conditions        : list[str] = []       # must be met before proceeding
    # INVEST: ["Complete legal DD", "Confirm cap table"]
    # WATCH: ["Re-engage at $50k MRR", "Hire domain expert"]
    # PASS: [] — conditions rarely apply to a pass

    next_steps        : list[str] = []       # concrete actions for the analyst
    # e.g. ["Schedule founder call", "Request data room access"]

    # ── Fit context ───────────────────────────────────────
    fund_fit_note     : Optional[str] = None # how it aligns with fund thesis
    # e.g. "Aligns with B2B SaaS focus, India market thesis"

class MemoSection(BaseModel):
    # ── One written section of the memo ───────────────────

    title      : str                       # e.g. "Market Analysis"
    content    : str                       # full markdown text
    order      : int                       # render order in final doc
    word_count : Optional[int] = None
    status     : AgentStatus = AgentStatus.PENDING # per-section write status



class MemoCaveat(BaseModel):
    # ── One surfaced limitation in the memo footer ────────
    source     : str                       # e.g. "due_diligence_manager"
    message    : str                       # human-readable caveat
    # e.g. "LinkedIn data unavailable for founder John Doe.
    # Background assessment based on deck claims only."


class MemoSchema(BaseModel):
        # ── Sections (named fields, not dict) ─────────────────
        executive_summary    : Optional[MemoSection] = None
        company_overview     : Optional[MemoSection] = None
        market_analysis      : Optional[MemoSection] = None
        competitive_landscape : Optional[MemoSection] = None
        team_assessment      : Optional[MemoSection] = None
        due_diligence_notes  : Optional[MemoSection] = None
        risk_factors         : Optional[MemoSection] = None
        recommendation       : Optional[RecommendationSchema] = None

        # ── Assembled output ──────────────────────────────────
        full_markdown        : Optional[str] = None # all sections joined
        pdf_path             : Optional[str] = None # outputs/{run_id}/memo.pdf

        # ── Caveats (separate list, rendered as footer) ───────
        caveats              : list[MemoCaveat] = []
        # populated from state.errors where is_fatal=False
        # always appended as last section of the PDF