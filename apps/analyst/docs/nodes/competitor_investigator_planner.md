# Node Specification: competitor_investigator_planner (Parallel Competitor Investigator Planner)

## Aim
Run in parallel for each competitor identified by the finder. The planner node audits the competitor's profile against the fixed dimensions (funding, geography, business model, strengths) and custom dimensions to identify missing information or weak points. If gaps exist and loop limits are not hit, it plans 1–2 highly targeted search queries using either positive or adversarial search mode.

## Inputs
- **`PipelineGraphState.analysis_state.company`** (`CompanySchema`): For comparison context.
- **`competitor`** (`CompetitorSchema`): The specific competitor profile being analyzed in this branch of the parallel loop (includes existing fields, sources, and queries).
- **`AnalysisState.competitive.custom_dimension_keys`** (`List[str]`): The 2-3 custom dimensions locked by the Finder that must be filled.
- **`competitor_research_attempts`** (`int`): Loop counter tracking iterations *for this specific competitor*.

## Tools Available
None. This is a cognitive-only planning node.

## Output Structure (Pydantic Schema)
The node returns a structured planning decision:
- **`CompetitorInvestigatorDecision`** (defined in `vs_analyst/schemas/competitive.py`):
  - `status` (`Literal["COMPLETE", "INCOMPLETE"]`): Set to `"COMPLETE"` if all required dimensions are populated, or loop limits are hit. Set to `"INCOMPLETE"` if more research is required.
  - `queries` (`List[InvestigatorQueryGoal]`): List of 1–2 research tasks. Must be empty if `status` is `"COMPLETE"`.
    - `query` (`str`): Target search query.
    - `goal` (`str`): specific data extraction instructions for crawler.
    - `tool_mode` (`Literal["positive", "adversarial"]`): Maps to `deep_research_tool` (positive details) or `adversarial_search_tool` (mode="competitor_risk", weaknesses/complaints).

## Target Value (State Variables to Update)
- Appends generated queries to `competitor.queries_used`.
- Writes the decision object to the branch's local state `competitor_planner_decision`.

## Working Flow (Per Competitor Task)
1. **Attempts Check**:
   - Check if `competitor_research_attempts >= settings.competitor_research_max_attempts` (default: 2).
   - If true, return `status = COMPLETE`.
2. **Missing Dimension Audit**:
   - Audit the competitor's profile:
     - Check if fixed dimensions (`funding_stage`, `funding_amount`, `geography`, `business_model`, `founding_year`, `positioning`, `key_strengths`) are empty.
     - Check if custom dimensions in `custom_dimension_keys` are empty.
     - Check if `key_weaknesses` is empty or lacks evidence.
3. **Query Generation**:
   - Generate queries targeting missing dimensions:
     - If positive dimensions (funding, product details) are missing, generate a query with `tool_mode = "positive"`.
     - If weaknesses, customer complaints, or stability risks are missing, generate a query with `tool_mode = "adversarial"`.
     - **Anti-Duplication Guard:** Ensure generated queries have no overlap with `competitor.queries_used`.
4. **Return Decision**:
   - Return the structured Pydantic object.

## Conditions / Branching Rules
- **Loop Routing**:
  - If `status == "INCOMPLETE"`, route to the **Parallel Research Executor** (runs queries via `deep_research_tool` or `adversarial_search_tool`).
  - If `status == "COMPLETE"`, route to the **Competitor Investigator Synthesizer Node** to build the final profile for this competitor.
