from vs_analyst.utility.llm import llm
from vs_analyst.tools import (
    deep_research_tool,
    calculate_percentage,
    parse_numeric_value,
    get_current_date,
    parse_numeric_value,
    years_since
)


# 1. Market Planner Agent & Tools
MARKET_PLANNER_TOOLS = [deep_research_tool]
market_planner_agent = llm.bind_tools(MARKET_PLANNER_TOOLS)

# 2. Market Synthesizer Agent & Tools
MARKET_SYNTHESIZER_TOOLS = [calculate_percentage, parse_numeric_value, years_since, get_current_date]
market_synthesizer_agent = llm.bind_tools(MARKET_SYNTHESIZER_TOOLS)

# 3. Market Risk Analyst Agent & Tools
MARKET_RISK_TOOLS = [calculate_percentage, parse_numeric_value, get_current_date, years_since]
market_risk_analyst_agent = llm.bind_tools(MARKET_RISK_TOOLS)
