# Node Specification: market_risk_analyst (Market Risk Analyst Node)

## Aim
Analyze the synthesized market profile alongside the company's business model to identify critical market-level and company-specific risks. The node uses the specialized `adversarial_search_tool` to hunt for regulatory, operational, defensive, and macro risks, outputting a curated list of threats to update the state.

## Inputs
- **`PipelineGraphState.analysis_state`** (`AnalysisState`): Specifically:
  - `analysis_state.company` (to understand company sector, business model, geography, and operations)
  - `analysis_state.market` (for sizing data, trends, and market summary to contextualize scale and competitive landscape)

## Output Structure (Pydantic Schema)
The node outputs a structured list of risks:
- **`MarketRiskAdaptor`** (defined in `vs_analyst/schemas/adapters.py` or inline):
  - `market_risks` (`List[str]`): A list of 3–5 detailed, specific risk descriptions (e.g., *"High customer concentration with top 3 clients accounting for 60% of regional revenue, posing churn exposure"*).

## Target Value (State Variables to Update)
- Updates `AnalysisState.market.market_risks` (`List[str]`).
- Appends the findings to the existing list or overwrites it with the verified comprehensive set of risks.
- **Important**: Any search queries run by this agent using the adversarial search tool should be appended to `AnalysisState.market.queries_used` for full auditability.

## Working Flow
1. **Risk Identification Planning**:
   - The LLM reviews the company's profile (e.g., a healthcare tech B2B SaaS startup in Germany) and synthesized market trends.
   - It identifies key risk dimensions requiring research, such as:
     - *Regulatory Friction* (e.g., GDPR compliance, local healthcare approvals).
     - *Adoption Barriers* (e.g., long sales cycles, high switching costs).
     - *Defensibility / Competitive Threat* (e.g., low barriers to entry, legacy incumbents).
2. **Adversarial Search Execution**:
   - The agent constructs 1–2 specific risk queries (e.g., *"digital health regulations Germany compliance requirements"*).
   - The agent calls the `adversarial_search_tool` with these queries to search for regulatory hurdles, lawsuits, or compliance threats.
3. **Synthesis & Evaluation**:
   - The agent reviews the search results.
   - It synthesizes the findings into 3–5 major risk statements. The risks must not be generic (e.g., "competitors exist") but highly contextualized to the company's model and sector.
4. **State Writing**:
   - Write the list of risks to `AnalysisState.market.market_risks`.

## Conditions / Branching Rules
- **No Risks Found (Unlikely)**: If no specific adversarial details are found, the agent must still evaluate structural risks (like capital intensity, sales cycles, or technology dependency) and write them based on the company's business model and sector guidelines.
- **End of Market Phase**: Once this node completes, the Market Sub-Graph is complete. The sub-graph exits and returns control to the parent orchestrator for parallel state synchronization.
