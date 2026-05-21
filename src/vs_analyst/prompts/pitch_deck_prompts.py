DECK_SHARED_SYSTEM_PROMPT = """You are a world-class Venture Capital (VC) Associate and expert Investment Analyst.
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
    6. Current product stage (MVP, beta, GA, etc.).

    Output Formate:
    ```json
    {{
        "name": "<string | official company or startup name>",
        "founding_year": "<integer | company founding year between 1900 and 2026>",
        "problem_statement": "<string | core business problem, inefficiency, or customer pain point the company is solving>",
        "solution": "<string | description of the company's product, platform, technology, or service solution>",
        "website_url": "<string | official company website URL if available>",
        "sector": "<string | primary industry or sector such as AI, FinTech, HealthTech, SaaS, Cybersecurity, ClimateTech, LegalTech>",
        "geography": "<string | primary operating market or target geography such as India, US, Europe, Southeast Asia, Global>",
        "employee_count": "<string | estimated company team size such as '12', '10-15', '50+', or 'Not disclosed'>",
        "business_model": "<string | one of: b2b, b2c, b2b2c, marketplace, unknown>",
        "value_proposition": "<string | unique differentiator, competitive advantage, or key value proposition that makes the company stand out>",
        "product_stage": "<string | current company or product maturity stage such as Idea, Prototype, MVP, Beta, Early Revenue, Growth, Scale>"
    }}
    ```

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

    Output Formate:
    ```json
        {{
            "tam": {{
                "value": "<string | Total Addressable Market size such as '$10B' or '₹5000Cr'>",
                "year": "<string | year or forecast period for TAM such as '2024' or '2024-2030'>",
                "source": "<string | source of TAM estimate such as 'Statista 2024', 'McKinsey', 'Grand View Research'>",
                "source_url": "<string | URL of the market research source if available>",
                "confidence": "<string | one of: high, medium, low>",
                "notes": "<string | caveats, assumptions, or limitations in TAM estimation>"
            }},
            "sam": {{
                "value": "<string | Serviceable Addressable Market size relevant to the startup's target segment>",
                "year": "<string | year or forecast period for SAM>",
                "source": "<string | source used for SAM estimation>",
                "source_url": "<string | source URL if available>",
                "confidence": "<string | one of: high, medium, low>",
                "notes": "<string | notes or assumptions about SAM>"
            }},
            "som": {{
                "value": "<string | Serviceable Obtainable Market realistically capturable by the startup>",
                "year": "<string | year or forecast period for SOM>",
                "source": "<string | source or estimation basis for SOM>",
                "source_url": "<string | source URL if available>",
                "confidence": "<string | one of: high, medium, low>",
                "notes": "<string | assumptions or reasoning behind SOM estimate>"
            }},
            "growth_rate": "<string | market growth metric such as 'CAGR 18% through 2028'>",
            "growth_source": "<string | source of the growth rate data>",
            "key_trends": [
                "<string | important market or industry trend affecting the company>",
                "<string | macro trend, technology shift, regulatory change, or consumer behavior trend>"
            ],
            "market_risks": [
                "<string | market, competitive, regulatory, or operational risk>",
                "<string | example: 'Regulatory uncertainty in EU AI laws'>"
            ]
        }}
    ```

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

    Output Formate:
    ```json
    {{
        "name": "<string | full name of the founder or executive>",
        "role": "<string | one of: ceo, cto, coo, cpo, other, unknown>",
        "linkedin_url": "<string | LinkedIn profile URL if available>",
        "bio_from_deck": "<string | founder biography or background extracted from the pitch deck>",
        "past_companies": [
            "<string | previous company or organization where the founder worked>"
        ],
        "past_roles": [
            "<string | previous job title or role held by the founder>"
        ],
        "collage": "<string | college or university attended by the founder>",
        "level": "<string | highest education level such as undergraduate, postgraduate, MBA, PhD, post-doctoral>",
        "branch": "<string | field of study or academic specialization such as computer science, finance, biotechnology>",
        "passing_year": "<integer | graduation or completion year between 1900 and 2026>",
        "notable_achievements": [
            "<string | major achievement, award, patent, startup exit, publication, leadership accomplishment, or recognition>"
        ]
    }}
    ```
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
    5. How the funds will be used (use of funds) and any prior funding rounds mentioned.
    

    Output Formate:
    ```json
    {{
        "ask_amount": "<string | current fundraising ask amount such as '$2M seed' or '₹5Cr Series A'>",
        "valuation": "<string | company valuation such as '$10M pre-money', '$25M post-money'>",
        "use_of_funds": [
            "<string | planned use of raised capital such as hiring, product development, sales, marketing, expansion>"
        ],
        "prior_funding": [
            "<string | previous funding rounds or capital raised such as 'Raised $500k pre-seed from angels'>"
        ],
        "revenue_monthly": "<string | current monthly recurring revenue (MRR) or monthly revenue such as '$50k MRR'>",
        "revenue_annual": "<string | annual recurring revenue (ARR) or yearly revenue such as '$1.2M ARR'>",
        "user_count": "<string | total customers, users, subscribers, or active accounts such as '25k MAU', '120 enterprise clients'>",
        "growth_rate": "<string | business growth metric such as '15% MoM revenue growth', '3x YoY growth'>",
        "key_customers": "<string | notable customers, enterprise clients, brands, or partnerships>",
        "other_metrics": [
            {{
                "metric_name": "<string | name of traction or KPI metric>",
                "metric_value": "<string | value of the metric>",
                "notes": "<string | optional explanation or context>"
            }}
        ]
    }}

    ```
    Deck content:
    {TEXT}
"""


PITCH_DECK_COMPETITORS_AND_DD_INSTRUCTION = """
    Scan the pitch deck and extract competitor details and key traction claims requiring external due diligence check.
    Your objective is to identify:
    1. Direct, indirect, emerging, or substitute competitors, their primary website.

    Output Formate:
    ```json
    {{
        "competitors": [
            {{
                "name": "<string | competitor company or product name>",
                "website_url": "<string | official competitor website URL if available>",
                "competitor_type": "<string | one of: direct, indirect, emerging, substitute>",
                "notes": "<string | optional explanation of why this company is considered a competitor>"
            }}
        ]
    }}
    ```
    Deck content:
    {TEXT}
"""

PITCH_DECK_SLIDE_SUMMARIES_INSTRUCTION = """
    Scan the pitch deck content and summarize each slide/page.
    Your objective is to output a clear page-by-page mapping containing:
    1. The slide/page number.
    2. A concise summary of the key takeaway, points, or data presented on that specific slide.

    Output Formate:
    ```json
    {{
        "doc": [
            {{
                "page_number": "<integer | slide or page number starting from 1>",
                "section_type": "<string | primary category of the page such as company_overview, problem, solution, market, traction, financials, competitors, founders, product, roadmap, fundraising>",
                "title": "<string | inferred or extracted title/headline of the page>",
                "summary": "<string | concise but information-dense summary of the page content>",
                "key_points": [
                    "<string | important insight, metric, claim, or statement from the page>",
                    "<string | another major point extracted from the page>"
                ]    
            }}
        ]
    }}
    ```
    Deck content:
    {TEXT}
"""