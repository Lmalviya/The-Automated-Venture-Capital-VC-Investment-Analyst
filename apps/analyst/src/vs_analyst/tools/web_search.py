import json
import asyncio
import httpx
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from vs_analyst.config import settings
from vs_analyst.utility.logs import get_logger
from vs_analyst.tools.relevance import bm25_rank

logger = get_logger(__name__)

class SearchResult(BaseModel):
    title: str = Field(..., description="The title of the search result")
    url: str = Field(..., description="The source URL")
    snippet: str = Field(..., description="A snippet containing key information")

async def _query_searxng(query: str, client: httpx.AsyncClient, top_k: int = 5) -> List[SearchResult]:
    if not settings.searxng_url:
        raise ValueError("SearXNG URL is not configured.")
        
    url = f"{str(settings.searxng_url).rstrip('/')}/search"
    logger.info("Querying SearXNG metasearch", url=url, query=query, top_k=top_k)
    
    response = await client.get(
        url,
        params={"q": query, "format": "json"},
        timeout=settings.search_timeout
    )
    response.raise_for_status()
    data = response.json()
    
    results = []
    for r in data.get("results", [])[:top_k]:
        results.append(
            SearchResult(
                title=r.get("title", "No Title"),
                url=r.get("url", ""),
                snippet=r.get("content", "")
            )
        )
    return results

async def _query_tavily(query: str, client: httpx.AsyncClient, top_k: int = 5) -> List[SearchResult]:
    if not settings.tavily_api_key:
        raise ValueError("Tavily API key is not configured.")
        
    logger.info("Querying Tavily search", query=query, top_k=top_k)
    
    response = await client.post(
        "https://api.tavily.com/search",
        json={
            "api_key": settings.tavily_api_key.get_secret_value(),
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "max_results": top_k
        },
        timeout=settings.search_timeout
    )
    response.raise_for_status()
    data = response.json()
    
    results = []
    for r in data.get("results", [])[:top_k]:
        results.append(
            SearchResult(
                title=r.get("title", "No Title"),
                url=r.get("url", ""),
                snippet=r.get("content", "")
            )
        )
    return results

@tool
async def web_search_tool(query: str, top_k: int = 5) -> str:
    """
    Searches the web for market trends, competitor information, or general queries.
    Returns a structured JSON list of search results.

    Args:
        query: The search query to run.
        top_k: The number of top search results to return (default: 5).
    """
    logger.info("web_search_tool invoked with BM25 ranking", query=query, provider=settings.search_provider, top_k=top_k)
    
    max_retries = 3
    initial_delay = 1.0  # seconds
    backoff_factor = 2.0
    
    results = []
    last_error = None

    # Fetch more results initially to perform high-quality local BM25 ranking
    fetch_k = max(top_k * 2, 10)

    # Connection pooling with httpx.Limits
    limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
    
    try:
        async with httpx.AsyncClient(limits=limits) as client:
            for attempt in range(max_retries):
                try:
                    if settings.search_provider == "tavily":
                        results = await _query_tavily(query, client, fetch_k)
                    else:
                        results = await _query_searxng(query, client, fetch_k)
                    break
                except Exception as e:
                    last_error = str(e)
                    logger.warning(
                        "Web search attempt failed",
                        attempt=attempt+1,
                        query=query,
                        provider=settings.search_provider,
                        error=last_error
                    )
                    if attempt < max_retries - 1:
                        delay = initial_delay * (backoff_factor ** attempt)
                        await asyncio.sleep(delay)
    except Exception as e:
        last_error = str(e)
        logger.error("Web search client initialization or request failed", error=last_error)

    # Clean fallback: Return a structured search summary with the error message so the LLM agent is informed
    if last_error is not None and not results:
        fallback_msg = f"Web search service is currently unavailable. No external live results could be retrieved for this query. (Error: {last_error})"
        fallback_result = [
            SearchResult(
                title="Search Status",
                url="N/A",
                snippet=fallback_msg
            )
        ]
        return json.dumps([r.model_dump() for r in fallback_result])

    # Apply Okapi BM25 Ranking locally on the retrieved candidates
    if results and len(results) > 1:
        logger.info("Applying BM25 re-ranking on search candidates", candidate_count=len(results))
        # Build text representation for BM25: combining title and snippet content
        corpus = [f"{r.title} {r.snippet}" for r in results]
        ranked_indices = bm25_rank(query, corpus, top_k=top_k)
        results = [results[i] for i in ranked_indices]
    else:
        results = results[:top_k]
        
    return json.dumps([r.model_dump() for r in results])
