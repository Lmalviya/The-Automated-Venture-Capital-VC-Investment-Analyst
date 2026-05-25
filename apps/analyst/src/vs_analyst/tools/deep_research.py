import json
import asyncio
from typing import List
from langchain_core.tools import tool

from vs_analyst.config import settings
from vs_analyst.utility.logs import get_logger
from vs_analyst.tools.web_search import web_search_tool
from vs_analyst.tools.website_scraper import website_scraper_tool

logger = get_logger(__name__)

@tool
async def deep_research_tool(query: str, goal: str, top_k: int = 5) -> str:
    """
    Performs deep vertical market or company research on a topic by dynamically 
    combining metasearch, parallel website crawling, BM25 paragraph ranking, 
    and senior VC expert LLM synthesis with inline citations and full references.

    Args:
        query: The search query or target startup/market to investigate.
        goal: The guiding objective or specific requirements detailing what information to extract.
        top_k: The number of search results and crawl candidates to evaluate (default: 5).
    """
    logger.info("deep_research_tool invoked with advanced parallel orchestrator", query=query, goal=goal, top_k=top_k)
    
    # 1. Search Phase: Retrieve candidate results using the BM25-ranked metasearch tool
    try:
        search_result_str = await web_search_tool.ainvoke({"query": query, "top_k": top_k})
        search_results = json.loads(search_result_str)
    except Exception as e:
        logger.error("Deep research search phase failed", error=str(e))
        return f"Deep research failed during the search phase. (Error: {str(e)})"

    # Extract clean target URLs from the search results
    urls = []
    for r in search_results:
        url = r.get("url")
        if url and url != "N/A" and url.startswith("http"):
            urls.append(url)
            
    # Select the top 3 high-quality URLs for deep crawling
    urls = list(dict.fromkeys(urls))  # Deduplicate while preserving order
    
    if not urls:
        logger.warning("No valid URLs discovered in search phase, returning search snippets directly")
        return f"No crawlable websites could be found for the query. Search findings:\n{json.dumps(search_results, indent=2)}"

    logger.info("URL selection complete. Spawning parallel web crawlers", selected_urls=urls)

    # 2. Scrape & Crawl Phase: Invoke the stateless scraper tool on all target URLs
    # It will crawl each domain in parallel and return the top BM25 ranked chunks matching query + goal
    try:
        chunks_json_str = await website_scraper_tool.ainvoke({
            "urls": urls,
            "depth": 2,
            "max_page": 5,
            "query": query,
            "goal": goal
        })
        chunks = json.loads(chunks_json_str)
    except Exception as e:
        logger.error("Deep research crawling phase failed", error=str(e))
        return f"Deep research failed during the parallel scraping phase. (Error: {str(e)})"

    if not chunks:
        logger.warning("No relevant text chunks crawled, returning search snippets as backup")
        return f"No relevant content could be extracted from the target domains. Search snippets:\n{json.dumps(search_results, indent=2)}"

    # 3. Context Tagging: Format the collected chunks into structured XML source blocks
    xml_context_lines = ["<context>"]
    for chunk in chunks:
        xml_context_lines.append(f'  <source url="{chunk["url"]}">')
        xml_context_lines.append(f'    {chunk["text"]}')
        xml_context_lines.append("  </source>")
    xml_context_lines.append("</context>")
    xml_context = "\n".join(xml_context_lines)

    # 4. Synthesis Phase: Retrieve pre-configured LLM agent and system prompts to compile the report
    logger.info("Executing deep research synthesis using deep_research_synthesizer agent")
    try:
        from vs_analyst.agents import AgentRegistry
        from vs_analyst.prompts import PromptRegistry

        system_prompt = PromptRegistry.deep_research_synthesizer_system.value
        user_prompt = PromptRegistry.deep_research_synthesizer_user.value.format(
            QUERY=query,
            GOAL=goal,
            CONTEXT=xml_context
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Retrieve the pre-configured synthesizer agent from the central registry
        synthesizer_agent = AgentRegistry.deep_research_synthesizer
        # Invoke agent asynchronously
        response = await synthesizer_agent.ainvoke(messages)
        return response.content
        
    except Exception as e:
        logger.error("Deep research LLM synthesis failed. Returning raw XML context as fallback.", error=str(e))
        # Complete fallback: Output raw XML context structured beautifully
        return (
            "Deep research synthesis service was temporarily unavailable, returning raw high-density web context:\n\n"
            f"{xml_context}"
        )
