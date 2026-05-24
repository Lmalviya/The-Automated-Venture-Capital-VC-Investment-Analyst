from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.state import AnalysisState
from vs_analyst.schemas.due_diligence import TractionVerification
from vs_analyst.schemas.shared_models import PressMention
from vs_analyst.tools.deep_research import deep_research_tool
from vs_analyst.tools.market_tools import web_search_tool
from vs_analyst.utility.llm import llm
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


# =========================================================
# Structured Output Pydantic Models for Verifiers
# =========================================================

class LegalVerificationResult(BaseModel):
    regulatory_flags: List[str] = Field(default_factory=list, description="Verified regulatory flags or compliance gaps found")
    legal_notes: List[str] = Field(default_factory=list, description="Verified legal notes or lawsuit findings")
    patent_mentions: List[str] = Field(default_factory=list, description="Verified patent or patent applications details found")


class VerifiedTractionClaim(BaseModel):
    claim: str = Field(..., description="Stated deck traction claim")
    verified: Optional[bool] = Field(..., description="True if verified, False if refuted, None if uncorroborated")
    evidence: str = Field(..., description="Detailed verification evidence or research notes")
    source_url: Optional[str] = Field(None, description="URL of verifying source")


class TractionVerificationResult(BaseModel):
    verifications: List[VerifiedTractionClaim] = Field(default_factory=list, description="Traction verifications results list")


class VerifiedPressMention(BaseModel):
    title: str = Field(..., description="Press claim or article headline under verification")
    url: Optional[str] = Field(None, description="URL of article")
    source: Optional[str] = Field(None, description="Featured publication, e.g. TechCrunch")
    date: Optional[str] = Field(None, description="Date of article")
    sentiment: Optional[str] = Field(None, description="Sentiment: positive, neutral, or negative")
    snippet: Optional[str] = Field(None, description="Short snippet cap 300 chars")


class PressVerificationResult(BaseModel):
    press_mentions: List[VerifiedPressMention] = Field(default_factory=list, description="List of verified press articles")
    press_summary: str = Field(..., description="Cohesive synthesis of media coverage footprint and sentiment tone")


# =========================================================
# Node 1: dd_legal_verifier_node
# =========================================================

async def dd_legal_verifier_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parallel Legal & Regulatory Verifier Node.
    Verifies incorporation standing, licenses, compliance and lawsuits.
    Conforms to due_diligence_sub_graph.md and Phase 6 specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Due-Diligence Legal Verifier node started", run_id=analysis_state.run_id)

    due_diligence = analysis_state.due_diligence
    company = analysis_state.company

    # 1. Prepare context for ReAct Agent
    context = (
        f"Target Startup:\n"
        f"Company Name: {company.name or 'N/A'}\n"
        f"Sector: {company.sector or 'N/A'}\n"
        f"HQ Location: {company.geography or 'N/A'}\n\n"
        f"Stated Regulatory Claims: {due_diligence.regulatory_flags}\n"
        f"Stated Legal Notes: {due_diligence.legal_notes}\n"
        f"Stated Patents: {due_diligence.patent_mentions}\n"
    )

    messages = [
        SystemMessage(content=PromptRegistry.dd_legal_verifier_system.value),
        HumanMessage(content=f"Verify corporate legitimacy, operating licenses, compliance standards and lawsuits for {company.name or 'the startup'}.\n\nContext Details:\n{context}")
    ]

    try:
        # ReAct loop (Up to 3 steps)
        for step in range(3):
            response = await AgentRegistry.dd_legal_verifier.ainvoke(messages)
            messages.append(response)

            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:
                if tool_call["name"] == "deep_research_tool":
                    args = tool_call["args"]
                    tool_result = await deep_research_tool.ainvoke(args)
                    messages.append(
                        ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"], name=tool_call["name"])
                    )

        # Parse findings structurally
        parser = llm.with_structured_output(LegalVerificationResult)
        result = await parser.ainvoke([
            SystemMessage(content="You are a data extraction assistant. Map legal findings to schemas."),
            HumanMessage(content=f"Parse the following legal research findings for {company.name or 'the startup'} into structured format:\n\n{messages[-1].content}")
        ])

        if result:
            logger.info("Legal verification findings parsed successfully", run_id=analysis_state.run_id)
            due_diligence.regulatory_flags = list(set(due_diligence.regulatory_flags + result.regulatory_flags))
            due_diligence.legal_notes = list(set(due_diligence.legal_notes + result.legal_notes))
            due_diligence.patent_mentions = list(set(due_diligence.patent_mentions + result.patent_mentions))

    except Exception as e:
        logger.error("Error in Legal Verifier node", run_id=analysis_state.run_id, error=str(e))

    # Build parent state update
    parent_update = AnalysisState(
        run_id=analysis_state.run_id,
        user_input=analysis_state.user_input,
        created_at=analysis_state.created_at
    )
    parent_update.due_diligence = due_diligence

    return {"analysis_state": parent_update}


# =========================================================
# Node 2: dd_traction_verifier_node
# =========================================================

