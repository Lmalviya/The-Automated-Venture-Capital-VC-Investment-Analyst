from vs_analyst.utility.llm import llm
from vs_analyst.tools.market_tools import web_search_tool
from vs_analyst.tools.cognitive_utils import (
    calculate_percentage,
    parse_numeric_value,
    get_current_date,
)

# 1. Market Planner Agent & Tools
MARKET_PLANNER_TOOLS = [web_search_tool]
market_planner_agent = llm.bind_tools(MARKET_PLANNER_TOOLS)

# 2. Market Synthesizer Agent & Tools
MARKET_SYNTHESIZER_TOOLS = [calculate_percentage, parse_numeric_value]
market_synthesizer_agent = llm.bind_tools(MARKET_SYNTHESIZER_TOOLS)

# 3. Market Risk Analyst Agent & Tools
MARKET_RISK_TOOLS = [calculate_percentage, parse_numeric_value, get_current_date]
market_risk_analyst_agent = llm.bind_tools(MARKET_RISK_TOOLS)
