from vs_analyst.utility.llm import llm
from vs_analyst.tools.website_scraper import website_scraper_tool

# List of tools assigned to the Intake Agent
INTAKE_TOOLS = [
    website_scraper_tool,
]

# Configured LLM runner with bound tools
intake_agent = llm.bind_tools(INTAKE_TOOLS)
