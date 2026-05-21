
from vs_analyst.schemas.state import AnalysisState
from vs_analyst.schemas.founder import Education, FounderSchema
from vs_analyst.schemas.competitive import CompetitorSchema
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

# =========================================================
# Private State Mapping Helper
# =========================================================

def _map_intake_output_to_state(run_id: str, analysis_state: AnalysisState) -> None:
    """
    Reads the full PDFExtractorOutput from the extraction cache and maps
    all structured fields into the central AnalysisState.

    This runs AFTER the intake agent is done — never inside the LLM loop.

    TODO: The _extraction_cache approach will be revisited with the user.
          A better state-passing mechanism may replace this in future.
    """
    from vs_analyst.tools.file_extractor import _extraction_cache

    result = _extraction_cache.get(run_id)
    if result is None:
        logger.warning("No extraction cache entry found", run_id=run_id)
        return

    raw_output = result.output

    # 1. Company Identity (deck_company)
    company_data = raw_output.get("deck_company")
    if company_data and hasattr(company_data, "__dict__"):
        try:
            for field in [
                "name", "founding_year", "problem_statement", "solution",
                "website_url", "sector", "geography", "employee_count",
                "business_model", "value_proposition", "product_stage",
            ]:
                val = getattr(company_data, field, None)
                if val is not None:
                    setattr(analysis_state.company, field, val)
        except Exception as e:
            logger.error("Failed mapping company identity", error=str(e))

    # 2. Financials & Traction (deck_financials)
    fin_data = raw_output.get("deck_financials")
    if fin_data and hasattr(fin_data, "__dict__"):
        try:
            if hasattr(analysis_state.company, "traction"):
                for field in [
                    "revenue_monthly", "revenue_annual", "user_count",
                    "growth_rate", "key_customers", "other_metrics",
                ]:
                    val = getattr(fin_data, field, None)
                    if val is not None:
                        setattr(analysis_state.company.traction, field, val)

            if hasattr(analysis_state.company, "funding"):
                for field in ["ask_amount", "valuation", "use_of_funds", "prior_funding"]:
                    val = getattr(fin_data, field, None)
                    if val is not None:
                        setattr(analysis_state.company.funding, field, val)
        except Exception as e:
            logger.error("Failed mapping financials", error=str(e))

    # 3. Founders (deck_founders)
    founder_data = raw_output.get("deck_founders")
    if founder_data and hasattr(founder_data, "name"):
        try:
            edu_list = []
            if getattr(founder_data, "collage", None) or getattr(founder_data, "level", None):
                edu_list.append(
                    Education(
                        collage=getattr(founder_data, "collage", ""),
                        level=getattr(founder_data, "level", ""),
                        branch=getattr(founder_data, "branch", ""),
                        passing_year=getattr(founder_data, "passing_year", None),
                    )
                )
            analysis_state.founders.append(
                FounderSchema(
                    name=founder_data.name,
                    role=getattr(founder_data, "role", None),
                    linkedin_url=getattr(founder_data, "linkedin_url", None),
                    bio_from_deck=getattr(founder_data, "bio_from_deck", None),
                    past_companies=getattr(founder_data, "past_companies", []),
                    past_roles=getattr(founder_data, "past_roles", []),
                    education=edu_list if edu_list else None,
                    notable_achievements=getattr(founder_data, "notable_achievements", []),
                )
            )
        except Exception as e:
            logger.error("Failed mapping founders", error=str(e))

    # 4. Market (deck_market)
    market_data = raw_output.get("deck_market")
    if market_data and hasattr(market_data, "__dict__"):
        try:
            for size_type in ["tam", "sam", "som"]:
                size_adaptor = getattr(market_data, size_type, None)
                if size_adaptor:
                    target_size = getattr(analysis_state.market, size_type)
                    for field in ["value", "year", "source", "source_url", "confidence", "notes"]:
                        val = getattr(size_adaptor, field, None)
                        if val is not None:
                            setattr(target_size, field, val)

            for field in ["growth_rate", "growth_source", "key_trends", "market_risks"]:
                val = getattr(market_data, field, None)
                if val is not None:
                    setattr(analysis_state.market, field, val)
        except Exception as e:
            logger.error("Failed mapping market dynamics", error=str(e))

    # 5. Competitors (deck_competitor)
    comp_data = raw_output.get("deck_competitor")
    if comp_data and hasattr(comp_data, "competitors"):
        try:
            analysis_state.competitive.competitors = []
            for c in comp_data.competitors:
                analysis_state.competitive.competitors.append(
                    CompetitorSchema(
                        name=c.name,
                        website_url=getattr(c, "website_url", None),
                        competitor_type=getattr(c, "competitor_type", None),
                    )
                )
        except Exception as e:
            logger.error("Failed mapping competitive landscape", error=str(e))

    # Clear cache entry after mapping
    _extraction_cache.pop(run_id, None)
    logger.info("Intake output successfully mapped to AnalysisState", run_id=run_id)

