# Web Tools & Research Architecture Guidelines

This document outlines the blueprints, requirements, and strict design specifications for our search, crawling, and composite research tools. These tools are designed to provide accurate, privacy-respecting, and highly synthesized domain data for the VC Investment Analyst.

---

## 1. Web Search Tool (SearXNG Metasearch)

The Search Tool must use a self-hosted **SearXNG** instance to aggregate results from multiple search engines in a private and rate-limit-resistant manner.

### Tool Specifications:
- **Inputs:**
  - `query` (`str`): The search query to run (e.g., *"Acme Corp competitors"*).
- **Outputs:**
  - A structured list of results: `[{"title": "...", "url": "...", "snippet": "..."}]`.
- **Backend Infrastructure:**
  - Direct JSON API queries to the self-hosted SearXNG endpoint (`settings.searxng_url`).
  - Strict URL routing configuration using Pydantic Settings.

### Self-Hosted SearXNG Setup (Docker-Compose):
To run a self-hosted SearXNG instance locally, add this block to the main `docker-compose.yml`:
```yaml
services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng:ro
    environment:
      - SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml
    restart: always
```

---

## 2. URL Crawler Tool (Crawl4AI + Agent Optimizer)

The Crawler Tool uses `Crawl4AI` to spider a website up to a configurable depth and cleans the raw output using dedicated text clean-and-filter libraries before executing an internal LLM optimization agent.

### Tool Specifications:
- **Inputs:**
  - `url` (`str`): Absolute start URL to crawl.
  - `goal` (`str`): The perspective, requirement, or specific instruction directing what information to extract (e.g., *"Identify user traction metrics"*).
- **Target Configurations (Configured in `config.py`):**
  - `settings.crawl_depth_limit` (Default: `2`)
  - `settings.crawl_max_pages` (Default: `5` per domain)
- **Cleaning Requirement (Strict):**
  - **Zero Raw HTML:** Raw HTML/boilerplate must never be passed to the LLM.
  - Use `trafilatura` or `beautifulsoup4` to extract pure readable text blocks, strip navigational menus, sidebars, headers, and footers, and return clean Markdown/text.
- **Internal Optimization Agent:**
  - Once the crawled pages are cleaned, a dedicated internal LLM call (utilizing `query_text_model`) takes the cleaned content, the original `url`, and the `goal`, and synthesizes a highly focused target summary.

---

## 3. Deep Research Tool (Composite Meta-Search)

The Research Tool orchestrates the Search and Crawler tools sequentially to perform deep vertical market research, executing all web crawls concurrently.

### Tool Specifications:
- **Inputs:**
  - `query` (`str`): Base search term (e.g., *"Enterprise LLM security standard"*).
  - `goal` (`str`): The objective/perspective guiding the synthesis (e.g., *"Compare compliance standards of top security providers"*).
- **Orchestration Flow:**
  1. **Search Phase:** Call the Web Search Tool with `query` to gather search results.
  2. **URL Selection:** Extract the top-K URLs (e.g., top 3) from the search output.
  3. **Concurrent Crawl Phase (Strictly Asynchronous):**
     * Invoke the URL Crawler Tool on the selected URLs.
     * **Must execute parallelly/asynchronously** using `asyncio.gather` so that all domains are crawled concurrently, preventing sequential network blocking.
  4. **Synthesis Phase:**
     * Run an internal LLM call to synthesize the crawled summaries.
     * **Auditability Requirement:** The synthesized report must contain strict inline citations (e.g., `[1]`, `[2]`) pointing to specific source URLs.
     * Append a structured, numbered **References** list at the bottom of the output, mapping each citation key back to its source URL.
