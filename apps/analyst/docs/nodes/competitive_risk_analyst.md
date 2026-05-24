# Node Specification: competitive_risk_analyst (Competitive Risk Synthesis Node)

## Aim
Synthesize the gathered competitor profiles and the startup's own profile to identify the most critical **competitive-level risks** facing the startup. This is a **pure synthesis node** — it has no tool access and reasons entirely from evidence already gathered during the Investigator phase.

## Scope: What "Competitive Risk" Means Here
This node has a deliberately narrow scope aligned with the overall risk taxonomy of the pipeline:

| Risk Type | Owning Node |
| :--- | :--- |
| Market macro/regulatory risk | `market_risk_analyst` |
| **Competitive landscape risk** | **This node** |
| Founder-level risk | Future `founder_risk_analyst` node |
| Legal/Regulatory/IP risk | Future `due_diligence` node |
| Company-level risk | Future `due_diligence` node |

Competitive-level risks include:
- **Capital Asymmetry Risk** — A competitor has raised significantly more funding and can outspend on growth, sales, or R&D.
- **Pricing Pressure Risk** — One or more competitors offer a free tier, open-source alternative, or significantly lower price point.
- **Geographic Encroachment Risk** — A competitor is actively expanding into the startup's primary geography.
- **Feature Parity Risk** — A larger competitor is adding features that erode the startup's core differentiation.
- **Category Lock-in Risk** — The market is consolidating around a dominant player, creating a winner-take-most dynamic.
- **Structural Unit Economics Risk** — No competitor has achieved profitability in this segment, suggesting a systemic unit economics problem in the market.

## Inputs
- **`PipelineGraphState.analysis_state`** (`AnalysisState`): Specifically:
  - `analysis_state.competitive.competitors` — fully profiled competitors (funding, geography, strengths, weaknesses, custom dimensions).
  - `analysis_state.competitive.moat_assessment` — the moat strength to calibrate risk severity.
  - `analysis_state.company` — startup's current stage, funding, geography, business model.
  - `analysis_state.market` — market growth rate and dynamics for timing context.

## Tools Available (Utility Only — No Internet Access)
- **`get_current_date`** — Temporal baseline for reasoning about how recent a competitive threat is (e.g., *"Competitor A's $80M raise was 3 months ago"*).
- **`years_since(year)`** — Computes competitor maturity to assess how entrenched a rival is in the market.
- **`calculate_percentage(part, whole)`** — Computes capital asymmetry ratios (e.g., startup's $2M vs. competitor's $80M → 2.5% capital parity).
- **`parse_numeric_value(amount_str)`** — Parses multi-currency funding strings before numeric comparison (e.g., `"₹800Cr"`, `"$24M"`).
- **`count_by_competitor_type(competitors_json)`** — Measures competitive density to calibrate overall risk severity.


## Output Structure (Pydantic Schema)
- **`CompetitiveRiskAdaptor`** (defined in `schemas/adapters.py`):
  - `competitive_risk` (`str`): A 2–3 paragraph synthesis identifying the top competitive threats. Must reference specific competitors by name with evidence (e.g., *"Competitor A's $80M Series C in 2024 and their announced expansion into Southeast Asia directly threatens the startup's primary market..."*).
  - `top_risks` (`List[str]`): 3–5 structured, specific risk statements. Each risk must name the threat, the source (competitor or structural), and the impact.
  - `risk_severity` (`Literal["CRITICAL", "HIGH", "MODERATE", "LOW"]`): Overall competitive risk rating.

## Target Value (State Variables to Update)
- Writes `competitive_risk` to `AnalysisState.competitive.competitive_risk`.

## Working Flow

1. **Competitive Landscape Scan:**
   - Review all profiled competitors, focusing on `funding_amount`, `geography`, `key_strengths`, `founding_year`, and `custom_dimensions`.
2. **Risk Category Evaluation:**
   - For each competitive risk type listed in the Scope section, evaluate whether evidence from the competitor profiles supports that risk.
3. **Severity Calibration:**
   - Cross-reference the `moat_assessment` score. A `WEAK` or `NONE` moat amplifies all identified risks.
   - Cross-reference the startup's current funding stage and product maturity against the competitive threats.
4. **Output Generation:**
   - Write the structured `CompetitiveRiskAdaptor`.

## Conditions / Branching Rules
- **Transition**: After completion, the competitive analysis phase is complete. The pipeline transitions to the next phase (e.g., Founder Analysis).

---

> **⚠️ Design Note (Option A Consequence):** This node has no tool access because the adversarial competitor research was intentionally shifted to the `competitor_investigator_planner` node and synthesized by `competitor_investigator_synthesizer`. The negative signals (competitor complaints, stagnation, pricing issues) are already embedded in `key_weaknesses` and `profiling_notes` of each `CompetitorSchema`. If future iterations reveal that this node needs live competitive intelligence (e.g., recent funding news), tool access should be added here rather than expanding the Investigator phase further.
