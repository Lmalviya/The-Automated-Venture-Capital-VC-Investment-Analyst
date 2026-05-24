# Tool Specification: Cognitive Utility Tools (Stateless Computation Tools)

## Purpose
These are stateless, deterministic, **zero-network** tools designed to eliminate hallucination-prone computations from LLM reasoning. They act as a reliable "calculator layer" for any node that requires mathematical, temporal, or structural aggregation — without granting any internet access.

These tools are available to the `moat_assessment` node. Other synthesis nodes may be granted access in future iterations.

---

## 1. `get_current_date`

### Aim
Return the current date in ISO 8601 format (`YYYY-MM-DD`). This is critical because LLMs have a fixed training cutoff and will hallucinate the current year if asked without grounding.

### Inputs
None.

### Output
```json
{ "date": "2025-05-24" }
```

### Use Cases
- Establishing an accurate temporal baseline before computing any time-based reasoning (e.g., competitor founding age, market timing).

---

## 2. `years_since`

### Aim
Given a year (integer), return the number of complete years elapsed since that year up to today. Prevents the LLM from performing its own date subtraction, which is error-prone when the training cutoff year differs from the actual current year.

### Inputs
- **`year`** (`int`): The reference year (e.g., a competitor's founding year, e.g., `2017`).

### Output
```json
{ "years_elapsed": 8 }
```

### Use Cases
- *"Competitor A was founded in 2017 — how many years of head start do they have?"*
- *"The startup was founded in 2022 — how mature is this company?"*

---

## 3. `calculate_percentage`

### Aim
Given a `part` and a `whole`, return the percentage that `part` represents of `whole`, rounded to 2 decimal places. Eliminates LLM arithmetic errors in comparative analysis.

### Inputs
- **`part`** (`float`): The numerator value (e.g., a startup's funding amount).
- **`whole`** (`float`): The denominator value (e.g., the largest competitor's funding amount).

### Output
```json
{ "percentage": 8.33 }
```

### Use Cases
- *"The startup has raised $2M. The lead competitor raised $24M. What is the capital ratio?"* → `calculate_percentage(2_000_000, 24_000_000)` → `8.33%`.
- Computing estimated market share given TAM and revenue estimates.

---

## 4. `parse_numeric_value`

### Aim
Extract and normalize a numeric value from a human-readable financial string. Handles common suffixes (`K`, `M`, `B`, `Cr`, `L`) and currency symbols (`$`, `€`, `£`, `₹`). Returns both the raw numeric value (as a float in base units) and the detected currency code.

LLMs regularly misparse financial strings — especially Indian notation (`Cr` for Crore, `L` for Lakh), confuse `M` (million) with other units, and make errors when mixing currencies. This tool resolves those reliably.

### Inputs
- **`amount_str`** (`str`): Human-readable financial string (e.g., `"$24M"`, `"₹800Cr"`, `"€5.5M"`, `"£2B"`).

### Output
```json
{
  "numeric_value": 24000000.0,
  "currency_code": "USD",
  "original_string": "$24M"
}
```

### Suffix Conversion Table
| Suffix | Multiplier | Notes |
| :--- | :--- | :--- |
| `K` | 1,000 | Thousands |
| `M` | 1,000,000 | Millions |
| `B` | 1,000,000,000 | Billions |
| `L` | 100,000 | Indian Lakh |
| `Cr` | 10,000,000 | Indian Crore |

### Currency Detection
| Symbol | Code |
| :--- | :--- |
| `$` | USD |
| `€` | EUR |
| `£` | GBP |
| `₹` | INR |
| No symbol | UNKNOWN |

### Use Cases
- Parsing `"$24M"` before passing to `calculate_percentage`.
- Comparing two funding amounts in the same currency.

> **⚠️ Important Constraint:** This tool does **not** perform currency conversion. If the startup's ask is in USD and a competitor's funding is in EUR, the LLM must note the currency mismatch explicitly and avoid a direct numeric comparison. Cross-currency comparisons require a live exchange rate, which is outside the scope of utility tools.

---

## 5. `count_by_competitor_type`

### Aim
Given a JSON array of competitor objects (each with a `competitor_type` field), return a structured count breakdown by `CompetitorType`. Ensures the competitive landscape summary is deterministic rather than approximated.

### Inputs
- **`competitors_json`** (`str`): A JSON string containing a list of competitor objects, each with at minimum a `competitor_type` field.
  ```json
  [
    { "name": "Acme Corp", "competitor_type": "direct" },
    { "name": "BetaCo",   "competitor_type": "indirect" },
    { "name": "GammaInc", "competitor_type": "direct" }
  ]
  ```

### Output
```json
{
  "total": 3,
  "direct": 2,
  "indirect": 1,
  "emerging": 0,
  "substitute": 0
}
```

### Use Cases
- *"Summarize the competitive landscape before starting moat analysis."*
- Giving the LLM a structured count to reference in the moat assessment narrative.

---

## Integration Guidelines
All five tools are **stateless**: they take inputs, compute outputs, and return results. They do not read or write to graph state. They may be granted to any synthesis or analysis node that needs deterministic computation — they never grant internet access.

### Node Access Matrix

| Tool | `moat_assessment` | `competitive_risk_analyst` | `market_synthesizer` | `venture_partner_ic_agent` |
| :--- | :---: | :---: | :---: | :---: |
| `get_current_date` | ✅ | ✅ | ❌ | ❌ |
| `years_since` | ✅ | ✅ | ❌ | ❌ |
| `calculate_percentage` | ✅ | ✅ | ✅ | ✅ |
| `parse_numeric_value` | ✅ | ✅ | ✅ | ❌ |
| `count_by_competitor_type` | ✅ | ✅ | ❌ | ❌ |

### Rationale Per Node

**`moat_assessment`:** Needs all five tools. Founding year gaps (`years_since`), funding ratio comparisons (`calculate_percentage` + `parse_numeric_value`), landscape density summary (`count_by_competitor_type`), and a temporal baseline (`get_current_date`).

**`competitive_risk_analyst`:** Needs all five tools. Capital asymmetry risk requires parsing multi-currency funding strings (`parse_numeric_value`), computing ratios (`calculate_percentage`), assessing competitor maturity (`years_since` + `get_current_date`), and understanding competitive density (`count_by_competitor_type`) to calibrate risk severity.

**`market_synthesizer`:** Needs only the numeric tools. When resolving discrepancies between founder-claimed TAM (`"₹800Cr"`) and independently researched TAM (`"$4B"`), the synthesizer must parse both values (`parse_numeric_value`) and compute the discrepancy ratio (`calculate_percentage`). It does not need temporal or competitor-counting tools.

**`venture_partner_ic_agent`:** Needs only `calculate_percentage`. When synthesizing the Advocate and Adversary briefs into a final verdict, the IC agent may express the conviction rationale using ratio computations (e.g., *"Verified traction covers only 40% of the claimed MRR figure"*). All other dimensions are handled by pure LLM reasoning over the state data.

