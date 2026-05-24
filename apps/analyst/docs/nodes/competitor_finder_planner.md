# Node Specification: competitor_finder_planner (Competitor Discovery Planner Node)

## Aim
Analyze the startup's profile and the current list of competitors in the state to detect discovery gaps. If coverage is insufficient (e.g., fewer than 3-4 qualified competitors identified) and the search threshold is not exceeded, the planner generates 2–3 targeted search queries to discover new competitors. Otherwise, it completes the planning phase.

## Inputs
- **`PipelineGraphState.analysis_state`** (`AnalysisState`):
  - `analysis_state.company` (for sector, value proposition, business model, and ICP context)
  - `analysis_state.competitive.competitors` (to inspect the current set of discovered or seed competitors)
  - `analysis_state.competitive.queries_used` (to audit and prevent query duplication)
- **`PipelineGraphState.competitor_search_attempts`** (`int`): A loop counter tracking search iterations.

## Tools Available
None. This is a cognitive-only planning node.

## Output Structure (Pydantic Schema)
The node returns a structured planning decision:
- **`CompetitorPlannerDecision`** (defined in `vs_analyst/schemas/competitive.py`):
  - `status` (`Literal["COMPLETE", "INCOMPLETE"]`): Set to `"COMPLETE"` if sufficient competitors have been found, or loop limits are hit. Set to `"INCOMPLETE"` if more discovery is required.
  - `queries` (`List[SearchQueryGoal]`): List of 2–3 distinct search queries with crawler goals. Must be empty if `status` is `"COMPLETE"`.

## Target Value (State Variables to Update)
- Appends generated query strings to `AnalysisState.competitive.queries_used`.
- Writes the decision object to `PipelineGraphState.competitor_planner_decision`.

## Working Flow
1. **Attempts Check**:
   - Check if `competitor_search_attempts >= settings.competitor_search_max_attempts` (default: 2).
   - If true, return `status = COMPLETE` and bypass LLM execution.
2. **Coverage Audit**:
   - Evaluate the current competitors in `AnalysisState.competitive.competitors`.
   - If we already have 3+ direct or indirect competitors with high-confidence classifications, and we have searched the core segments, the LLM may decide `status = COMPLETE`.
3. **Query Generation (Anti-Duplication Guard)**:
   - If coverage is insufficient, the LLM generates 2-3 search queries targeting specific alternative types or geographic niches.
   - **Crucial Rule:** The agent must compare new queries against `queries_used` and ensure zero overlap with previously executed search terms.
4. **Structured Decision Return**:
   - Return the Pydantic structured output.

## Conditions / Branching Rules
- **Loop Router**:
  - If `status == "INCOMPLETE"`, route to the **Parallel Research Executor** (runs queries via `deep_research_tool`).
  - If `status == "COMPLETE"`, route directly to the **Competitor Finder Synthesizer Node** to consolidate the candidate pool.
