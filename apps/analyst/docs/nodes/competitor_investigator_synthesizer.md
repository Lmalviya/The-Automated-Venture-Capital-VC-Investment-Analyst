# Node Specification: competitor_investigator_synthesizer (Parallel Competitor Investigator Synthesizer)

## Aim
Consolidate positive and adversarial research findings gathered for a specific competitor. The synthesizer node parses raw data, resolves information conflicts, calculates key temporal and financial metrics using cognitive utility tools, and returns a fully populated, structured competitor profile.

## Inputs
- **`PipelineGraphState.analysis_state.company`** (`CompanySchema`): For baseline funding and timeline context.
- **`competitor`** (`CompetitorSchema`): The competitor object being profiled, containing raw research summaries (`competitor.research_sources`) and custom dimension keys.
- **`AnalysisState.competitive.custom_dimension_keys`** (`List[str]`): The keys to fill in `competitor.custom_dimensions`.

## Tools Available (Utility Only — No Internet Access)
- **`get_current_date`** — Baseline for calculating age or event recency.
- **`years_since(year)`** — Computes competitor operating years.
- **`parse_numeric_value(amount_str)`** — Converts multi-currency funding values into raw numbers for comparison.
- **`calculate_percentage(part, whole)`** — Computes capital discrepancies.

## Output Structure
Returns a fully populated **`CompetitorSchema`** (defined in `vs_analyst/schemas/competitive.py`):
- **Fixed Dimensions**:
  - `name` (`str`)
  - `website_url` (`Optional[HttpUrl]`)
  - `competitor_type` (`CompetitorType`)
  - `funding_stage` (`str`, e.g., "Series A")
  - `funding_amount` (`str`, e.g., "$12M")
  - `geography` (`str`)
  - `business_model` (`str`)
  - `founding_year` (`int`)
  - `positioning` (`str`)
  - `key_strengths` (`List[str]`): 2–4 verified strengths.
  - `key_weaknesses` (`List[str]`): 2–4 vulnerabilities/complaints found via adversarial search.
- **Custom Dimensions** (`dict[str, str]`): Must contain a value for each key in `custom_dimension_keys`.
- **Sources** (`List[ResearchSource]`): Inline citation reference list.
- **Profiling Notes** (`List[str]`): Context notes on ambiguities or low-confidence details.

## Working Flow
1. **Source Aggregation**:
   - Collect and read the competitor's raw `research_sources`.
2. **Conflict Resolution**:
   - Reconcile differences between source materials (e.g. different funding stage reports). Prioritize verified databases (Crunchbase, Pitchbook summaries) over marketing positioning.
3. **Deterministic Utility Calls**:
   - Convert funding amounts using `parse_numeric_value` if needed for comparison.
   - Run `years_since(founding_year)` to determine company age.
4. **Dimension Completion**:
   - Map findings into the fixed dimensions.
   - For every key in `custom_dimension_keys`, populate the corresponding slot in `competitor.custom_dimensions`. If research yielded no information, explicitly write `"Not found"`.
5. **State Return**:
   - Return the finalized `CompetitorSchema` to be collected in the Reduce step.

## Conditions / Branching Rules
- **Direct Transition**: The finalized competitor schema is returned. Once all parallel competitor branches complete, the orchestrator collects and merges them, then transitions the graph to the **Moat Assessment Node**.
