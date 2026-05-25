from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum 
from datetime import datetime
from .shared_enums import BusinessModel


class TractionMetric(BaseModel):
    revenue_monthly: Optional[str] = Field(default=None, description="Monthly revenue of the company")
    revenue_annual: Optional[str] = Field(default=None, description="Annual revenue of the company")

    user_count: Optional[str] = Field(default=None, description="Current number of users")
    growth_rate: Optional[str] = Field(default=None, description="User or revenue growth rate")
    key_customers: Optional[str] = Field(default=None, description="Notable key customers")
    other_metrics: List[Dict] = Field(default_factory=list, description="Any other traction metrics")
    

class FoundingInfo(BaseModel):
    ask_amount: Optional[str] = Field(default=None, description="Requested funding amount, e.g. '$2M'")
    valuation: Optional[str] = Field(default=None, description="Company valuation, e.g. '$10M pre-money'")
    use_of_funds: Optional[List[str]] = Field(default=None, description="How the funds will be used, e.g. ['Hire 3 engineers', 'Marketing']")
    prior_funding: Optional[List[str]] = Field(default=None, description="Previous funding rounds, e.g. ['Raised $500k pre-seed']")



class CompanySchema(BaseModel):
    name: str = Field(default=None, description="Name of the company")
    founding_year: int = Field(default=None, 
                               ge=1900, 
                               le=datetime.now().year, 
                               description=f"Founding year, valid year between 1900 to {datetime.now().year}"
                               )
    problem_statement: str = Field(default=None, description="The problem the company is trying to solve")
    solution: str = Field(default=None, description="The solution offered by the company")
    
    website_url: Optional[str] = Field(default=None, description="Company website URL")
    sector: Optional[str] = Field(default=None, description="Industry sector of the company")
    geography: Optional[str] = Field(default=None, description="Geographical location of the company")
    employee_count: Optional[str] = Field(default=None, description="Number of employees, e.g. '12' or '10-15'") 
    
    business_model: BusinessModel = Field(default=BusinessModel.UNKNOWN, description="The company's business model")
    value_proposition: str = Field(default=None, description="The company's unique value proposition")
    product_stage: str = Field(default=None, description="Current stage of the product, e.g. 'MVP', 'Beta', 'GA', 'Idea'")

    traction: TractionMetric = Field(default_factory=TractionMetric, description="Traction metrics")
    funding: FoundingInfo = Field(default_factory=FoundingInfo, description="Funding information")

    extracted_notes: List[str] = Field(default_factory=list, description="Any ambiguity the agent flagged")

    #  things wrong with the business itself (metric inconsistencies, suspicious claims, regulatory exposure)
    red_flags : list[str] = Field(default_factory=list, description="list of claim which are wrong or contradict") 