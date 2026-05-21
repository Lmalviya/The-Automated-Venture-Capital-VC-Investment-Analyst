from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Union

from vs_analyst.schemas.shared_enums import BusinessModel
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

AdaptorType = Union[
    CompanyAdaptor,
    MarketAdaptor,
    FounderAdaptor,
    FinanceAdaptor,
    CompetitorAdaptor,
    OverviewAdaptor,
]