from langchain_core.tools import tool

from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


@tool
def web_search_tool(query: str) -> str:
    """
    Searches the web for market research data relevant to the startup.
    Use this tool to find market size figures, industry trends, and
    competitor intelligence from external sources.

    Args:
        query: The search query string, e.g. 'EdTech market size India 2024'.

    Note: This tool is currently in stub mode (Phase 2 implementation pending).
    """
    logger.info("web_search_tool invoked (stub)", query=query)
    return f"[Web Search Stub] No real results yet for query: '{query}'. Phase 2 pending."


@tool
def market_synthesizer_tool(raw_data: str) -> str:
    """
    Synthesizes raw market research data into structured market insights.
    Use this tool after web_search_tool to process and structure the search results.

    Args:
        raw_data: Raw text or JSON string of market research data to synthesize.

    Note: This tool is currently in stub mode (Phase 2 implementation pending).
    """
    logger.info("market_synthesizer_tool invoked (stub)")
    return "[Market Synthesizer Stub] Synthesis complete. Phase 2 pending."
