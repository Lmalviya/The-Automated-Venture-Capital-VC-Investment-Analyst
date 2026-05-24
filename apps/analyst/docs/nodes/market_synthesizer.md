# Node Specification: market_synthesizer (Market Research Synthesizer Node)

## Aim
Consolidate the startup's claims (extracted from the pitch deck/website) with independent market research sources collected during the planning-loop phase. The node outputs a verified, structured market profile, resolves data conflicts, and assigns confidence levels based on search-result reliability.

## Inputs
- **`PipelineGraphState.analysis_state`** (`AnalysisState`): Specifically:
  - `analysis_state.company` (for business context)
  - `analysis_state.market` (containing the initial deck claims, `queries_used`, and `research_sources` containing crawled research details and citations)

## Tools Available (Utility Only — No Internet Access)
- **`parse_numeric_value(amount_str)`** — Parses multi-currency market sizing strings (e.g., `"₹800Cr"`, `"$4B"`) before comparing founder-claimed values against independently researched values.
- **`calculate_percentage(part, whole)`** — Computes the discrepancy ratio between a founder's TAM claim and the independently researched figure (e.g., founder claims $100B, research shows $10B → 10% of claimed value).

## Output Structure (Pydantic Schema)
The node returns a structured synthesis model (e.g., `MarketSynthesizerAdaptor` in `vs_analyst/schemas/adapters.py` or defined in `market.py`):
- **`tam`** (`MarketSize`): Verified Total Addressable Market sizing, year, source, source URL, confidence, and context notes.
- **`sam`** (`MarketSize`): Verified Serviceable Addressable Market.
- **`som`** (`MarketSize`): Verified Serviceable Obtainable Market.
- **`growth_rate`** (`str`, e.g., "CAGR 14.2% (2024–2030)"): Synthesized growth rate.
- **`growth_source`** (`str`): Source reference verifying the CAGR.
- **`key_trends`** (`List[str]`): 3–5 synthesized macro industry trends backed by independent sources.
- **`summary`** (`str`): A detailed 2–3 paragraph narrative summarizing the market landscaping, key drivers, and sizing discrepancies for insertion into the investment memo.
- **`overall_confidence`** (`ConfidenceLevel`): A synthesized confidence score (`HIGH`, `MEDIUM`, `LOW`) representing the quality and consensus of the independent sources found.

## Target Value (State Variables to Update)
- Updates `AnalysisState.market` (`MarketSchema` in `vs_analyst/schemas/market.py`).
- Specifically overwrites:
  - `market.tam`, `market.sam`, `market.som`
  - `market.growth_rate`, `market.growth_source`
  - `market.key_trends`
  - `market.summary`
  - `market.overall_confidence`
- **Important**: Existing `research_sources` and `queries_used` in the state must be preserved as an audit trail.

## Working Flow
1. **Source Aggregation**:
   - Collect the initial claims extracted from the deck/website and the accumulated list of raw research findings (`research_sources`).
2. **Conflict Resolution**:
   - The LLM compares the startup's claims against independent research:
     - If the startup claims an inflated TAM (e.g., $100B) but independent reports suggest a smaller realistic market (e.g., $10B), the LLM populates the state with the realistic independent number, marks `confidence = LOW` on the TAM estimate, and documents the discrepancy in the TAM `notes` field.
     - Source URL links must be mapped from the corresponding `ResearchSource` objects to the `source_url` fields in the `MarketSize` models.
3. **Synthesis Generation**:
   - Write a 2-3 paragraph synthesis describing the market environment, segment growth, and competitive drivers.
4. **State Writing**:
   - Update `AnalysisState.market` with the structured outputs.

## Conditions / Branching Rules
- **No Research Found**: If the planning loop failed to gather external sources, the LLM falls back to the initial deck claims, marks all sizing elements with `confidence = LOW`, and adds a note explaining that web verification was unavailable.
- **Direct Transition**: After this node completes, the pipeline transitions to the **Market Risk Analyst Node**.
