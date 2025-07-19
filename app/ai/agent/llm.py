
from typing import List, Optional, Type, Union
import re
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from app.core.config import settings


class LLM:
    @staticmethod
    def get_response(prompt):
        model = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            api_key=settings.GEMINI_API_KEY
        )
        resp =  model.invoke(prompt)
        return resp.content

    @staticmethod
    def get_structured_response(prompt, schema: Type[BaseModel] = None):
        resp = LLM.get_response(prompt)
        json_data = LLM.extract_json_blocks_from_response(resp)

        if schema:
            if isinstance(json_data, list):
                return [schema.model_validate(item) for item in json_data]
            return schema.model_validate(json_data)

        return json_data


    @staticmethod
    def _extract_blocks_from_response(content: str, start_sep: str, end_sep: str, multiple: bool = False) -> Union[List[str], str]:
        pattern = re.escape(start_sep) + r"(.*?)" + re.escape(end_sep)
        matches = re.findall(pattern, content, re.DOTALL)
        extracted = [match.strip() for match in matches]
        return extracted if multiple else (extracted[0] if extracted else "")


    @staticmethod
    def extract_json_blocks_from_response(content: str, multiple: bool = False) -> Union[List[dict], dict]:
        json_blocks = LLM._extract_blocks_from_response(content, "```json", "```", multiple=multiple)
        if not json_blocks:
            return [] if multiple else {}
        
        parsed_jsons = []
        for block in (json_blocks if isinstance(json_blocks, list) else [json_blocks]):
            try:
                parsed_jsons.append(json.loads(block))
            except json.JSONDecodeError:
                print("Error: Invalid JSON format")
                print(block)
        
        return parsed_jsons if multiple else parsed_jsons[0] if parsed_jsons else {}
