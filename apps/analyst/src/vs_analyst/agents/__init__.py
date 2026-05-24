from .intake import intake_agent, INTAKE_TOOLS
from .market import market_agent, MARKET_TOOLS

class AgentRegistry:
    """
    Centralized registry for all pre-configured LLM agent instances with bound tools.
    Provides unified access to agents, completely decoupled from managers and nodes.
    No node or tool should create LLM-related variables inline.
    """
    intake = intake_agent
    market = market_agent
