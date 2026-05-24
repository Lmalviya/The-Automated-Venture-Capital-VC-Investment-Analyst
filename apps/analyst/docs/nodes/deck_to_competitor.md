# Node Specification: deck_to_competitor (Competitor Seed Extraction Node)

## Aim
Identify and extract key competitors, their websites, and competitor types (Direct vs. Indirect) mentioned in the pitch deck and website, structuring them into the competitor section of the state. This node acts as the **initial seed extraction step** inside the Competitor Sub-Graph, providing the baseline context for the discovery loop.

## Inputs
- **`PipelineGraphState.raw_deck_text`** (`str`): Raw text extracted from the pitch deck.
- **`PipelineGraphState.raw_website_text`** (`str`, Optional): Scraped text from the official startup website.

## Output Structure (Pydantic Schema)
Expected output must map directly to **`CompetitorAdaptor`** in `vs_analyst/schemas/adapters.py`:
- `competitors` (`List[CompetitorSchemaAdaptor]`)
  - `name` (`str`)
  - `website_url` (`HttpUrl`)
  - `competitor_type` (`CompetitorType` enum: `DIRECT`, `INDIRECT`, `UNKNOWN`)

## Target Value (State Variables to Update)
- Replaces or appends to `AnalysisState.competitive.competitors` (`List[CompetitorSchema]` in `vs_analyst/schemas/competitive.py`).

## Working Flow
1. **Context Synthesis**: Read `raw_deck_text` and `raw_website_text` from the state.
2. **LLM Structured Extraction**: Invoke the LLM compiled with `.with_structured_output(CompetitorAdaptor)`.
   - Provide a specialized prompt instructing the LLM to search for competitive matrix slides, lists of competitor names, comparison grids, or sentences referencing other players in the sector.
3. **State Syncing**:
   - Iterate over the extracted list of competitors in the adapter response.
   - For each competitor, map its fields to a new `CompetitorSchema` object and append it to `AnalysisState.competitive.competitors` if a competitor with that name is not already present.
4. **Transition to Competitor Finder Planner**:
   - The sub-graph passes control to the **Competitor Finder Planner Node** (`competitor_finder_planner`).

## Conditions / Branching Rules
- **No Competitors Listed**: If no competitors are extracted, set `AnalysisState.competitive.competitors` to an empty list, and log a warning in `AnalysisState.company.extracted_notes`: "No competitors declared in intake sources."
- **Ambiguous Competitor Type**: Default to `CompetitorType.UNKNOWN` based on context.
