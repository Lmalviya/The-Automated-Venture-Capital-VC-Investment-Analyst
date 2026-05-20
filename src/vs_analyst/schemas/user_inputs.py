from pydantic import BaseModel, HttpUrl, field_validator, Field
from enum import Enum 
from pathlib import Path
from typing import Optional, List

class InvestmentStage(str, Enum):
    PRE_SEE = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"

class UserInputSchema(BaseModel):
    pitch_deck_path: Path = Field(..., description="Path to the pitch deck file")
    investment_stage: InvestmentStage = Field(..., description="Target investment stage")
    linkedin_urls: Optional[List[HttpUrl]] = Field(default_factory=list, description="List of LinkedIn profile URLs")
    website_url: Optional[HttpUrl] = Field(default=None, description="Company website URL")
    sector: Optional[str] = Field(default=None, description="Target industry sector") 

    github_urls: List[HttpUrl] = Field(default_factory=list, description="List of GitHub profile or repository URLs")
    geography: Optional[str] = Field(default=None, description="Target geography or region")

    @field_validator("pitch_deck_path")
    @classmethod
    def validate_deck(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError("Pitch deck file not found")
        if v.suffix.lower() not in (".pdf", ".pptx"):
            raise ValueError("File Extention must be .pdf or .pptx")
        return v
    