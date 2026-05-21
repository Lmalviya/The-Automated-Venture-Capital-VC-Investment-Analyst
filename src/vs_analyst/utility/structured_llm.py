from typing import List, Dict, Type, TypeVar
from pydantic import BaseModel
from openai import OpenAI
from vs_analyst.config import settings

T = TypeVar("T", bound=BaseModel)

def query_structured_model(
    messages: List[Dict[str, str]],
    response_format: Type[T],
    log
) -> T:
    """
    Sends messages to the OpenAI Chat Completions API and forces a structured
    response matching the specified Pydantic schema using Structured Outputs.
    """
    log.info(
        "Sending request with Structured Outputs response_format",
        model=settings.llm.text_model,
        schema_name=response_format.__name__
    )
    
    try:
        client = OpenAI()
        response = client.beta.chat.completions.parse(
            model=settings.llm.text_model,
            messages=messages,
            response_format=response_format,
            temperature=settings.llm.temperature
        )
        
        parsed_result = response.choices[0].message.parsed
        if parsed_result is None:
            # Fallback in case of parsing failures
            refusal = getattr(response.choices[0].message, "refusal", None)
            if refusal:
                log.error("Model refused to answer", refusal=refusal)
                raise ValueError(f"Model refused to answer: {refusal}")
            raise ValueError("Parsed output was empty or failed validation.")
            
        return parsed_result
        
    except Exception as e:
        log.error("Error encountered while calling structured LLM API", error=str(e))
        raise e
