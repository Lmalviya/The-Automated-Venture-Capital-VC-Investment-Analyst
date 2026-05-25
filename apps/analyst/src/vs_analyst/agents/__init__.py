from .intake import intake_agent, INTAKE_TOOLS, deep_research_synthesizer_agent
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
from .report import (
    executive_summary_writer_agent,
    market_section_writer_agent,
    competitor_section_writer_agent,
    founder_section_writer_agent,
    dd_section_writer_agent,
    investment_advocate_agent,
    investment_adversary_agent,
    growth_strategist_agent,
    hazard_mitigator_agent,
    venture_partner_ic_agent,
    memo_reviewer_agent,
    compiler_agent,
)

class AgentRegistry:
    """
    Centralized registry for all pre-configured LLM agent instances with bound tools.
    Provides unified access to agents, completely decoupled from managers and nodes.
    No node or tool should create LLM-related variables inline.
    """
    intake = intake_agent
    deep_research_synthesizer = deep_research_synthesizer_agent
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

    # Report / Memo agents
    executive_summary_writer = executive_summary_writer_agent
    market_section_writer = market_section_writer_agent
    competitor_section_writer = competitor_section_writer_agent
    founder_section_writer = founder_section_writer_agent
    dd_section_writer = dd_section_writer_agent
    investment_advocate = investment_advocate_agent
    investment_adversary = investment_adversary_agent
    growth_strategist = growth_strategist_agent
    hazard_mitigator = hazard_mitigator_agent
    venture_partner_ic = venture_partner_ic_agent
    memo_reviewer = memo_reviewer_agent
    compiler = compiler_agent
