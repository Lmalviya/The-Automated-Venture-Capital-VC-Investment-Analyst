from typing import Any, Dict
from pathlib import Path
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.schemas.shared_enums import AgentStatus
from vs_analyst.services.deck_reader import file_extractor

async def intake_extraction_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Intake phase node. Reads pitch deck from disk via services.deck_reader.
    Writes raw_deck_text directly to state. No LLM call — pure Python service.
    """
    analysis_state = state["analysis_state"]
    file_path = Path(analysis_state.user_input.pitch_deck_path)
    result = await file_extractor(file_path, analysis_state.run_id, logger)
    full_text = "\n=========\n".join(
        [f"Page No: {p.page_number}\nContent: {p.text}" for p in result.pages]
    )
    return {"raw_deck_text": full_text}


from vs_analyst.schemas.competitive import CompetitorSchema
from vs_analyst.schemas.founder import Education, FounderSchema
from vs_analyst.schemas.adapters import (
    CompanyAdaptor,
    MarketAdaptor,
    FounderAdaptor,
    FinanceAdaptor,
    CompetitorAdaptor
)
from vs_analyst.prompts import PromptRegistry
from vs_analyst.utility.llm import llm
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

async def extract_company_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Extracts core company information from raw text and maps to state.company.
    """
    raw_text = state.get("raw_deck_text")
    analysis_state = state["analysis_state"]
    if not raw_text:
        return {}

    logger.info("Extracting company details from pitch deck", run_id=analysis_state.run_id)
    structured_llm = llm.with_structured_output(CompanyAdaptor)
    
    prompt = PromptRegistry.deck_company.value.format(TEXT=raw_text)
    result = await structured_llm.ainvoke(prompt)
    
    if result:
        for field in [
            "name", "founding_year", "problem_statement", "solution",
            "website_url", "sector", "geography", "employee_count",
            "business_model", "value_proposition", "product_stage"
        ]:
            val = getattr(result, field, None)
            if val is not None:
                setattr(analysis_state.company, field, val)
                
    return {"analysis_state": analysis_state}


async def extract_market_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Extracts market size estimates (TAM/SAM/SOM) and dynamics from raw text.
    """
    raw_text = state.get("raw_deck_text")
    analysis_state = state["analysis_state"]
    if not raw_text:
        return {}

    logger.info("Extracting market details from pitch deck", run_id=analysis_state.run_id)
    structured_llm = llm.with_structured_output(MarketAdaptor)
    
    prompt = PromptRegistry.deck_market.value.format(TEXT=raw_text)
    result = await structured_llm.ainvoke(prompt)
    
    if result:
        for size_type in ["tam", "sam", "som"]:
            size_adaptor = getattr(result, size_type, None)
            if size_adaptor:
                target_size = getattr(analysis_state.market, size_type)
                for field in ["value", "year", "source", "source_url", "confidence", "notes"]:
                    val = getattr(size_adaptor, field, None)
                    if val is not None:
                        setattr(target_size, field, val)
                        
        for field in ["growth_rate", "growth_source", "key_trends", "market_risks"]:
            val = getattr(result, field, None)
            if val is not None:
                setattr(analysis_state.market, field, val)
                
    return {"analysis_state": analysis_state}


async def extract_founders_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Extracts founder backgrounds and education from raw text.
    """
    raw_text = state.get("raw_deck_text")
    analysis_state = state["analysis_state"]
    if not raw_text:
        return {}

    logger.info("Extracting founder details from pitch deck", run_id=analysis_state.run_id)
    structured_llm = llm.with_structured_output(FounderAdaptor)
    
    prompt = PromptRegistry.deck_founders.value.format(TEXT=raw_text)
    result = await structured_llm.ainvoke(prompt)
    
    if result and getattr(result, "name", None):
        edu_list = []
        if getattr(result, "collage", None) or getattr(result, "level", None):
            edu_list.append(
                Education(
                    collage=getattr(result, "collage", ""),
                    level=getattr(result, "level", ""),
                    branch=getattr(result, "branch", ""),
                    passing_year=getattr(result, "passing_year", None),
                )
            )
            
        exists = any(f.name.lower() == result.name.lower() for f in analysis_state.founders)
        if not exists:
            analysis_state.founders.append(
                FounderSchema(
                    name=result.name,
                    role=getattr(result, "role", None),
                    linkedin_url=getattr(result, "linkedin_url", None),
                    bio_from_deck=getattr(result, "bio_from_deck", None),
                    past_companies=getattr(result, "past_companies", []),
                    past_roles=getattr(result, "past_roles", []),
                    education=edu_list if edu_list else None,
                    notable_achievements=getattr(result, "notable_achievements", []),
                )
            )
            
    return {"analysis_state": analysis_state}


async def extract_financials_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Extracts startup financials, traction, and fundraising details from raw text.
    """
    raw_text = state.get("raw_deck_text")
    analysis_state = state["analysis_state"]
    if not raw_text:
        return {}

    logger.info("Extracting financials and traction from pitch deck", run_id=analysis_state.run_id)
    structured_llm = llm.with_structured_output(FinanceAdaptor)
    
    prompt = PromptRegistry.deck_financials.value.format(TEXT=raw_text)
    result = await structured_llm.ainvoke(prompt)
    
    if result:
        if hasattr(analysis_state.company, "traction"):
            for field in [
                "revenue_monthly", "revenue_annual", "user_count",
                "growth_rate", "key_customers", "other_metrics",
            ]:
                val = getattr(result, field, None)
                if val is not None:
                    setattr(analysis_state.company.traction, field, val)

        if hasattr(analysis_state.company, "funding"):
            for field in ["ask_amount", "valuation", "use_of_funds", "prior_funding"]:
                val = getattr(result, field, None)
                if val is not None:
                    setattr(analysis_state.company.funding, field, val)
                    
    return {"analysis_state": analysis_state}


async def extract_competitors_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Extracts competitors and competitive positioning from raw text.
    """
    raw_text = state.get("raw_deck_text")
    analysis_state = state["analysis_state"]
    if not raw_text:
        return {}

    logger.info("Extracting competitive landscape from pitch deck", run_id=analysis_state.run_id)
    structured_llm = llm.with_structured_output(CompetitorAdaptor)
    
    prompt = PromptRegistry.deck_competitor.value.format(TEXT=raw_text)
    result = await structured_llm.ainvoke(prompt)
    
    if result and getattr(result, "competitors", None):
        analysis_state.competitive.competitors = []
        for c in result.competitors:
            analysis_state.competitive.competitors.append(
                CompetitorSchema(
                    name=c.name,
                    website_url=getattr(c, "website_url", None),
                    competitor_type=getattr(c, "competitor_type", None),
                )
            )
            
    return {"analysis_state": analysis_state}
