# advisory.py
from vs_analyst.utility.llm import llm
from vs_analyst.tools.cognitive_utils import calculate_percentage
from vs_analyst.schemas.memo import (
    InvestmentBrief,
    StrategicDirective,
    InvestmentRecommendation,
    ReviewDecision,
)

# 1. Advisory debate agents (pure cognitive, no tools)
investment_advocate_agent = llm.with_structured_output(InvestmentBrief)
investment_adversary_agent = llm.with_structured_output(InvestmentBrief)
growth_strategist_agent = llm.with_structured_output(StrategicDirective)
hazard_mitigator_agent = llm.with_structured_output(StrategicDirective)

# 2. Venture Partner IC Chairperson (bound to calculate_percentage tool)
venture_partner_ic_agent = llm.bind_tools([calculate_percentage]).with_structured_output(InvestmentRecommendation)

# 3. Lead Memo Reviewer LLM-as-a-Judge (pure cognitive, no tools)
memo_reviewer_agent = llm.with_structured_output(ReviewDecision)
