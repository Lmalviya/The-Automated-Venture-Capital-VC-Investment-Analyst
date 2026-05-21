from langchain_core import tool
from typing import Annotated
from langgraph.prebuilt import InjectedState
from langchain_core.prompts import ChatPromptTemplate

from vs_analyst.prompts import PromptRegistry
@tool
def query_pitch_deck_tool(
    query: str,
    raw_deck_text: Annotated[str, InjectedState("raw_deck_text")]
) -> str:
    """
    Search and query the raw extracted text of the startup pitch deck for a specific detail.
    Use this tool if you need to look up obscure or highly specific numbers, facts,
    or details from the pitch deck that are not available in the main structured state.

    Args:
        query: The specific question or detail to search for (e.g., Q3 monthly retention).
    """
    if not raw_deck_text:
        return "No pitch deck text has been extracted yet. Please run the PDF extractor tool first."

    # Import llm lazily to prevent circular imports
    from vs_analyst.utility.llm import llm

    prompt = ChatPromptTemplate.from_messages([
        ("system", PromptRegistry.deck_query.value),
        ("human", "Question: {QUERY}")
    ])

    chain = prompt | llm
    response = chain.invoke({"TEXT": raw_deck_text, "QUERY": query})
    return response.content