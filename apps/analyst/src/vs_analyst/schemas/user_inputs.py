from pydantic import BaseModel, HttpUrl, field_validator, Field
from enum import Enum 
from pathlib import Path
from typing import Optional, List

class InvestmentStage(str, Enum):
    PRE_SEE = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"

    @classmethod
    def from_str(cls, stage_str: Optional[str]) -> Optional["InvestmentStage"]:
        """
        Resolves an optional funding stage string to an InvestmentStage enum member.
        If stage_str is None or empty/whitespace, returns None.
        If it's provided but unrecognized, raises a ValueError with clean allowed options.
        """
        if not stage_str or not stage_str.strip():
            return None

        # Clean and normalize the string
        normalized = stage_str.strip().lower().replace(" ", "_").replace("-", "_")

        # 1. Match against enum values
        for member in cls:
            if member.value == normalized:
                return member

        # 2. Match against enum keys (uppercase)
        key_normalized = normalized.upper()

        # Special alias handling for PRE_SEED -> PRE_SEE
        if key_normalized == "PRE_SEED":
            key_normalized = "PRE_SEE"

        try:
            return cls[key_normalized]
        except KeyError:
            valid_values = ", ".join(f"'{m.value}'" for m in cls)
            valid_keys = ", ".join(f"'{m.name}'" for m in cls)
            raise ValueError(
                f"Unrecognized investment stage '{stage_str}'. "
                f"Allowed stages are: {valid_values} (or keys like {valid_keys})."
            )

class UserInputSchema(BaseModel):
    pitch_deck_path: Path = Field(..., description="Path to the pitch deck file")
    investment_stage: Optional[InvestmentStage] = Field(default=None, description="Target investment stage")
    linkedin_urls: Optional[List[HttpUrl]] = Field(default_factory=list, description="List of LinkedIn profile URLs")
    website_url: Optional[HttpUrl] = Field(default=None, description="Company website URL")
    sector: Optional[str] = Field(default=None, description="Target industry sector") 
    ask_amount: Optional[float] = Field(default=None, description="Amount seeking")
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
    