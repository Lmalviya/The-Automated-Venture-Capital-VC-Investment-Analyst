from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

from .shared_enums import ConfidenceLevel
from .shared_models import ResearchSource



class MarketSize(BaseModel):
    # ── One sized estimate (TAM, SAM, or SOM) ────────────
    value : Optional[str] = None # e.g. "$4.2B", "₹800Cr"
    year : Optional[str] = None # e.g. "2024", "2024–2028"
    source : Optional[str] = None # e.g. "Statista 2024", "Grand View Research"
    source_url : Optional[str] = None
    confidence : ConfidenceLevel = ConfidenceLevel.LOW
    notes : Optional[str] = None # LLM caveat e.g. "Adjacent market, not exact"



class MarketSchema(BaseModel):
    # ── Sized estimates ───────────────────────────────────
    tam : MarketSize = MarketSize() # Total Addressable Market
    sam : MarketSize = MarketSize() # Serviceable Addressable Market
    som : MarketSize = MarketSize() # Serviceable Obtainable Market

    # ── Market dynamics ───────────────────────────────────
    growth_rate : Optional[str] = None # e.g. "CAGR 18% through 2028"
    growth_source : Optional[str] = None # where growth_rate came from
    key_trends : list[str] = [] # 3–5 macro trends shaping the market
    market_risks : list[str] = [] # e.g. "Regulatory uncertainty in EU"

    # ── Synthesis ─────────────────────────────────────────
    summary : Optional[str] = None # 2–3 para LLM synthesis for memo
    overall_confidence : ConfidenceLevel = ConfidenceLevel.LOW
    # ↑ agent sets this based on source quality across all estimates

    # ── Audit trail (raw search data) ─────────────────────
    research_sources : list[ResearchSource] = []
    queries_used : list[str] = [] # exact search queries the agent ran