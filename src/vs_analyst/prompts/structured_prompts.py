from enum import Enum

SHARED_SYSTEM_PROMPT = """You are a world-class Venture Capital (VC) Associate and expert Investment Analyst.
Your objective is to analyze the provided pitch deck content extremely carefully and extract the requested information.
Adhere strictly to the provided JSON schema to structure your output. Do not summarize or lose granularity."""

PITCH_DECK_CORE_COMPANY_INSTRUCTION = """
Scan the pitch deck and extract the core startup identity. 
Your objective is to identify:
1. The company name and founding year.
2. The core problem statement and the product/service solution.
3. The unique value proposition.
4. The business model (B2B, B2C, B2B2C, marketplace, etc.) and primary sector/industry.
5. The geographical market coverage.
6. Current product stage (MVP, beta, GA, etc.) and employee count.

Deck content:
{TEXT}
"""

PITCH_DECK_MARKET_SIZE_INSTRUCTION = """
Scan the pitch deck and extract market size estimates and dynamics.
Your objective is to identify:
1. Market sizing values for TAM (Total Addressable Market), SAM (Serviceable Addressable Market), and SOM (Serviceable Obtainable Market). Include estimated years, source names, confidence levels, and any notes.
2. Market growth rate (CAGR or other growth indicators) and the source for that rate.
3. 3-5 macro trends shaping the market.
4. Identified market risks or regulatory hurdles.
5. Synthesis overview of the market size and opportunities.

Deck content:
{TEXT}
"""

PITCH_DECK_FOUNDERS_INSTRUCTION = """
Scan the pitch deck and extract details of all founders and key team members.
For each founder, identify:
1. Full name, role/title (e.g. CEO, CTO, COO), and LinkedIn/GitHub URLs.
2. Biography extracted from the deck.
3. List of past companies they worked at and roles held.
4. Detailed education history including university name, degree level (BS, MS, PhD), branch of study, and passing year.

Deck content:
{TEXT}
"""

PITCH_DECK_FINANCIALS_AND_ASK_INSTRUCTION = """
Scan the pitch deck and extract traction metrics and funding ask details.
Your objective is to identify:
1. Revenue details (monthly revenue or ARR).
2. Current user/customer count and growth rate (e.g., MoM growth).
3. Major notable key customers or partners.
4. Any other specific traction metrics highlighted.
5. Funding ask amount and target valuation (pre or post-money).
6. How the funds will be used (use of funds) and any prior funding rounds mentioned.
7. Any financial inconsistencies or red flags.

Deck content:
{TEXT}
"""

PITCH_DECK_COMPETITORS_AND_DD_INSTRUCTION = """
Scan the pitch deck and extract competitor details and key traction claims requiring external due diligence check.
Your objective is to identify:
1. Direct, indirect, emerging, or substitute competitors, their primary website, funding stage/amount, geography, business model, strengths, weaknesses, and unique positioning.
2. Startup's defensible moat assessment and top competitive risk factors.
3. Traction claims (exact metrics, partnerships, or claims to be verified) and any regulatory, patent, or legal notes.

Deck content:
{TEXT}
"""

PITCH_DECK_SLIDE_SUMMARIES_INSTRUCTION = """
Scan the pitch deck content and summarize each slide/page.
Your objective is to output a clear page-by-page mapping containing:
1. The slide/page number.
2. A concise summary of the key takeaway, points, or data presented on that specific slide.

Deck content:
{TEXT}
"""

class StructuredPromptRegistry(str, Enum):
    """
    Central registry for all clean prompts used in structured extraction.
    """
    system_prompt = SHARED_SYSTEM_PROMPT
    deck_company = PITCH_DECK_CORE_COMPANY_INSTRUCTION
    deck_market = PITCH_DECK_MARKET_SIZE_INSTRUCTION
    deck_founders = PITCH_DECK_FOUNDERS_INSTRUCTION
    deck_financials = PITCH_DECK_FINANCIALS_AND_ASK_INSTRUCTION
    deck_competitor = PITCH_DECK_COMPETITORS_AND_DD_INSTRUCTION
    deck_summary = PITCH_DECK_SLIDE_SUMMARIES_INSTRUCTION
