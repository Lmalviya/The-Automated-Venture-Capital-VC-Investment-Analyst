# Node Specification: dd_extractor (Due-Diligence Seed Extraction Node)

## Aim
Identify and extract all startup-claimed traction metrics, named press/media mentions, patent applications, regulatory compliances, and active legal/regulatory disputes from the pitch deck and website raw texts. This node acts as the **initial seed extraction step** inside the Due-Diligence Sub-Graph, building the target verification checklist.

## Inputs
- **`PipelineGraphState.raw_deck_text`** (`str`): Raw text extracted from the pitch deck.
- **`PipelineGraphState.raw_website_text`** (`str`, Optional): Scraped text from the official startup website.

## Output Structure (Pydantic Schema)
Expected output must map to a unified **`DueDiligenceAdaptor`** in `vs_analyst/schemas/adapters.py`:
- `traction_claims` (`List[str]`): e.g., `["Hit $100k MRR in Dec 2023", "50k active users"]`.
- `press_claims` (`List[str]`): e.g., `["Featured in TechCrunch", "Named top AI startup by Wired"]`.
- `patents` (`List[str]`): e.g., `["US Patent App 17/123456", "Pending machine learning patent"]`.
- `regulatory_flags` (`List[str]`): e.g., `["FDA clearance required", "HIPAA compliant"]`.
- `legal_notes` (`List[str]`): e.g., `["No active litigation"]`.

## Target Value (State Variables to Update)
- Updates `AnalysisState.due_diligence` (`DueDiligenceSchema` in `vs_analyst/schemas/due_diligence.py`):
  - Sets `due_diligence.regulatory_flags` and `due_diligence.legal_notes` with initial deck claims.
  - Maps `traction_claims` into `due_diligence.traction_checks` as empty work items (`TractionVerification` with `claim` set, `verified = None`, `evidence = None`).
  - Maps `patents` into `due_diligence.patent_mentions`.
  - Maps `press_claims` into `due_diligence.press_mentions` as empty `PressMention` objects.

## Working Flow
1. **Context Synthesis**: Read `raw_deck_text` and `raw_website_text` from the state.
2. **LLM Structured Extraction**: Invoke the LLM with `.with_structured_output(DueDiligenceAdaptor)`.
   - Provide a specialized prompt instructing the LLM to scan for all numerical traction claims, press and logo mentions, patent assertions, regulatory statements (e.g. FDA, HIPAA, GDPR), and legal dispute references.
3. **State Syncing**:
   - For each extracted traction claim, instantiate a `TractionVerification` and append it to `due_diligence.traction_checks`.
   - For each patent claim, append to `due_diligence.patent_mentions`.
   - Write regulatory flags and legal notes directly into the respective lists.
4. **Transition to Parallel Verification Fork**:
   - The sub-graph forks into the parallel validation nodes (`dd_regulatory_planner`, `dd_patent_verifier`, `dd_press_verifier`, `dd_traction_verifier`, `dd_github_fetcher`).

## Conditions / Branching Rules
- **No Claims Found**: If no due-diligence related claims are extracted, leave state lists empty, log a diagnostic note, and transition directly to the parallel verification fork (which will bypass empty checks).
