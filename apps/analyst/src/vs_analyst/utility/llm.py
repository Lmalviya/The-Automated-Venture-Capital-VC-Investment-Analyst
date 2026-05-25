import os
import json
from typing import List, Dict, Any
from pydantic import BaseModel
from vs_analyst.config import settings
from openai import OpenAI

from vs_analyst.schemas.adapters import AdaptorType

def _mock_output_for_schema(schema_class: Any) -> Any:
    """Generates a mock instance of a Pydantic schema class recursively."""
    if not isinstance(schema_class, type) or not issubclass(schema_class, BaseModel):
        return "Mock response"
        
    mock_dict = {}
    for field_name, field_info in schema_class.model_fields.items():
        annotation = field_info.annotation
        
        # Check standard types
        if annotation == int:
            mock_dict[field_name] = 2026
        elif annotation == float:
            mock_dict[field_name] = 85.5
        elif annotation == bool:
            mock_dict[field_name] = True
        elif annotation == str:
            mock_dict[field_name] = f"Mock {field_name} text content"
        elif hasattr(annotation, "__origin__"):
            origin = annotation.__origin__
            if origin is list:
                mock_dict[field_name] = []
            elif origin is dict:
                mock_dict[field_name] = {}
            else:
                mock_dict[field_name] = None
        else:
            # Recursive mock if it's a nested Pydantic model
            if isinstance(annotation, type) and issubclass(annotation, BaseModel):
                mock_dict[field_name] = _mock_output_for_schema(annotation)
            else:
                mock_dict[field_name] = None
                
    return schema_class(**mock_dict)


def _output_parser(content: str, response_format: AdaptorType):
    json_output = json.loads(content)
    pydantic_output = response_format(**json_output)
    return pydantic_output

def _llm_call(messages: List[Dict], model: str, max_token: int, temperature:float, log, response_format: AdaptorType=None):
    if os.environ.get("MOCK_LLM", "false").lower() == "true":
        log.info("Mock LLM Call: Intercepting and returning simulated output", model=model)
        if response_format:
            return _mock_output_for_schema(response_format)
        return "Mock text response generated offline to bypass active OpenAI calls."

    max_retry = 3
    retry = 0
    while retry <= max_retry:
        try:
            client = OpenAI(
            base_url = settings.llm.base_url,
            api_key = settings.llm.api_key
            )
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={ "type": "json_object" },
                max_tokens=max_token,
                temperature=temperature,
            )
            output = response.choices[0].message.content or ""
            messages.append({"role": "assistant", "content": output})
        except Exception as e:
            log.error("getting error while calling llm api")
            return "getting erorr while calling llm api"
        
        if response_format:
            try:
                return _output_parser(output, response_format)
            except Exception as e:
                log.error("Faild to parse the output")
                retry += 1
                messages.append({"role": "user", "content": f"error: {e}"})

        return output
        

def query_text_model(messages: List[Dict], response_format: AdaptorType, log) -> str:
    log.info("Querying text model")
    return _llm_call(messages, settings.llm.model, settings.llm.max_tokens, settings.llm.temperature, log, response_format)

def query_vision_model(messages: List[Dict], log) -> str:
    """Helper to call OpenAI Vision API and extract structured content from slide image."""

    log.info("Sending slide/page image to vision model")
    return _llm_call(messages, settings.vlm.model, settings.vlm.max_tokens, settings.vlm.temperature, log)


# =========================================================
# Centralized LangChain LLM instance (Mockable)
# =========================================================

if os.environ.get("MOCK_LLM", "false").lower() == "true":
    class MockChatModel:
        def __init__(self, *args, **kwargs):
            pass
        def with_structured_output(self, schema, **kwargs):
            class MockRunnable:
                async def ainvoke(self, *args, **kwargs):
                    return _mock_output_for_schema(schema)
                def invoke(self, *args, **kwargs):
                    return _mock_output_for_schema(schema)
            return MockRunnable()
        def bind_tools(self, tools, **kwargs):
            return self
        async def ainvoke(self, *args, **kwargs):
            from langchain_core.messages import AIMessage
            return AIMessage(content="Mock LLM response message")
        def invoke(self, *args, **kwargs):
            from langchain_core.messages import AIMessage
            return AIMessage(content="Mock LLM response message")
            
    llm = MockChatModel()
else:
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model=settings.llm.model or "mistralai/mistral-nemotron",
        openai_api_base=str(settings.llm.base_url),
        openai_api_key=(
            settings.llm.api_key.get_secret_value()
            if settings.llm.api_key
            else "dummy_key"
        ),
        temperature=settings.llm.temperature,
        max_tokens=settings.llm.max_tokens,
    )
