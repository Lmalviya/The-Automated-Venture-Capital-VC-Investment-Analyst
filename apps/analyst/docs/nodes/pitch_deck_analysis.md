# Phase Specification: Intake Phase (pitch_deck_analysis)

## Aim
Parse the startup's pitch deck, extract raw text using visual and textual extraction tools, and scraped official website text (if a website URL is found or provided) to populate the raw source state variables before any structured analysis or sub-graphs begin.

## Inputs
- **`pitch_deck_path`** (Required, `str`): Absolute path to the startup pitch deck file (typically PDF).
- **`investment_stage`** (Optional, `str`): Target stage (e.g., Seed, Series A).
- **`website_url`** (Optional, `str`): Website URL of the startup.
- **`sector`** (Optional, `str`): Startup sector/industry context.
- **`ask_amount`** (Optional, `str`): Funding request.
- **`geography`** (Optional, `str`): Startup location.

## Target Value (State Variables to Update)
- `PipelineGraphState.raw_deck_text` (`str`): Aggregated raw text extracted from the pitch deck pages.
- `PipelineGraphState.raw_website_text` (`str`): Scraped markdown text from the official website.
- `AnalysisState.user_input` (`UserInputSchema`): Initial state settings populated from the inputs.

## Tool Access
- **`file_to_image`**: Converts a PDF file page-by-page into high-resolution images.
- **`web_crawler`**: Scrapes raw HTML and converts it to clean, readable Markdown/Text.

## Working Flow
1. **Initial Input Binding**: Read the input details and write them into the shared `AnalysisState.user_input` sub-schema.
2. **Pitch Deck Text Extraction**:
   - Use `file_to_image` to convert each slide of the pitch deck into an image.
   - For each slide image, invoke a Vision Language Model (VLM) with an optimized prompt instructing it to extract all readable text, tables, figures, and structural components into a concise Markdown representation.
   - Concatenate all slide texts with clear slide dividers (e.g., `--- Slide [N] ---`) and write the result to `PipelineGraphState.raw_deck_text`.
3. **Website Discovery & Scraping**:
   - Check if `website_url` is provided in the input, OR search `PipelineGraphState.raw_deck_text` using regex or a lightweight LLM check to extract a company website URL.
   - If a valid website URL is found, trigger `web_crawler` to extract up to 5 core pages from the website.
   - Store the clean, scraped content as raw text in `PipelineGraphState.raw_website_text`.
4. **Transition to Company Sub-Graph**:
   - Return control to the parent orchestrator to immediately execute the **Company Sub-Graph**.

## Conditions / Branching Rules
- **No Pitch Deck File**: If `pitch_deck_path` does not exist or fails to open, log a critical error in `AnalysisState.errors` and abort the pipeline.
- **No Website Discovered**: If no website URL is found or crawled, or the crawl fails, leave `PipelineGraphState.raw_website_text` as `None` or empty and continue. Do not raise a critical error.
