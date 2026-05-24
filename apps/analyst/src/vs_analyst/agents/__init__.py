from .intake import intake_agent, INTAKE_TOOLS
from .market import (
    market_planner_agent, MARKET_PLANNER_TOOLS,
    market_synthesizer_agent, MARKET_SYNTHESIZER_TOOLS,
    market_risk_analyst_agent, MARKET_RISK_TOOLS,
)

class AgentRegistry:
    """
    Centralized registry for all pre-configured LLM agent instances with bound tools.
    Provides unified access to agents, completely decoupled from managers and nodes.
    No node or tool should create LLM-related variables inline.
    """
    intake = intake_agent
    market_planner = market_planner_agent
    market_synthesizer = market_synthesizer_agent
    market_risk_analyst = market_risk_analyst_agent
