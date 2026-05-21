import json
from typing import List, Dict
from vs_analyst.config import settings
from openai import OpenAI

from vs_analyst.schemas.adapters import AdaptorType

def _output_parser(content: str, response_format: AdaptorType):
    json_output = json.loads(content)
    pydantic_output = response_format(**json_output)
    return pydantic_output

def _llm_call(messages: List[Dict], model: str, max_token: int, temperature:float, log, response_format: AdaptorType=None):
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
    return _llm_call(messages, settings.llm.model, settings.llm.max_tokens, settings.llm.temperature, log)

def query_vision_model(messages: List[Dict], log) -> str:
    """Helper to call OpenAI Vision API and extract structured content from slide image."""

    log.info("Sending slide/page image to vision model")
    return _llm_call(messages, settings.vlm.model, settings.vlm.max_tokens, settings.vlm.temperature, log)
    