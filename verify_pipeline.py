import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from pydantic import HttpUrl

from vs_analyst.orchestrator.pipeline import run_pipeline
from vs_analyst.schemas.state import AnalysisState
from vs_analyst.schemas.user_inputs import UserInputSchema, InvestmentStage
from vs_analyst.schemas.adapters import (
    CompanyAdaptor,
    MarketAdaptor,
    FounderAdaptor,
    FinanceAdaptor,
    CompetitorAdaptor
)
from vs_analyst.schemas.market import MarketSize
from vs_analyst.schemas.competitive import CompetitorSchema

# =========================================================
# Mock Objects for LLM Structured Output Response
# =========================================================

mock_company = CompanyAdaptor(
    name="Antigravity AI",
    founding_year=2026,
    problem_statement="AI agent context limits",
    solution="Context preservation and decoupled architectures",
    website_url="https://antigravity.ai",
    sector="Artificial Intelligence",
    geography="Global",
    employee_count="15-50",
    business_model="b2b",
    value_proposition="Wowing users with clean code and premium design",
    product_stage="Beta"
)

mock_market = MarketAdaptor(
    tam=MarketSize(value="100B", year="2026", source="Gartner"),
    sam=MarketSize(value="25B", year="2026", source="Gartner"),
    som=MarketSize(value="2B", year="2026", source="Gartner"),
    growth_rate="35% YoY",
    growth_source="IDC Research",
    key_trends=["Decoupled agents", "Context compaction"],
    market_risks=["API token cost inflation"]
)

mock_founder = FounderAdaptor(
    name="Antigravity Agent",
    role="cto",
    linkedin_url="https://linkedin.com/in/antigravity",
    bio_from_deck="AI assistant specialized in advanced engineering",
    past_companies=["Google DeepMind"],
    past_roles=["Staff Software Engineer"],
    collage="DeepMind Academy",
    level="PhD",
    branch="Computer Science",
    passing_year=2026,
    notable_achievements=["100% correct compaction designs"]
)

mock_finance = FinanceAdaptor(
    revenue_monthly="$120K MRR",
    revenue_annual="$1.4M ARR",
    user_count="5,000 MAU",
    growth_rate="15% MoM",
    key_customers="SaaS Giants, Venture Funds",
    other_metrics=[{"metric": "92% Net Revenue Retention"}],
    ask_amount="$1.5M",
    valuation="$10M Pre-Money",
    use_of_funds=["Expand R&D and engineering team"],
    prior_funding=["Bootstrapped"]
)

mock_competitors = CompetitorAdaptor(
    competitors=[
        {"name": "Legacy Mono-Agent", "website_url": "https://legacy.ai/", "competitor_type": "direct"},
        {"name": "Linear Workflow Parser", "website_url": "https://linear.ai/", "competitor_type": "indirect"}
    ]
)

# Map adaptor schemas to their mock instances
mock_data_map = {
    CompanyAdaptor: mock_company,
    MarketAdaptor: mock_market,
    FounderAdaptor: mock_founder,
    FinanceAdaptor: mock_finance,
    CompetitorAdaptor: mock_competitors
}

# =========================================================
# Custom Mock Structured Runnable
# =========================================================

class MockStructuredRunnable:
    def __init__(self, response_schema):
        self.response_schema = response_schema

    async def ainvoke(self, prompt, config=None, **kwargs):
        # Return the mock schema data mapped above
        return mock_data_map.get(self.response_schema)


def mock_with_structured_output(schema, **kwargs):
    return MockStructuredRunnable(schema)


# =========================================================
# Execution Runner
# =========================================================

async def run_dry_run_verification():
    print("\n" + "="*60)
    print("STARTING DRY-RUN VERIFICATION OF DECOUPLED PIPELINE")
    print("="*60)

    # 1. Instantiate the central AnalysisState
    user_input = UserInputSchema(
        pitch_deck_path=Path("deck.pdf"),
        investment_stage=InvestmentStage.SEED,
        website_url="https://antigravity.ai",
        sector="Artificial Intelligence"
    )

    state = AnalysisState(
        run_id="verification-test-run-123",
        user_input=user_input
    )

    # 2. Prepare Mock Vision/Text outputs for tools
    from vs_analyst.tools.file_extractor import PDFExtractorOutput, ExtractedPage, ExtractionMode
    
    mock_pdf_output = PDFExtractorOutput(
        file_path="deck.pdf",
        file_type="pdf",
        page_count=1,
        total_chars=120,
        pages=[ExtractedPage(page_number=0, mode=ExtractionMode.NORMAL, text="Antigravity AI Pitch Deck content about sector, TAM, and founders.", char_count=60)],
        output={}
    )

    # Setup the patches
    # Patch file_extractor tool logic to bypass actual PDF rendering
    patch_extractor = patch("vs_analyst.tools.file_extractor.file_extractor", return_value=mock_pdf_output)
    
    # Patch the centralized ChatOpenAI class to bypass actual API queries
    from vs_analyst.utility.llm import llm
    patch_llm_structured = patch.object(llm, "with_structured_output", side_effect=mock_with_structured_output)
    
    # Patch ChatOpenAI ainvoke to simulate agent message replies (Intake agent & Market agent)
    # The Intake agent executes, uses file_extractor, then returns tool result.
    # The Market agent executes and returns a mock market analysis message.
    from langchain_core.messages import AIMessage, ToolCall
    
    async def mock_llm_ainvoke(messages, **kwargs):
        # Inspect context to decide which agent is running
        system_msgs = [m for m in messages if hasattr(m, "content") and "system" in getattr(m, "type", "")]
        content_str = "".join([m.content for m in system_msgs])

        if "Intake Manager" in content_str:
            # If pdf extractor hasn't been called yet, trigger it
            has_tool_result = any(getattr(m, "type", "") == "tool" for m in messages)
            if not has_tool_result:
                # Return tool call to extract PDF
                return AIMessage(
                    content="Let me read the pitch deck first using the extractor tool.",
                    tool_calls=[{
                        "name": "pdf_extractor_tool",
                        "args": {"file_path": "deck.pdf", "run_id": "verification-test-run-123"},
                        "id": "call_123"
                    }]
                )
            else:
                # After tool executes, trigger routing completion
                return AIMessage(content="Perfect! The raw text has been saved. Transitioning to structured extraction.")
        
        elif "Market Research Manager" in content_str:
            # Market agent phase - just complete
            return AIMessage(content="Market research complete! Evaluated TAM/SAM/SOM growth rate at 35% YoY.")
            
        return AIMessage(content="Simulated complete.")

    patch_llm_ainvoke = patch.object(llm, "ainvoke", side_effect=mock_llm_ainvoke)

    # 3. Apply patches and execute the pipeline
    with patch_extractor, patch_llm_structured, patch_llm_ainvoke:
        final_state = await run_pipeline(state)

    print("\n" + "="*60)
    print("DRY RUN COMPLETED SUCCESSFULLY!")
    print("="*60)

    print(f"\nCompany Structured Name: {final_state.company.name}")
    print(f"Founder Role: {final_state.founders[0].name} ({final_state.founders[0].role})")
    print(f"TAM Value: {final_state.market.tam.value} (Source: {final_state.market.tam.source})")
    print(f"Competitors Count: {len(final_state.competitive.competitors)}")
    print(f"Agent Statuses: {final_state.agent_statuses}")
    print(f"Overall Pipeline Status: {final_state.status}")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_dry_run_verification())
