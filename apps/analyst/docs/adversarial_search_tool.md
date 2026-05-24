# Tool Specification: adversarial_search_tool (Risk-Targeted Search Tool)

## Aim
Provide agents with a specialized search capability focused exclusively on discovering negative evidence, liabilities, hurdles, and risks. The tool automatically enriches any base user query with adversarial search modifiers before querying the metasearch engine, filtering out generic marketing/PR pages.

The tool supports two **modes** that control which modifier set is appended to the query. Each mode is bound to a specific node.

## Inputs
- **`query`** (`str`): The base search query (e.g., *"Acme Corp"* or *"autonomous drone delivery regulations"*).
- **`mode`** (`Literal["market_risk", "competitor_risk"]`): Controls which adversarial modifier set is applied to the query.

## Output Structure
- Returns a structured JSON string or list of results:
  ```json
  [
    {
      "title": "Title of the risk-related source",
      "url": "https://example.com/regulatory-filing",
      "snippet": "Snippet containing details of the lawsuit, compliance failure, or market risk..."
    }
  ]
  ```

## Backend Infrastructure
- Queries the self-hosted **SearXNG** instance (`settings.searxng_url`) using the modified query string.
- Returns up to a configurable number of results (e.g., top 5).

## Query Enrichment Logic (Adversarial Modifiers)
When the tool is called, the Python code intercepts the `query` parameter and appends mode-specific risk-related search operators.

### `mode="market_risk"` (Owner: `market_risk_analyst` node)
Used to discover macro-level threats: regulatory filings, compliance failures, legal actions, and sector-wide vulnerabilities.

- **Enriched Query Form:**
  `"Q" AND (site:gov OR "regulatory risk" OR "lawsuit" OR "SEC filing" OR "compliance challenge" OR "security exploit" OR "vulnerability" OR "market limitations")`
- *Example:*
  - Input: `quantum key distribution supply chain`
  - Executed: `quantum key distribution supply chain AND (site:gov OR "regulatory risk" OR "lawsuit" OR "SEC filing" OR "compliance challenge" OR "security exploit" OR "vulnerability" OR "market limitations")`

### `mode="competitor_risk"` (Owner: `competitor_investigator_planner` node)
Used to discover competitor-specific negative signals: customer complaints, stagnation indicators, pricing issues, layoffs, and product failures.

- **Enriched Query Form:**
  `"Q" AND ("complaints" OR "negative reviews" OR "layoffs" OR "pricing problems" OR "funding stalled" OR "shutting down" OR "product issues" OR "G2 review" OR "Capterra review")`
- *Example:*
  - Input: `Acme Corp`
  - Executed: `Acme Corp AND ("complaints" OR "negative reviews" OR "layoffs" OR "pricing problems" OR "funding stalled" OR "shutting down" OR "product issues" OR "G2 review" OR "Capterra review")`

## Integration Guidelines
- **`mode="market_risk"`** is bound **only** to the `market_risk_analyst_agent`.
- **`mode="competitor_risk"`** is bound **only** to the `competitor_investigator_planner` agent (used during the adversarial research step of parallel competitor profiling).
- Results from either mode must be appended to the relevant state audit trail (`queries_used` and `research_sources`) for full auditability.

---

> **⚠️ Design Note:** The two modes share the same underlying SearXNG infrastructure and differ only in modifier strings. This avoids duplicating tool code while keeping each agent's search behavior clearly scoped. If the modifier sets diverge significantly in future iterations, splitting into two separate tools should be reconsidered.
