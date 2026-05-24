from .intake import intake_agent, INTAKE_TOOLS
from .market import (
    market_planner_agent, MARKET_PLANNER_TOOLS,
    market_synthesizer_agent, MARKET_SYNTHESIZER_TOOLS,
    market_risk_analyst_agent, MARKET_RISK_TOOLS,
)
from .competitor import (
    competitor_finder_planner_agent, COMPETITOR_FINDER_PLANNER_TOOLS,
    competitor_finder_synthesizer_agent, COMPETITOR_FINDER_SYNTHESIZER_TOOLS,
    competitor_investigator_planner_agent, COMPETITOR_INVESTIGATOR_PLANNER_TOOLS,
    competitor_investigator_synthesizer_agent, COMPETITOR_INVESTIGATOR_SYNTHESIZER_TOOLS,
    competitive_risk_analyst_agent, COMPETITIVE_RISK_ANALYST_TOOLS,
)
from .founder import (
    founder_profiler_agent, FOUNDER_PROFILER_TOOLS,
    founder_risk_analyst_agent, FOUNDER_RISK_ANALYST_TOOLS,
)
from .due_diligence import (
    dd_extractor_agent, DD_EXTRACTOR_TOOLS,
    dd_legal_verifier_agent, DD_LEGAL_VERIFIER_TOOLS,
    dd_traction_verifier_agent, DD_TRACTION_VERIFIER_TOOLS,
    dd_press_verifier_agent, DD_PRESS_VERIFIER_TOOLS,
    dd_synthesizer_agent, DD_SYNTHESIZER_TOOLS,
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
    
    # Competitor agents
    competitor_finder_planner = competitor_finder_planner_agent
    competitor_finder_synthesizer = competitor_finder_synthesizer_agent
    competitor_investigator_planner = competitor_investigator_planner_agent
    competitor_investigator_synthesizer = competitor_investigator_synthesizer_agent
    competitive_risk_analyst = competitive_risk_analyst_agent
    
    # Founder agents
    founder_profiler = founder_profiler_agent
    founder_risk_analyst = founder_risk_analyst_agent
    
    # Due Diligence agents
    dd_extractor = dd_extractor_agent
    dd_legal_verifier = dd_legal_verifier_agent
    dd_traction_verifier = dd_traction_verifier_agent
    dd_press_verifier = dd_press_verifier_agent
    dd_synthesizer = dd_synthesizer_agent
