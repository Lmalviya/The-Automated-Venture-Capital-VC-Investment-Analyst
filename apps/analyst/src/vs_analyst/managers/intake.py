from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage

from vs_analyst.prompts import PromptRegistry
from vs_analyst.tools.file_extractor import pdf_extractor_tool
from vs_analyst.tools.website_scraper import website_scraper_tool

from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.utility.llm import llm

from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

class IntakeManager:
    """
    Declarative metadata definition for the Intake Manager agent.

    This class contains NO graph logic, NO LLM instantiation, and NO routing.
    All StateGraph compilation, node definitions, routing, and state mapping
    live exclusively in orchestrator/pipeline.py.

    The orchestrator reads these three attributes to wire up the agent:
      - name:          used as the node name in the StateGraph
      - system_prompt: passed as the SystemMessage to the LLM
      - tools:         bound to the LLM via llm.bind_tools(IntakeManager.tools)
    """

    name: str = "intake"
    system_prompt: str = PromptRegistry.intake_system.value
    tools: list = [pdf_extractor_tool, website_scraper_tool]

intake_llm = llm.bind_tools(IntakeManager.tools)
async def intake_agent_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Intake agent node.
    On first call: builds SystemMessage + HumanMessage from IntakeManager config.
    On subsequent calls (after tool results): passes updated messages back to LLM.
    """
    analysis_state = state["analysis_state"]
    messages = list(state["messages"])

    if not messages:
        logger.info("Intake agent: first turn", run_id=analysis_state.run_id)
        human_text = PromptRegistry.intake_human.value.format(
            run_id=analysis_state.run_id,
            deck_path=analysis_state.user_input.pitch_deck_path,
            website_url=analysis_state.user_input.website_url or "None provided",
        )
        messages = [
            SystemMessage(content=IntakeManager.system_prompt),
            HumanMessage(content=human_text),
        ]

    response = await intake_llm.ainvoke(messages)
    logger.info("Intake agent: LLM responded", run_id=analysis_state.run_id)
    return {"messages": [response]}
