import json
import asyncio
import httpx
from typing import List, Dict, Set, Union, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from vs_analyst.config import settings
from vs_analyst.utility.logs import get_logger
from vs_analyst.tools.relevance import bm25_rank

logger = get_logger(__name__)

# Optional Crawl4AI import for premium JS rendering
CRAWL4AI_AVAILABLE = False
try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    pass

IGNORE_EXTENSIONS: Set[str] = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".zip", ".tar", ".gz",
    ".mp4", ".mp3", ".wav", ".avi", ".mov", ".exe", ".dmg", ".pkg", ".css", ".js",
    ".ico", ".woff", ".woff2", ".ttf", ".eot"
}

class ScrapedPage(BaseModel):
    url: str
    text_content: str

def normalize_url(url: str) -> str:
    """Normalizes a URL by stripping fragments and trailing slashes."""
    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        return f"{parsed.scheme}://{parsed.netloc}{path}"
    except Exception:
        return url

def is_same_domain(url1: str, url2: str) -> bool:
    """Checks if two URLs share the same netloc domain."""
    try:
        return urlparse(url1).netloc == urlparse(url2).netloc
    except Exception:
        return False

def should_ignore_url(url: str) -> bool:
    """Checks if the URL path points to static assets or media files."""
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        return any(path.endswith(ext) for ext in IGNORE_EXTENSIONS)
    except Exception:
        return True

def clean_html_to_text(html_content: str) -> str:
    """Strips HTML boilerplate and returns high-density text elements."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    # Strip non-informational elements
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        element.decompose()
        
    # Get paragraphs, headers, and list items
    lines = []
    for el in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"]):
        text = el.get_text(strip=True)
        if text:
            lines.append(text)
            
    return "\n\n".join(lines)

async def _crawl_single_domain_local(start_url: str, client: httpx.AsyncClient, depth: int, max_page: int) -> List[ScrapedPage]:
    """Crawls a single root URL using an asynchronous BFS same-domain crawler."""
    logger.info("Starting local async crawl for domain", start_url=start_url, depth=depth, max_page=max_page)
    
    visited: Set[str] = set()
    scraped_pages: List[ScrapedPage] = []
    
    # Queue stores tuples of (url, current_depth)
    queue: List[tuple[str, int]] = [(normalize_url(start_url), 1)]
    
    while queue and len(visited) < max_page:
        # Get all URLs at the current level to fetch them concurrently
        current_level_urls = []
        next_level_queue = []
        
        for url, d in queue:
            if url not in visited and len(visited) + len(current_level_urls) < max_page:
                current_level_urls.append((url, d))
            else:
                next_level_queue.append((url, d))
                
        if not current_level_urls:
            break
            
        # Execute concurrent requests for the current BFS layer
        async def fetch_and_parse(target_url: str, d: int) -> Optional[ScrapedPage]:
            try:
                logger.debug("Fetching page in crawler", url=target_url, current_depth=d)
                response = await client.get(target_url, timeout=6.0, follow_redirects=True)
                if response.status_code == 200:
                    html_content = response.text
                    clean_text = clean_html_to_text(html_content)
                    
                    # Extract same-domain links for next depth level if we haven't hit depth limit
                    links_found = []
                    if d < depth:
                        soup = BeautifulSoup(html_content, "html.parser")
                        for a in soup.find_all("a", href=True):
                            absolute_link = urljoin(target_url, a["href"])
                            normalized = normalize_url(absolute_link)
                            if (
                                is_same_domain(start_url, normalized)
                                and not should_ignore_url(normalized)
                                and normalized not in visited
                            ):
                                links_found.append(normalized)
                                
                    return ScrapedPage(url=target_url, text_content=clean_text), links_found
            except Exception as e:
                logger.warning("Failed to fetch page in local crawler", url=target_url, error=str(e))
            return None
            
        tasks = [fetch_and_parse(url, d) for url, d in current_level_urls]
        results = await asyncio.gather(*tasks)
        
        # Update queue and visited tracker
        queue = next_level_queue
        for res in results:
            if res:
                page, new_links = res
                visited.add(page.url)
                scraped_pages.append(page)
                
                # Add discovered same-domain links to queue for next BFS level
                for link in new_links:
                    if link not in visited:
                        # Grab the current depth and add 1
                        current_d = next(d for u, d in current_level_urls if u == page.url)
                        queue.append((link, current_d + 1))
                        
    return scraped_pages

async def _crawl_local(urls: List[str], depth: int, max_page: int) -> List[ScrapedPage]:
    """Crawls a list of URLs locally in parallel using BeautifulSoup."""
    logger.info("Executing local BeautifulSoup async crawler", urls=urls)
    
    limits = httpx.Limits(max_connections=15, max_keepalive_connections=5)
    async with httpx.AsyncClient(limits=limits, headers={"User-Agent": "VC-Investment-Analyst-Bot/1.0"}) as client:
        tasks = [_crawl_single_domain_local(url, client, depth, max_page) for url in urls]
        results = await asyncio.gather(*tasks)
        
    # Flatten results from all domains
    flat_results = []
    for res_list in results:
        flat_results.extend(res_list)
    return flat_results

async def _extract_tavily(urls: List[str]) -> List[ScrapedPage]:
    """Scrapes clean text content from a list of URLs in parallel using Tavily's Extract API."""
    if not settings.tavily_api_key:
        raise ValueError("Tavily API key is not configured.")
        
    logger.info("Executing Tavily Extract API concurrent scraping", urls=urls)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://api.tavily.com/extract",
            json={
                "api_key": settings.tavily_api_key.get_secret_value(),
                "urls": urls
            }
        )
        response.raise_for_status()
        data = response.json()
        
    scraped_pages = []
    for r in data.get("results", []):
        scraped_pages.append(
            ScrapedPage(
                url=r.get("url", ""),
                text_content=r.get("raw_content", "")
            )
        )
    return scraped_pages

