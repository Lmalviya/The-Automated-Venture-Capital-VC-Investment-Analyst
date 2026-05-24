# Node Specification: deck_to_market (Market Seed Extraction Node)

## Aim
Extract the startup-claimed market sizing estimates (TAM, SAM, SOM) along with general market dynamic inputs (growth rate, key trends, macro risks) from raw text and structure it into the state. This node acts as the **initial seed extraction step** inside the Market Sub-Graph, providing the baseline context for the planning loop.

## Inputs
- **`PipelineGraphState.raw_deck_text`** (`str`): Raw text extracted from the pitch deck.
- **`PipelineGraphState.raw_website_text`** (`str`, Optional): Scraped text from the official startup website.

## Output Structure (Pydantic Schema)
Expected output must map directly to **`MarketAdaptor`** in `vs_analyst/schemas/adapters.py`:
- `tam` (`MarketSize` schema: value, year, source, etc.)
- `sam` (`MarketSize` schema)
- `som` (`MarketSize` schema)
- `growth_rate` (`str`, e.g., "CAGR 18% through 2028")
- `growth_source` (`str`)
- `key_trends` (`List[str]`)
- `market_risks` (`List[str]`)

## Target Value (State Variables to Update)
- Updates `AnalysisState.market` (`MarketSchema` in `vs_analyst/schemas/market.py`).
- Specifically maps:
  - `market.tam`, `market.sam`, `market.som`
  - `market.growth_rate`, `market.growth_source`
  - `market.key_trends`, `market.market_risks`

## Working Flow
1. **Context Synthesis**: Read `raw_deck_text` and `raw_website_text` from the state.
2. **LLM Structured Extraction**: Invoke the LLM with `.with_structured_output(MarketAdaptor)`.
   - Provide a specialized prompt instructing the LLM to search for market slides, TAM/SAM/SOM dollar values, growth statistics, CAGR claims, and industry trends mentioned in the pitch deck.
3. **State Syncing**:
   - Map and write each size estimator (`tam`, `sam`, `som`) into the target fields under `AnalysisState.market`.
   - Set the general attributes `growth_rate`, `growth_source`, `key_trends`, and `market_risks` on `AnalysisState.market`.
4. **Transition to Market Planner**:
   - The sub-graph passes control to the **Market Planner Node** (`market_planner`).

## Conditions / Branching Rules
- **Missing Sizing Values**: If only TAM is found, SAM and SOM fields in state will remain with default empty values.
- **Non-Numeric Market Sizes**: If a size is stated as text (e.g., "Very large," "Billions"), attempt to extract a numerical range or save it in the `notes` field of the `MarketSize` schema.
