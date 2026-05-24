# Node Specification: market_planner (Market Gap Analysis & Planner Node)

## Aim
Analyze the current startup information (sector, business model, target audience) and any existing market data (extracted from the pitch deck) to detect information gaps. If gaps exist and the iteration threshold is not exceeded, the node plans and outputs three distinct search queries with targeted research goals. Otherwise, it marks the planning phase as complete.

## Inputs
- **`PipelineGraphState.analysis_state`** (`AnalysisState`): Specifically accesses:
  - `analysis_state.company` (for sector, business model, and value proposition context)
  - `analysis_state.market` (for existing TAM/SAM/SOM, growth rate, and trends to check completeness)
  - `analysis_state.market.research_sources` (to avoid repeating searches and verify previous research)
- **`PipelineGraphState.market_research_attempts`** (`int`): A counter tracking how many research iterations have run.

## Output Structure (Pydantic Schema)
The node returns a structured planning decision using a model defined in `vs_analyst/schemas/market.py` or similar:
- **`SearchQueryGoal`** (Sub-model):
  - `query` (`str`): A highly specific, search-engine-optimized query targeting a distinct aspect of the market (e.g. market size, growth, macro trends, sector dynamics).
  - `goal` (`str`): The guiding perspective or requirement for the crawler and internal synthesizer (e.g. "Identify the CAGR and its source for the global API security market between 2024 and 2030").
  - `rationale` (`str`): Rationale for this query based on gaps in current state.
- **`MarketPlannerDecision`** (Main model):
  - `status` (`Literal["COMPLETE", "INCOMPLETE"]`): Set to `"COMPLETE"` if no substantial data gaps remain or if maximum attempts are reached. Set to `"INCOMPLETE"` if more research is required.
  - `queries` (`List[SearchQueryGoal]`): List of **exactly 3** distinct queries with goals if `status` is `"INCOMPLETE"`. Must be empty if `status` is `"COMPLETE"`.

## Target Value (State Variables to Update)
This node does not write directly to the persistent `AnalysisState.market` fields (except tracking queries). Instead:
- It outputs a decision that drives the LangGraph router.
- If `status` is `"INCOMPLETE"`, the queries are added to the list of `AnalysisState.market.queries_used`.

## Working Flow
1. **Attempts Check**:
   - Check if `market_research_attempts >= settings.market_research_max_attempts` (default: 2).
   - If true, bypass the LLM and immediately return `{"status": "COMPLETE", "queries": []}`.
2. **Context Setup**:
   - Gather company sector/description, pitch-deck-extracted market claims (`tam`, `sam`, `som`, `growth_rate`, `key_trends`), and any previously gathered `research_sources`.
3. **LLM Gap Assessment**:
   - Invoke the LLM with `.with_structured_output(MarketPlannerDecision)`.
   - The LLM assesses:
     - *Sizing Completeness*: Are TAM, SAM, and SOM values present? Are they backed by sources?
     - *Dynamics Completeness*: Is the growth rate (CAGR) present and sourced? Are there 3–5 distinct trends?
     - *Contradiction Check*: Do initial pitch deck claims clash with raw details or previous research findings?
4. **Structured Decision Return**:
   - Return the Pydantic structured output.

## Conditions / Branching Rules
- **Loop Routing**:
  - If `status == "INCOMPLETE"`, route to the **Parallel Research Executor** (calls the Deep Research Tool on the 3 queries in parallel).
  - If `status == "COMPLETE"`, route to the **Market Synthesizer Node** to build the final market profile.
- **Distinct Query Constraint**:
  - The system prompt strictly enforces that the 3 generated queries must target different aspects (e.g., Query 1: TAM/Market Sizing validation, Query 2: growth rate/market driver, Query 3: industry trends/headwinds). Overlapping or near-identical queries are prohibited.
