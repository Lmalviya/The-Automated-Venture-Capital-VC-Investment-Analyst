# due_diligence.py
from vs_analyst.utility.llm import llm
from vs_analyst.tools.deep_research import deep_research_tool
from vs_analyst.tools.market_tools import web_search_tool

# 1. DD Extractor Agent (pure state extraction)
DD_EXTRACTOR_TOOLS = []
dd_extractor_agent = llm.bind_tools(DD_EXTRACTOR_TOOLS)

# 2. DD Legal Verifier Agent (bound to deep_research_tool)
DD_LEGAL_VERIFIER_TOOLS = [deep_research_tool]
dd_legal_verifier_agent = llm.bind_tools(DD_LEGAL_VERIFIER_TOOLS)

# 3. DD Traction Verifier Agent (bound to deep_research_tool)
DD_TRACTION_VERIFIER_TOOLS = [deep_research_tool]
dd_traction_verifier_agent = llm.bind_tools(DD_TRACTION_VERIFIER_TOOLS)

# 4. DD Press Verifier Agent (bound to web_search_tool)
DD_PRESS_VERIFIER_TOOLS = [web_search_tool]
dd_press_verifier_agent = llm.bind_tools(DD_PRESS_VERIFIER_TOOLS)

# 5. DD Synthesizer Agent (pure synthesis, no tools)
DD_SYNTHESIZER_TOOLS = []
dd_synthesizer_agent = llm.bind_tools(DD_SYNTHESIZER_TOOLS)
