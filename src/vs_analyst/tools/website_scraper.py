from pydantic import BaseModel, Field
from vs_analyst.utility.logs import get_logger
from langchain_core.tools import tool


logger = get_logger(__name__)

class WebsiteScraperInput(BaseModel):
    url: str = Field(..., description="The company website URL to crawl and scrape.")

class WebsiteScraperOutput(BaseModel):
    url: str = Field(..., description="The crawled website URL.")
    text_content: str = Field(..., description="The raw or parsed text content extracted from the website.")

async def website_scraper(url: str, log) -> WebsiteScraperOutput:
    """
    Website Scraper Tool (Stub).
    Crawls and extracts text content from the company's homepage, about page, and product pages.
    """
    log.info("Running website scraper tool (stub)", url=url)
    
    # Return a basic placeholder text for Phase-1 testing
    return WebsiteScraperOutput(
        url=url,
        text_content=f"[Website Scraper Stub] Successfully scraped content from {url}."
    )


@tool
async def website_scraper_tool(url: str) -> str:
    """
    Scrapes text content from a startup's website.
    Use this tool when a company website URL is provided.

    Args:
        url: The company website URL to crawl and scrape.
    """
    log = get_logger("website_scraper_tool")
    log.info("website_scraper_tool invoked", url=url)

    result = await website_scraper(url, log)
    return result.model_dump_json()
