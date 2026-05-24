from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from vs_analyst.agents import AgentRegistry
from vs_analyst.prompts import PromptRegistry
from vs_analyst.schemas.founder import FounderSchema
from vs_analyst.schemas.state import AnalysisState
from vs_analyst.tools.deep_research import deep_research_tool
from vs_analyst.utility.llm import llm
from vs_analyst.utility.logs import get_logger

logger = get_logger(__name__)


async def founder_profiler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parallel Founder Profiler Node.
    Reads a single fanned-out founder slice, calls AgentRegistry.founder_profiler via ReAct loop,
    and updates the FounderSchema in-place with verified details.
    Conforms to founder_sub_graph.md and Phase 5 specs.
    """
    analysis_state = state["analysis_state"]
    founder = state["founder"]

    logger.info(
        "Parallel Founder Profiler started",
        run_id=analysis_state.run_id,
        founder_name=founder.name
    )

    # 1. Initialize ReAct Messages
    messages = [
        SystemMessage(content=PromptRegistry.founder_profiler_system.value),
        HumanMessage(
            content=(
                f"Please conduct target biographical research and verify the background details for:\n"
                f"Founder Name: {founder.name}\n"
                f"Stated Role: {founder.role.value if founder.role else 'unknown'}\n"
                f"Pitch Deck Bio Claim: '{founder.bio_from_deck or ''}'\n\n"
                f"Use deep_research_tool to search for their LinkedIn profile, careers/employers, education history, "
                f"and notable achievements."
            )
        )
    ]

    # 2. ReAct Execution Loop (Up to 5 iterations)
    try:
        for step in range(5):
            logger.info("Executing ReAct profiler loop step", step=step, founder_name=founder.name)
            response = await AgentRegistry.founder_profiler.ainvoke(messages)
            messages.append(response)

            if not response.tool_calls:
                # No more tools called, agent has finished searching
                break

            for tool_call in response.tool_calls:
                if tool_call["name"] == "deep_research_tool":
                    args = tool_call["args"]
                    logger.info("ReAct loop calling deep_research_tool", args=args, founder_name=founder.name)
                    tool_result = await deep_research_tool.ainvoke(args)
                    messages.append(
                        ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_call["id"],
                            name=tool_call["name"]
                        )
                    )
                else:
                    logger.warning("Agent called unknown tool in profiler", tool_name=tool_call["name"])
                    messages.append(
                        ToolMessage(
                            content=f"Error: Unknown tool {tool_call['name']}.",
                            tool_call_id=tool_call["id"],
                            name=tool_call["name"]
                        )
                    )

        research_findings = messages[-1].content
        logger.info("Biographical research compilation completed", founder_name=founder.name)

        # 3. Parse Findings into structured FounderSchema fields using LLM structured output
        parser_agent = llm.with_structured_output(FounderSchema)
        parse_prompt = (
            f"You are a structured parser. Read the following verified biographical research findings for "
            f"founder {founder.name} and parse them into structured JSON format matching the schema:\n\n"
            f"--- Verified Research Findings ---\n"
            f"{research_findings}\n\n"
            f"Note: Ensure the 'name' field matches '{founder.name}'. Do not invent or change bio_from_deck."
        )
        
        parsed_result = await parser_agent.ainvoke([
            SystemMessage(content="You are a precise data parsing assistant. Parse findings into structured schemas."),
            HumanMessage(content=parse_prompt)
        ])

        # 4. In-place merge ONLY empty or None fields (Never overwrite existing bio_from_deck or other non-empty fields)
        if parsed_result:
            logger.info("Structured schema successfully parsed", founder_name=founder.name)
            
            if not founder.linkedin_url and parsed_result.linkedin_url:
                founder.linkedin_url = parsed_result.linkedin_url
                
            if not founder.past_companies and parsed_result.past_companies:
                founder.past_companies = parsed_result.past_companies
                
            if not founder.past_roles and parsed_result.past_roles:
                founder.past_roles = parsed_result.past_roles
                
            if not founder.education and parsed_result.education:
                founder.education = parsed_result.education
                
            if not founder.linkedin_summary and parsed_result.linkedin_summary:
                founder.linkedin_summary = parsed_result.linkedin_summary
                
            if not founder.verified_background and parsed_result.verified_background:
                founder.verified_background = parsed_result.verified_background
                
            if not founder.notable_achievements and parsed_result.notable_achievements:
                founder.notable_achievements = parsed_result.notable_achievements
                
            # Github fields mapping (if parsed)
            if not founder.github_url and parsed_result.github_url:
                founder.github_url = parsed_result.github_url
            if founder.github_public_repos is None and parsed_result.github_public_repos is not None:
                founder.github_public_repos = parsed_result.github_public_repos
            if not founder.github_languages and parsed_result.github_languages:
                founder.github_languages = parsed_result.github_languages
            if not founder.github_oss_notable and parsed_result.github_oss_notable:
                founder.github_oss_notable = parsed_result.github_oss_notable
            if not founder.github_account_age and parsed_result.github_account_age:
                founder.github_account_age = parsed_result.github_account_age
            if founder.github_active is None and parsed_result.github_active is not None:
                founder.github_active = parsed_result.github_active

    except Exception as e:
        logger.error(
            "Error in founder profiler node",
            run_id=analysis_state.run_id,
            founder_name=founder.name,
            error=str(e)
        )

    # 5. Build and return parent state update (Merged via merge_founders_reducer)
    parent_update = AnalysisState(
        run_id=analysis_state.run_id,
        user_input=analysis_state.user_input,
        created_at=analysis_state.created_at
    )
    parent_update.founders = [founder]

    return {"analysis_state": parent_update}
