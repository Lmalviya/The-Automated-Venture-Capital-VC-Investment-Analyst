# founder.py
from vs_analyst.utility.llm import llm
from vs_analyst.tools.deep_research import deep_research_tool

# 1. Founder Profiler Agent (bound to deep_research_tool)
FOUNDER_PROFILER_TOOLS = [deep_research_tool]
founder_profiler_agent = llm.bind_tools(FOUNDER_PROFILER_TOOLS)

# 2. Founder Risk Analyst Agent (pure synthesis, no tools)
FOUNDER_RISK_ANALYST_TOOLS = []
founder_risk_analyst_agent = llm.bind_tools(FOUNDER_RISK_ANALYST_TOOLS)
