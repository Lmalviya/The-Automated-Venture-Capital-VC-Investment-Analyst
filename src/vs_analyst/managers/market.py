from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage

from vs_analyst.prompts import PromptRegistry
from vs_analyst.tools.market_tools import web_search_tool, market_synthesizer_tool
from vs_analyst.schemas.state import PipelineGraphState
from vs_analyst.utility.llm import llm
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)

class MarketManager:
    """
    Declarative metadata definition for the Market Research Manager agent.

    This class contains NO graph logic, NO LLM instantiation, and NO routing.
    All StateGraph compilation, node definitions, routing, and state mapping
    live exclusively in orchestrator/pipeline.py.

    The orchestrator reads these three attributes to wire up the agent:
      - name:          used as the node name in the StateGraph
      - system_prompt: passed as the SystemMessage to the LLM
      - tools:         bound to the LLM via llm.bind_tools(MarketManager.tools)

    Note: This manager is a Phase-2 stub. Tools return placeholder responses.
    """

    name: str = "market"
    system_prompt: str = PromptRegistry.market_system.value
    tools: list = [web_search_tool, market_synthesizer_tool]


market_llm = llm.bind_tools(MarketManager.tools)
async def market_agent_node(state: PipelineGraphState) -> Dict[str, Any]:
    """
    Market research agent node. Runs after intake is complete.
    Initializes its own SystemMessage + HumanMessage on first call.
    """
    analysis_state = state["analysis_state"]
    messages = list(state["messages"])

    # Detect first call by checking if market system prompt is already in messages
    has_market_system = any(
        isinstance(m, SystemMessage) and "Market Research Manager" in m.content
        for m in messages
    )

    if not has_market_system:
        logger.info("Market agent: first turn", run_id=analysis_state.run_id)
        company_name = analysis_state.company.name or "the startup"
        sector = analysis_state.company.sector or "the relevant sector"
        messages = messages + [
            SystemMessage(content=MarketManager.system_prompt),
            HumanMessage(
                content=(
                    f"Conduct market research for '{company_name}' "
                    f"operating in '{sector}'.\nRun ID: {analysis_state.run_id}"
                )
            ),
        ]

    response = await market_llm.ainvoke(messages)
    logger.info("Market agent: LLM responded", run_id=analysis_state.run_id)
    return {"messages": [response]}