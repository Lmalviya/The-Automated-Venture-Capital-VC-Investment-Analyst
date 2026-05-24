from vs_analyst.utility.llm import llm
from vs_analyst.tools.market_tools import web_search_tool, market_synthesizer_tool

# List of tools assigned to the Market Research Agent
MARKET_TOOLS = [
    web_search_tool,
]

# Configured LLM runner with bound tools
market_agent = llm.bind_tools(MARKET_TOOLS)
