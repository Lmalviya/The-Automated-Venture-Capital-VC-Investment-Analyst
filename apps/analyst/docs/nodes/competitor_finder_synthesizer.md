# Node Specification: competitor_finder_synthesizer (Competitor Discovery Synthesizer Node)

## Aim
Consolidate the entire competitor candidate pool (including the pre-populated seed list from intake and any raw crawler/search summaries from the planner loop). The synthesizer deduplicates competitors, classifies each based on customer overlap and solution approach, discards irrelevant false positives, and locks 2-3 sector-specific custom dimensions.

## Inputs
- **`PipelineGraphState.analysis_state`** (`AnalysisState`):
  - `analysis_state.company` (for ICP, core problem, and value proposition context)
  - `analysis_state.competitive.competitors` (the initial seed list plus any new entries accumulated during discovery)
  - `analysis_state.competitive.research_sources` (raw crawls and search summaries of potential candidates)

## Tools Available
None. This is a cognitive-only synthesis node.

## Output Structure (Pydantic Schema)
The node returns a structured discovery decision to write to the state:
- **`CompetitorDiscoveryResult`** (defined in `vs_analyst/schemas/adapters.py`):
  - `qualified_competitors` (`List[CompetitorDiscoveryEntry]`): Final validated list.
    - `name` (`str`)
    - `website_url` (`Optional[HttpUrl]`)
    - `competitor_type` (`CompetitorType`): `DIRECT`, `INDIRECT`, `EMERGING`, `SUBSTITUTE`.
    - `rationale` (`str`): One-sentence justification of classification.
  - `custom_dimension_keys` (`List[str]`): 2–3 sector-specific dimension keys chosen by the LLM (e.g., `["regulatory_licenses", "api_integrations"]` for Fintech). These must be concise snake_case keys.

## Target Value (State Variables to Update)
- Merges `qualified_competitors` into `AnalysisState.competitive.competitors`.
  - **Crucial Merge Rule:** Do not drop seed competitors that were pre-populated during intake. If a seed competitor is missing details, merge the discovered details (e.g., website URLs or updated type classification) instead of overwriting the entire object.
- Writes `custom_dimension_keys` to `AnalysisState.competitive.custom_dimension_keys`.

## Working Flow
1. **Candidate Consolidation & Deduplication**:
   - Collect all candidate names and website URLs from the seed list and the newly discovered research sources.
   - Deduplicate candidates based on normalized names and domain URLs.
2. **Semantic Classification (Qualifying)**:
   - For each candidate, compare its target market and solution approach to the startup:
     - `DIRECT`: Same customer segment, same solution approach.
     - `INDIRECT`: Same customer segment, different solution approach.
     - `EMERGING`: Early-stage startup with high potential for direct overlap.
     - `SUBSTITUTE`: Different category, but solves the same underlying problem.
     - `FALSE_POSITIVE`: Discarded.
3. **Custom Dimension Selection**:
   - Analyze the company's sector and select 2-3 highly relevant, sector-specific `custom_dimension_keys` that will be consistently profiled across all competitors by the Investigator.
4. **State Writing**:
   - Commit the updated `competitors` list and `custom_dimension_keys` to `AnalysisState`.

## Conditions / Branching Rules
- **No Candidates Discovered Fallback**: If the search loop returns zero new candidates, the synthesizer falls back entirely to the seed list, classifies them based on available intake context, selects standard SaaS dimensions (e.g., `["customer_feedback", "integrations"]`), and proceeds.
- **Direct Transition**: After this node completes, the pipeline transitions to the **Competitor Investigator Phase**.
