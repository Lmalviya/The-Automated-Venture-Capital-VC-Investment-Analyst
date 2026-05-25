from vs_analyst.utility.llm import llm
from vs_analyst.tools import (
    adversarial_search_tool,
    deep_research_tool,

    calculate_percentage,
    parse_numeric_value,
    years_since,
    get_current_date,
    count_by_competitor_type,
)

# 1. Competitor Finder Planner Agent
COMPETITOR_FINDER_PLANNER_TOOLS = [deep_research_tool]
competitor_finder_planner_agent = llm.bind_tools(COMPETITOR_FINDER_PLANNER_TOOLS)

# 2. Competitor Finder Synthesizer Agent
COMPETITOR_FINDER_SYNTHESIZER_TOOLS = []
competitor_finder_synthesizer_agent = llm.bind_tools(COMPETITOR_FINDER_SYNTHESIZER_TOOLS)

# 3. Competitor Investigator Planner Agent
COMPETITOR_INVESTIGATOR_PLANNER_TOOLS = [deep_research_tool, adversarial_search_tool]
competitor_investigator_planner_agent = llm.bind_tools(COMPETITOR_INVESTIGATOR_PLANNER_TOOLS)

# 4. Competitor Investigator Synthesizer Agent
COMPETITOR_INVESTIGATOR_SYNTHESIZER_TOOLS = [
    parse_numeric_value,
    calculate_percentage,
    count_by_competitor_type,
]
competitor_investigator_synthesizer_agent = llm.bind_tools(COMPETITOR_INVESTIGATOR_SYNTHESIZER_TOOLS)

# 5. Competitive Risk Analyst Agent
COMPETITIVE_RISK_ANALYST_TOOLS = [
    calculate_percentage,
    parse_numeric_value,
    years_since,
    get_current_date,
    count_by_competitor_type,
]
competitive_risk_analyst_agent = llm.bind_tools(COMPETITIVE_RISK_ANALYST_TOOLS)
