from typing import Optional, Dict, List, Literal
from enum import Enum
from pydantic import BaseModel, Field

from .shared_enums import AgentStatus


class RecommendationVerdict(str, Enum):
    INVEST = "invest"
    WATCH  = "watch"
    PASS   = "pass"


# ── Advisory Debate Output Models ─────────────────────────────────────────────

class InvestmentBrief(BaseModel):
    """
    Output of investment_advocate or investment_adversary nodes.
    Each agent argues from a fixed, biased persona to prevent bland middle-ground analysis.
    """
    stance              : Literal["INVEST", "PASS"]
    thesis              : str               # 2–3 paragraph argument
    supporting_evidence : List[str]         # 4–6 state-sourced evidence points


class StrategicDirective(BaseModel):
    """
    Output of growth_strategist (DO) or hazard_mitigator (STOP) nodes.
    Each action item must include an in-line rationale traceable to state data.
    """
    directive_type : Literal["DO", "STOP"]
    actions        : List[str]              # 3–5 concrete action items with rationale


# ── Venture Partner IC Output ─────────────────────────────────────────────────

class InvestmentRecommendation(BaseModel):
    """
    Final verdict produced by the venture_partner_ic_agent after weighing
    the Advocate brief, Adversary brief, and strategic directives.
    Written to AnalysisState.memo.recommendation.
    """
    verdict           : RecommendationVerdict
    conviction_score  : int = Field(..., ge=1, le=10, description="Overall conviction level 1 (low) to 10 (high)")

    # ── Reasoning ──────────────────────────────────────────
    investment_thesis : str               # 3-paragraph balanced synthesis
    key_strengths     : List[str]         # top 4 positive signals
    key_risks         : List[str]         # top 4 risk factors

    # ── Strategic Actions ──────────────────────────────────
    do_list           : List[str] = []    # from growth_strategist
    stop_list         : List[str] = []    # from hazard_mitigator

    # ── Conditions & next steps ────────────────────────────
    conditions        : List[str] = []    # pre-investment checklist
    # INVEST: ["Complete legal DD", "Confirm cap table"]
    # WATCH:  ["Re-engage at $50k MRR", "Hire domain expert"]
    next_steps        : List[str] = []    # concrete actions for the analyst

    # ── Fit context ────────────────────────────────────────
    fund_fit_note     : Optional[str] = None
    # e.g. "Aligns with B2B SaaS focus, India market thesis"


# ── LLM-as-Judge Review Models ────────────────────────────────────────────────

class SectionCritique(BaseModel):
    """
    A targeted correction instruction for one memo section.
    Produced by memo_reviewer when a factual discrepancy or omission is found.
    """
    section_name           : str   # e.g. "market_analysis"
    issue                  : str   # specific factual discrepancy or omission
    correction_instruction : str   # actionable re-write instruction for the writer agent


class ReviewDecision(BaseModel):
    """
    Output of the memo_reviewer (LLM-as-a-Judge) node.
    Routes execution back to the section writers with targeted critiques if rejected.
    """
    status   : Literal["APPROVED", "REJECTED"]
    critiques: List[SectionCritique] = []  # empty when APPROVED


# ── Memo Document Models ───────────────────────────────────────────────────────

class MemoSection(BaseModel):
    """One written section of the investment memo."""
    title      : str                       # e.g. "Market Analysis"
    content    : str                       # full markdown text
    order      : int                       # render order in final doc
    word_count : Optional[int] = None
    status     : AgentStatus = AgentStatus.PENDING


class MemoCaveat(BaseModel):
    """
    A surfaced limitation rendered in the memo footer.
    Populated from state.errors where is_fatal=False, or from state_assembler
    when an upstream namespace is empty or incomplete.
    """
    source  : str   # e.g. "due_diligence_manager"
    message : str   # e.g. "LinkedIn data unavailable for founder John Doe."


class MemoSchema(BaseModel):
    # ── Factual Sections (written by section writers) ──────
    executive_summary     : Optional[MemoSection] = None
    company_overview      : Optional[MemoSection] = None
    market_analysis       : Optional[MemoSection] = None
    competitive_landscape : Optional[MemoSection] = None
    team_assessment       : Optional[MemoSection] = None
    due_diligence_notes   : Optional[MemoSection] = None

    # ── Advisory Recommendation (written by venture_partner_ic_agent) ──
    recommendation        : Optional[InvestmentRecommendation] = None

    # ── Visual Diagrams (SVG strings, written by vector_diagram_generator) ──
    diagrams              : Dict[str, str] = {}
    # Keys: "competitive_quadrant", "traction_sparkline", "moat_radar"

    # ── Assembled Outputs ──────────────────────────────────
    full_markdown         : Optional[str] = None  # all sections joined
    html_pdf_path         : Optional[str] = None  # outputs/{run_id}/memo_web.pdf   (Pattern A)
    typst_pdf_path        : Optional[str] = None  # outputs/{run_id}/memo_typst.pdf (Pattern B)

    # ── Reviewer State (transient — cleared after compile) ─
    review_decision       : Optional[ReviewDecision] = None
    review_attempts       : int = 0

    # ── Caveats (rendered as memo footer) ─────────────────
    caveats               : List[MemoCaveat] = []