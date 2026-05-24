# Node Specification: deck_to_founder (Founder Extraction Node)

## Aim
Extract biographical, educational, professional history, and social signals of the founding team members from the aggregated raw data and structure it into the state graph.

## Inputs
- **`PipelineGraphState.raw_deck_text`** (`str`): Raw text extracted from the pitch deck.
- **`PipelineGraphState.raw_website_text`** (`str`, Optional): Scraped text from the official startup website.

## Output Structure (Pydantic Schema)
Expected output must map to **`FounderAdaptor`** in `vs_analyst/schemas/adapters.py`:
- `name` (`str`)
- `role` (`FounderRole` enum)
- `linkedin_url` (`HttpUrl`)
- `bio_from_deck` (`str`)
- `past_companies` (`List[str]`)
- `past_roles` (`List[str]`)
- `collage` (`str`)
- `level` (`str`)
- `branch` (`str`)
- `passing_year` (`int`)
- `notable_achievements` (`List[str]`)

## Target Value (State Variables to Update)
- Appends to or updates `AnalysisState.founders` (`List[FounderSchema]` in `vs_analyst/schemas/founder.py`).
- Specifically constructs a `FounderSchema` which includes a nested `List[Education]` schema populated from the adapter's college/level/branch/passing_year fields.

## Working Flow
1. **Context Synthesis:** Read `raw_deck_text` and `raw_website_text` from the state.
2. **LLM Structured Extraction:** Invoke the LLM using `.with_structured_output(FounderAdaptor)`. 
   - Note: Since a company usually has multiple founders, the prompt instructs the LLM to identify all distinct human profiles mentioned as founders, advisors, or key executives and return a list of profiles.
3. **De-duplication & Merging:**
   - For each extracted founder profile, check if a founder with the same case-insensitive name already exists in `AnalysisState.founders`.
   - If the founder does not exist: create a new `FounderSchema`, build the nested `Education` object from the college details, and append to `AnalysisState.founders`.
   - If the founder already exists: merge empty or missing fields from the new adapter into the existing state object to avoid losing historic information.
4. **Summary Return:** Return a short summary listing the identified founders and their roles (e.g., *"Extracted 2 founders: Jane Doe (CEO) and John Smith (CTO)"*).

## Conditions / Branching Rules
- **No Founders Identified:** If the LLM does not extract any founder schemas, append a warning log to `AnalysisState.company.extracted_notes` indicating "No founder profiles found in intake content."
- **Multiple Education Degrees:** If a founder profile has multiple educational backgrounds, consolidate key degrees or list the highest level (PG/PhD) degree in the single `Education` block, logging other details in `notable_achievements`.