@tool
async def website_scraper_tool(
    urls: List[str],
    depth: int = 2,
    max_page: int = 5,
    query: str = "",
    goal: str = ""
) -> str:
    """
    Crawls and scrapes a list of starting URLs up to a specific depth and page limit.
    Filters high-relevance paragraphs using Okapi BM25 ranking, and synthesizes 
    key insights in a single non-hallucinatory LLM extraction report.

    Args:
        urls: List of starting website URLs to crawl and scrape.
        depth: Maximum crawl depth (default: 2, used in local BFS mode).
        max_page: Maximum number of pages to crawl per domain (default: 5).
        query: General context query describing the target startup/sector.
        goal: The guiding objective or requirements directing what information to extract.
    """
    logger.info("website_scraper_tool invoked", urls=urls, provider=settings.search_provider, depth=depth, max_page=max_page)
    
    if not urls:
        return json.dumps({"error": "No URLs provided to scrape."})

    scraped_pages: List[ScrapedPage] = []
    
    # 1. Fetching Phase (Dual Engine)
    if settings.search_provider == "tavily" and settings.tavily_api_key:
        try:
            scraped_pages = await _extract_tavily(urls)
        except Exception as e:
            logger.warning("Tavily Extract API failed. Falling back to local crawler.", error=str(e))
            scraped_pages = await _crawl_local(urls, depth, max_page)
    else:
        scraped_pages = await _crawl_local(urls, depth, max_page)

    if not scraped_pages:
        return "Web scraper was unable to successfully crawl or parse any content from the provided URLs."

    # 2. Text Segmenting & Heuristic Cleaning
    all_chunks: List[Dict[str, str]] = []
    for page in scraped_pages:
        # Split page content into logical paragraph chunks
        paragraphs = [p.strip() for p in page.text_content.split("\n\n") if len(p.strip()) > 30]
        for p in paragraphs:
            all_chunks.append({
                "url": page.url,
                "text": p
            })

    logger.info("Website crawling completed", pages_crawled=len(scraped_pages), total_chunks=len(all_chunks))

    # 3. BM25 Scoring & Ranking
    selected_chunks = []
    if all_chunks:
        # Combine query and goal to build relevance matching target
        ranking_target = f"{query} {goal}".strip()
        corpus = [chunk["text"] for chunk in all_chunks]
        
        # Choose top 15 highest-density paragraphs matching BM25
        top_k = min(len(all_chunks), 15)
        ranked_indices = bm25_rank(ranking_target, corpus, top_k=top_k)
        
        selected_chunks = [all_chunks[idx] for idx in ranked_indices]
    
    return json.dumps(selected_chunks)
