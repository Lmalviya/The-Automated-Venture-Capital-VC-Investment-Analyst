# Node Specification: moat_assessment (Competitive Moat & Defensibility Assessment Node)

## Aim
Evaluate the startup's defensible competitive advantages (its "moat") by reasoning over the fully populated competitor profiles alongside the startup's own problem, solution, and value proposition. This is a **pure cognitive synthesis node** — it does not gather new information from the internet. It applies structural defensibility frameworks to produce a grounded, critical moat assessment.

## Inputs
- **`PipelineGraphState.analysis_state`** (`AnalysisState`): Specifically:
  - `analysis_state.company` — problem statement, solution, value proposition, business model, geography, product stage.
  - `analysis_state.competitive.competitors` — fully profiled competitors (fixed + custom dimensions, strengths, weaknesses).
  - `analysis_state.competitive.custom_dimension_keys` — for understanding which sector-specific dimensions were evaluated.
  - `analysis_state.market` — TAM/SAM/SOM context and growth rate for market timing reasoning.

## Tools Available (Utility Only — No Internet Access)
- **`get_current_date`** — Returns today's date. Used for accurate reasoning about founding year gaps, time-to-market, and market timing (e.g., *"Founded in 2018, this competitor has a 6-year head start"*).
- **`calculate_percentage`** — Given two numbers, returns percentage. Used for deriving relative scale (e.g., competitor funding vs. startup's ask, market share estimates).
- **`count_by_type`** — Aggregates the competitive landscape structure (e.g., *"3 Direct, 2 Indirect, 1 Substitute"*) for structured landscape summary.

> **Why utility tools, not internet tools?** Moats are structural properties of a business — they emerge from network effects, switching costs, proprietary data, or cost advantages. These cannot be reliably assessed by searching for the startup's own marketing copy. The LLM must reason over the actual gathered evidence.

## Output Structure (Pydantic Schema)
The node produces a structured moat assessment written directly to state:
- **`MoatAssessmentAdaptor`** (defined in `schemas/adapters.py`):
  - `moat_assessment` (`str`): A 2–3 paragraph critical assessment of the startup's defensible advantages, written for the investment memo. Must reference specific competitor comparisons.
  - `moat_score` (`Literal["STRONG", "MODERATE", "WEAK", "NONE"]`): A structured classification of the overall moat strength.
  - `moat_types_identified` (`List[str]`): Specific moat types identified (e.g., `["Network Effect", "Switching Cost", "Proprietary Data"]`). Empty list if none identified.
  - `moat_risks` (`List[str]`): Structural vulnerabilities in the moat (e.g., *"Network effect only activates above 500 users — current traction is 80 users"*).

## Target Value (State Variables to Update)
- Writes `moat_assessment` to `AnalysisState.competitive.moat_assessment`.

## Working Flow

### Framework Applied: Hamilton's 7 Powers (simplified for VC context)
The LLM prompt instructs the agent to evaluate the startup against these moat categories:

| Moat Type | What to Look For |
| :--- | :--- |
| **Scale Economies** | Does unit cost fall significantly as the company grows? |
| **Network Effects** | Does the product become more valuable as more users join? |
| **Switching Costs** | How painful/expensive is it for a customer to leave? |
| **Proprietary Data** | Does the startup accumulate data that competitors cannot easily replicate? |
| **Brand / Trust** | In this sector, is brand a genuine barrier (e.g., healthcare, finance)? |
| **IP / Patents** | Are there patents or trade secrets that create legal barriers? |
| **Counter-Positioning** | Is the startup's business model one that incumbents cannot copy without disrupting themselves? |

### Reasoning Steps
1. **Landscape Sizing:** Use `count_by_type` to summarize competitive density.
2. **Time Advantage Assessment:** Use `get_current_date` + competitor `founding_year` to compute head-start durations.
3. **Scale Gap Assessment:** Use `calculate_percentage` to compute funding/traction ratios where relevant.
4. **Framework Application:** For each moat category, evaluate the evidence in the gathered data. Write a critical conclusion — not a promotional one.
5. **Output Generation:** Produce the structured `MoatAssessmentAdaptor`.

## Conditions / Branching Rules
- **No Competitors Found (Edge Case)**: If the competitive list is empty, the node must still produce a moat assessment based solely on the startup's description, and explicitly note that no competitive comparison could be made.
- **Transition**: After completion, the pipeline transitions to the **Competitive Risk Analyst Node**.
