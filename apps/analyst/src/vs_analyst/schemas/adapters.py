from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Union, Literal

from vs_analyst.schemas.shared_enums import BusinessModel, ConfidenceLevel
from vs_analyst.schemas.market import MarketSize
from vs_analyst.schemas.founder import FounderRole, FounderSchema
from vs_analyst.schemas.competitive import CompetitorType, CompetitiveSchema
from vs_analyst.schemas.due_diligence import DueDiligenceSchema


# --- Company Information ---
class CompanyAdaptor(BaseModel):
    name: str = Field(default=None, description="Name of the company")
    founding_year: int = Field(default=None, 
                               ge=1900, 
                               le=datetime.now().year, 
                               description=f"Founding year, valid year between 1900 to {datetime.now().year}"
                               )
    problem_statement: str = Field(default=None, description="The problem the company is trying to solve")
    solution: str = Field(default=None, description="The solution offered by the company")
    website_url: Optional[HttpUrl] = Field(default=None, description="Company website URL")
    sector: Optional[str] = Field(default=None, description="Industry sector of the company")
    geography: Optional[str] = Field(default=None, description="Geographical location of the company")
    employee_count: Optional[str] = Field(default=None, description="Number of employees, e.g. '12' or '10-15'")
    business_model: BusinessModel = Field(default=BusinessModel.UNKNOWN, description="The company's business model")
    value_proposition: str = Field(default=None, description="The company's unique value proposition")
    product_stage: str = Field(default=None, description="Current stage of the product, e.g. 'MVP', 'Beta', 'GA', 'Idea'")


# --- Market Information ---
class MarketAdaptor(BaseModel):
    # ── Sized estimates ───────────────────────────────────
    tam : MarketSize = MarketSize() # Total Addressable Market
    sam : MarketSize = MarketSize() # Serviceable Addressable Market
    som : MarketSize = MarketSize() # Serviceable Obtainable Market

    # ── Market dynamics ───────────────────────────────────
    growth_rate : Optional[str] = None # e.g. "CAGR 18% through 2028"
    growth_source : Optional[str] = None # where growth_rate came from
    key_trends : list[str] = [] # 3–5 macro trends shaping the market
    market_risks : list[str] = [] # e.g. "Regulatory uncertainty in EU"


# --- Founders Information ---
class FounderAdaptor(BaseModel):
    name: str = Field(..., description="Full name of the founder")
    role: FounderRole = Field(default=FounderRole.UNKNOWN, description="Role of the founder, possible values are CEO, CTO, COO, other")
    linkedin_url: Optional[HttpUrl] = Field(default=None, description="LinkedIn profile URL")

    bio_from_deck: Optional[str] = Field(default=None, description="Founder biography extracted from the pitch deck")
    past_companies: List[str] = Field(default_factory=list, description="List of past companies the founder worked at")
    past_roles: List[str] = Field(default_factory=list, description="List of past roles held by the founder")
    collage: str = Field(..., description="College or university name")
    level: str = Field(..., description="Education level, e.g. undergraduate, PG, PhD, post-doctoral")
    branch: str = Field(..., description="Field of study or branch, e.g. computer science")
    passing_year: Optional[int] = Field(default=None, ge=1900, le=datetime.now().year, description="Graduation year")
    notable_achievements: Optional[List[str]] = Field(default=None, description="Notable achievements of the founder")
    

# --- Finance Information ---
class FinanceAdaptor(BaseModel):
    ask_amount: Optional[str] = Field(default=None, description="Requested funding amount, e.g. '$2M'")
    valuation: Optional[str] = Field(default=None, description="Company valuation, e.g. '$10M pre-money'")
    use_of_funds: Optional[List[str]] = Field(default=None, description="How the funds will be used, e.g. ['Hire 3 engineers', 'Marketing']")
    prior_funding: Optional[List[str]] = Field(default=None, description="Previous funding rounds, e.g. ['Raised $500k pre-seed']")

    revenue_monthly: Optional[str] = Field(default=None, description="Monthly revenue of the company")
    revenue_annual: Optional[str] = Field(default=None, description="Annual revenue of the company")

    user_count: Optional[str] = Field(default=None, description="Current number of users")
    growth_rate: Optional[str] = Field(default=None, description="User or revenue growth rate")
    key_customers: Optional[str] = Field(default=None, description="Notable key customers")
    other_metrics: List[Dict] = Field(default_factory=list, description="Any other traction metrics")
    

# --- Competitor Information ---
class CompetitorSchemaAdaptor(BaseModel):
    name : str
    website_url : Optional[HttpUrl] = None
    competitor_type : CompetitorType = CompetitorType.DIRECT

class CompetitorAdaptor(BaseModel):
    competitors : list[CompetitorSchemaAdaptor] = []

    
