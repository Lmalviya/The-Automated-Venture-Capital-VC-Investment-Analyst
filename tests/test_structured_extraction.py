import pytest
import asyncio
from unittest.mock import patch, MagicMock
from pydantic import BaseModel

from vs_analyst.tools.file_extractor import (
    run_parallel_extraction,
    ExtractedPage,
    ExtractionMode
)
from vs_analyst.schemas.adapters import (
    CompanyAdaptor,
    MarketAdaptor,
    FounderAdaptor,
    FinanceAdaptor,
    CompetitorAdaptor,
    OverviewAdaptor
)

@pytest.mark.anyio
async def test_run_parallel_extraction():
    """
    Test that run_parallel_extraction invokes query_structured_model for all tasks
    and maps the results to the correct schemas under parallel execution.
    """
    # 1. Prepare mock return values for each of the schemas
    mock_company = CompanyAdaptor(
        name="Antigravity AI",
        founding_year=2026,
        problem_statement="AI agent context size limits",
        solution="Extreme agent compression and pair programming support",
        value_proposition="Wowing users with premium design and clean architecture",
        product_stage="Beta"
    )
    
    from vs_analyst.schemas.market import MarketSize
    mock_market = MarketAdaptor(
        tam=MarketSize(value="50B"),
        sam=MarketSize(value="10B"),
        som=MarketSize(value="1B"),
        key_trends=["Agentic workflow adoption", "Local IDE integration"]
    )
    
    mock_founders = FounderAdaptor(
        name="Antigravity Agent",
        collage="DeepMind University",
        level="PhD",
        branch="Computer Science"
    )
    
    mock_financials = FinanceAdaptor(
        ask_amount="$2M",
        valuation="$10M pre-money"
    )
    
    mock_competitor = CompetitorAdaptor(competitors=[])
    
    mock_summary = OverviewAdaptor(
        page_number=1,
        section_type="company_overview",
        summary="A high performance agent."
    )
    
    # Dictionary mapping requested schema to its mock response
    schema_mock_map = {
        CompanyAdaptor: mock_company,
        MarketAdaptor: mock_market,
        FounderAdaptor: mock_founders,
        FinanceAdaptor: mock_financials,
        CompetitorAdaptor: mock_competitor,
        OverviewAdaptor: mock_summary,
    }
    
    # 2. Custom mock function to return correct schema based on the response_format passed to query_structured_model
    def mock_query_structured(messages, response_format, log):
        return schema_mock_map[response_format]
        
    # 3. Patch query_structured_model in file_extractor
    with patch("vs_analyst.tools.file_extractor.query_structured_model", side_effect=mock_query_structured) as mock_query:
        # Define dummy pages to pass to parallel extractor
        dummy_pages = [
            ExtractedPage(
                page_number=1,
                mode=ExtractionMode.NORMAL,
                text="Antigravity AI: Pitch Deck Page 1 text content."
            )
        ]
        
        # 4. Invoke parallel extraction
        mock_log = MagicMock()
        results = await run_parallel_extraction(dummy_pages, mock_log)
        
        # 5. Assert all expected extractions are present
        assert "deck_company" in results
        assert "deck_market" in results
        assert "deck_founders" in results
        assert "deck_financials" in results
        assert "deck_competitor" in results
        assert "deck_summary" in results
        
        # 6. Verify types and fields match mock inputs
        assert isinstance(results["deck_company"], CompanyAdaptor)
        assert results["deck_company"].name == "Antigravity AI"
        assert results["deck_company"].founding_year == 2026
        
        assert isinstance(results["deck_market"], MarketAdaptor)
        assert results["deck_market"].tam.value == "50B"
        
        assert isinstance(results["deck_founders"], FounderAdaptor)
        assert results["deck_founders"].name == "Antigravity Agent"
        
        assert isinstance(results["deck_financials"], FinanceAdaptor)
        assert results["deck_financials"].ask_amount == "$2M"
        
        assert isinstance(results["deck_competitor"], CompetitorAdaptor)
        assert len(results["deck_competitor"].competitors) == 0
        
        assert isinstance(results["deck_summary"], OverviewAdaptor)
        assert results["deck_summary"].section_type == "company_overview"
        
        # Assert query_structured_model was called exactly 6 times (once for each section in parallel)
        assert mock_query.call_count == 6
