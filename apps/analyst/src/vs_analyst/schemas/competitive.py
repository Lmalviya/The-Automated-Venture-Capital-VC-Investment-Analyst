from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
import uuid
from typing import Optional
from .market import ResearchSource


class CompetitorType(str, Enum):
    DIRECT = "direct" # same problem, same solution
    INDIRECT = "indirect" # same problem, different solution
    EMERGING = "emerging" # early player, watch list
    SUBSTITUTE = "substitute" # e.g. spreadsheets replacing a SaaS


class CompetitorSchema(BaseModel):
    # ── Entity ID ─────────────────────────────────────────
    competitor_id : str = Field(default_factory=lambda: str(uuid.uuid4()))

    # ── Identity ──────────────────────────────────────────
    name : str
    website_url : Optional[HttpUrl] = None
    competitor_type : CompetitorType = CompetitorType.DIRECT

    # ── Fixed dimensions (universal — always compared) ────
    funding_stage : Optional[str] = None # e.g. "Series B", "Bootstrapped"
    funding_amount : Optional[str] = None # e.g. "$24M raised"
    geography : Optional[str] = None # primary market
    business_model : Optional[str] = None # e.g. "B2B SaaS, per-seat"
    founding_year : Optional[str] = None
    key_strengths : list[str] = [] # what they do well
    key_weaknesses : list[str] = [] # known gaps or complaints
    positioning : Optional[str] = None # one-line: how they describe themselves


    # ── Flexible dimensions (sector-specific, agent decides)
    custom_dimensions : dict[str, str] = {}
    # Fintech: {"regulatory_licenses": "RBI NBFC", "api_integrations": "50+"}
    # SaaS HR: {"ats_features": "basic", "hris_integration": "SAP, Workday"}
    # Marketplace: {"supply_side": "12k vendors", "demand_gmv": "$2M/mo"}

    # ── Source tracking ───────────────────────────────────
    sources : list[ResearchSource] = [] # reused from shared_models
    profiling_notes : list[str] = [] # agent ambiguities
    queries_used : list[str] = [] # search queries used for this competitor


class CompetitiveSchema(BaseModel):
    # ── Competitor list ───────────────────────────────────

    competitors : list[CompetitorSchema] = []

    # ── Matrix metadata ───────────────────────────────────
    fixed_dimensions : list[str] = [ # always present in memo table
        "funding_stage", "funding_amount",
        "geography", "business_model",
        "founding_year", "positioning"
        ]

    custom_dimension_keys : list[str] = [] # agent registers keys it used
    # ↑ e.g. ["regulatory_licenses", "api_integrations"]
    # Memo Writer reads this to build consistent table columns

    # ── Analysis ──────────────────────────────────────────
    moat_assessment : Optional[str] = None # startup's defensible advantage
    competitive_risk : Optional[str] = None # biggest competitive threat
    summary : Optional[str] = None # 2–3 para for memo

    # ── Audit trail ───────────────────────────────────────
    research_sources : list[ResearchSource] = [] # all sources used
    queries_used : list[str] = [] # search queries ran

