from enum import Enum

from .image import IMAGE_ANALYSIS
from .pitch_deck_prompts import (
    DECK_SHARED_SYSTEM_PROMPT, 
    PITCH_DECK_COMPETITORS_AND_DD_INSTRUCTION,
    PITCH_DECK_CORE_COMPANY_INSTRUCTION,
    PITCH_DECK_MARKET_SIZE_INSTRUCTION,
    PITCH_DECK_FOUNDERS_INSTRUCTION,
    PITCH_DECK_FINANCIALS_AND_ASK_INSTRUCTION,
    PITCH_DECK_SLIDE_SUMMARIES_INSTRUCTION,
    QUERY_PITCH_DECK_CONTENT
)
from .intak_layer import (
    INTAKE_SYSTEM_PROMPT,
    INTAKE_HUMAN_REQUEST_TEMPLATE,
    MARKET_SYSTEM_PROMPT
)

class PromptRegistry(str, Enum):
    """
    Central registry for all prompts used in the project.
    """

    image_analysis: str = IMAGE_ANALYSIS
    deck_system_prompt = DECK_SHARED_SYSTEM_PROMPT
    deck_company = PITCH_DECK_CORE_COMPANY_INSTRUCTION
    deck_market = PITCH_DECK_MARKET_SIZE_INSTRUCTION
    deck_founders = PITCH_DECK_FOUNDERS_INSTRUCTION
    deck_financials = PITCH_DECK_FINANCIALS_AND_ASK_INSTRUCTION
    deck_competitor = PITCH_DECK_COMPETITORS_AND_DD_INSTRUCTION
    deck_summary = PITCH_DECK_SLIDE_SUMMARIES_INSTRUCTION
    deck_query = QUERY_PITCH_DECK_CONTENT

    # Agent / Manager Prompts
    intake_system = INTAKE_SYSTEM_PROMPT
    intake_human = INTAKE_HUMAN_REQUEST_TEMPLATE
    market_system = MARKET_SYSTEM_PROMPT