async def dd_traction_verifier_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parallel Traction Verifier Node.
    Cross-checks numerical traction claims, user metrics and ARR.
    Conforms to due_diligence_sub_graph.md and Phase 6 specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Due-Diligence Traction Verifier node started", run_id=analysis_state.run_id)

    due_diligence = analysis_state.due_diligence
    company = analysis_state.company

    if not due_diligence.traction_checks:
        logger.info("No traction claims to verify in state.", run_id=analysis_state.run_id)
        return {"analysis_state": analysis_state}

    # 1. Compile context
    claims_list = [check.claim for check in due_diligence.traction_checks]
    context = (
        f"Target Startup Name: {company.name or 'N/A'}\n"
        f"Sector: {company.sector or 'N/A'}\n"
        f"ICP/Value Prop: {company.value_proposition or 'N/A'}\n\n"
        f"Stated Traction claims to check:\n"
        f"{claims_list}\n"
    )

    messages = [
        SystemMessage(content=PromptRegistry.dd_traction_verifier_system.value),
        HumanMessage(content=f"Verify these numerical and growth claims for {company.name or 'the startup'}.\n\nContext:\n{context}")
    ]

    try:
        # ReAct loop (Up to 3 steps)
        for step in range(3):
            response = await AgentRegistry.dd_traction_verifier.ainvoke(messages)
            messages.append(response)

            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:
                if tool_call["name"] == "deep_research_tool":
                    args = tool_call["args"]
                    tool_result = await deep_research_tool.ainvoke(args)
                    messages.append(
                        ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"], name=tool_call["name"])
                    )

        # Parse findings structurally
        parser = llm.with_structured_output(TractionVerificationResult)
        result = await parser.ainvoke([
            SystemMessage(content="You are a precise parsing assistant. Map traction audit findings to schemas."),
            HumanMessage(content=f"Parse the following traction audit findings for {company.name or 'the startup'} into structured verifications:\n\n{messages[-1].content}")
        ])

        if result and result.verifications:
            logger.info("Traction verification findings parsed successfully", run_id=analysis_state.run_id)
            
            # Map back to state
            for v in result.verifications:
                for target in due_diligence.traction_checks:
                    if target.claim.lower() in v.claim.lower() or v.claim.lower() in target.claim.lower():
                        target.verified = v.verified
                        target.evidence = v.evidence
                        if v.source_url:
                            target.source_url = HttpUrl(v.source_url)

    except Exception as e:
        logger.error("Error in Traction Verifier node", run_id=analysis_state.run_id, error=str(e))

    # Build parent state update
    parent_update = AnalysisState(
        run_id=analysis_state.run_id,
        user_input=analysis_state.user_input,
        created_at=analysis_state.created_at
    )
    parent_update.due_diligence = due_diligence

    return {"analysis_state": parent_update}


# =========================================================
# Node 3: dd_press_verifier_node
# =========================================================

async def dd_press_verifier_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parallel Press Verifier Node.
    Verifies public media articles footprint and sentiment.
    Conforms to due_diligence_sub_graph.md and Phase 6 specs.
    """
    analysis_state = state["analysis_state"]
    logger.info("Due-Diligence Press Verifier node started", run_id=analysis_state.run_id)

    due_diligence = analysis_state.due_diligence
    company = analysis_state.company

    if not due_diligence.press_mentions:
        logger.info("No press claims to verify in state.", run_id=analysis_state.run_id)
        return {"analysis_state": analysis_state}

    # 1. Compile context
    claims_list = [mention.title for mention in due_diligence.press_mentions]
    context = (
        f"Target Startup Name: {company.name or 'N/A'}\n"
        f"Featured publication claims:\n"
        f"{claims_list}\n"
    )

    messages = [
        SystemMessage(content=PromptRegistry.dd_press_verifier_system.value),
        HumanMessage(content=f"Verify these press and media assertions for {company.name or 'the startup'}.\n\nContext:\n{context}")
    ]

    try:
        # ReAct loop (Up to 3 steps)
        for step in range(3):
            response = await AgentRegistry.dd_press_verifier.ainvoke(messages)
            messages.append(response)

            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:
                if tool_call["name"] == "web_search_tool":
                    args = tool_call["args"]
                    tool_result = await web_search_tool.ainvoke(args)
                    messages.append(
                        ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"], name=tool_call["name"])
                    )

        # Parse findings structurally
        parser = llm.with_structured_output(PressVerificationResult)
        result = await parser.ainvoke([
            SystemMessage(content="You are a precise media footprint parser. Map press audit findings to schemas."),
            HumanMessage(content=f"Parse the following press audit findings for {company.name or 'the startup'} into structured press mentions:\n\n{messages[-1].content}")
        ])

        if result:
            logger.info("Press verification findings parsed successfully", run_id=analysis_state.run_id)
            
            # Map back to state
            due_diligence.press_summary = result.press_summary
            
            verified_mentions = []
            for v in result.press_mentions:
                verified_mentions.append(
                    PressMention(
                        title=v.title,
                        url=HttpUrl(v.url) if v.url else None,
                        source=v.source,
                        date=v.date,
                        sentiment=v.sentiment,
                        snippet=v.snippet
                    )
                )
            due_diligence.press_mentions = verified_mentions

    except Exception as e:
        logger.error("Error in Press Verifier node", run_id=analysis_state.run_id, error=str(e))

    # Build parent state update
    parent_update = AnalysisState(
        run_id=analysis_state.run_id,
        user_input=analysis_state.user_input,
        created_at=analysis_state.created_at
    )
    parent_update.due_diligence = due_diligence

    return {"analysis_state": parent_update}