# --- Each page summary ---
class OverviewAdaptor(BaseModel):
    page_number: int = Field(
        ...,
        ge=1,
        description="Slide or page number starting from 1",
    )
    section_type: str = Field(
        ...,
        description=(
            "Primary section/category of the page such as "
            "'company_overview', 'problem', 'solution', "
            "'market', 'traction', 'financials', "
            "'competitors', 'founders', 'product', "
            "'roadmap', 'fundraising'"
        ),
    )
    title: Optional[str] = Field(
        default=None,
        description="Extracted or inferred page title/headline",
    )
    summary: str = Field(
        ...,
        description="Concise but information-rich summary of the page",
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="Important insights, claims, metrics, or highlights from the page",
    )

class SearchQueryGoal(BaseModel):
    query: str = Field(..., description="A highly specific, search-engine-optimized query targeting a distinct aspect of the market")
    goal: str = Field(..., description="The guiding perspective or requirement for the crawler and internal synthesizer")
    rationale: str = Field(..., description="Rationale for this query based on gaps in current state")

class MarketPlannerDecision(BaseModel):
    status: Literal["COMPLETE", "INCOMPLETE"] = Field(..., description="Status of the planning phase")
    queries: List[SearchQueryGoal] = Field(default_factory=list, description="List of exactly 3 distinct queries with goals if status is INCOMPLETE")

class MarketSynthesizerAdaptor(BaseModel):
    tam: MarketSize = Field(default_factory=MarketSize, description="Verified Total Addressable Market sizing")
    sam: MarketSize = Field(default_factory=MarketSize, description="Verified Serviceable Addressable Market")
    som: MarketSize = Field(default_factory=MarketSize, description="Verified Serviceable Obtainable Market")
    growth_rate: Optional[str] = Field(default=None, description="Synthesized growth rate")
    growth_source: Optional[str] = Field(default=None, description="Source reference verifying the CAGR")
    key_trends: List[str] = Field(default_factory=list, description="3-5 synthesized macro industry trends backed by independent sources")
    summary: Optional[str] = Field(default=None, description="A detailed 2-3 paragraph narrative summarizing the market landscaping")
    overall_confidence: ConfidenceLevel = Field(default=ConfidenceLevel.LOW, description="A synthesized confidence score representing source quality and consensus")

class MarketRiskAdaptor(BaseModel):
    market_risks: List[str] = Field(default_factory=list, description="A list of 3-5 detailed, specific risk descriptions")

class CompetitorPlannerDecision(BaseModel):
    status: Literal["COMPLETE", "INCOMPLETE"] = Field(..., description="Whether discovery is complete or not")
    queries: List[SearchQueryGoal] = Field(default_factory=list, description="List of 2-3 target search queries")

class CompetitorDiscoveryEntry(BaseModel):
    name: str = Field(..., description="Competitor name")
    website_url: Optional[HttpUrl] = Field(default=None, description="Competitor website URL")
    competitor_type: CompetitorType = Field(default=CompetitorType.DIRECT, description="Competitor classification")
    rationale: str = Field(..., description="One-sentence rationale for type and selection")

class CompetitorDiscoveryResult(BaseModel):
    qualified_competitors: List[CompetitorDiscoveryEntry] = Field(default_factory=list, description="Deduplicated and classified competitors")
    custom_dimension_keys: List[str] = Field(default_factory=list, description="2-3 sector-specific custom dimension keys")

class InvestigatorQueryGoal(BaseModel):
    query: str = Field(..., description="Target search query")
    goal: str = Field(..., description="Crawler goal/instructions")
    tool_mode: Literal["positive", "adversarial"] = Field(..., description="Search tool to use (web_search_tool vs adversarial_search_tool)")

class CompetitorInvestigatorDecision(BaseModel):
    status: Literal["COMPLETE", "INCOMPLETE"] = Field(..., description="Whether profiling is complete or not")
    queries: List[InvestigatorQueryGoal] = Field(default_factory=list, description="List of 1-2 positive or adversarial search tasks")

class CompetitiveRiskAdaptor(BaseModel):
    competitive_risk: str = Field(..., description="Top competitive threats detailed narrative")
    top_risks: List[str] = Field(default_factory=list, description="3-5 structured risk statements")
    risk_severity: Literal["CRITICAL", "HIGH", "MODERATE", "LOW"] = Field(..., description="Overall competitive risk rating")

AdaptorType = Union[
    CompanyAdaptor,
    MarketAdaptor,
    FounderAdaptor,
    FinanceAdaptor,
    CompetitorAdaptor,
    OverviewAdaptor,
    SearchQueryGoal,
    MarketPlannerDecision,
    MarketSynthesizerAdaptor,
    MarketRiskAdaptor,
    CompetitorPlannerDecision,
    CompetitorDiscoveryEntry,
    CompetitorDiscoveryResult,
    InvestigatorQueryGoal,
    CompetitorInvestigatorDecision,
    CompetitiveRiskAdaptor,
]