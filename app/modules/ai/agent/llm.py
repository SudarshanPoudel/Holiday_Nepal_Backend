import os
import re
import json
from typing import List, Type, Union, Optional, Literal, TypedDict
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()

# 🔒 Global LLM Type Alias
LLMType = Literal["gemini", "groq"]

class LLM:
    MODEL_MAP: dict[LLMType, dict] = {
        "gemini": {
            "class": ChatGoogleGenerativeAI,
            "model": "gemini-2.5-flash",
            "key_env": "GEMINI_API_KEY"
        },
        "groq": {
            "class": ChatGroq,
            "model": "llama3-70b-8192",
            "key_env": "GROQ_API_KEY"
        }
    }

    @staticmethod
    def _get_model_instance(llm: LLMType):
        config = LLM.MODEL_MAP[llm]
        api_key = os.getenv(config["key_env"])
        return config["class"](model=config["model"], api_key=api_key)

    @staticmethod
    async def get_response(prompt: str, llm: LLMType = "groq") -> str:
        model = LLM._get_model_instance(llm)
        resp = await model.ainvoke(prompt)
        return resp.content

    @staticmethod
    async def get_structured_response(
        prompt: str,
        schema: Optional[Type[BaseModel]] = None,
        llm: LLMType = "groq",
    ):
        resp = await LLM.get_response(prompt, llm)
        json_data = LLM.extract_json_blocks_from_response(resp)

        if schema:
            if isinstance(json_data, list):
                return [schema.model_validate(item) for item in json_data]
            return schema.model_validate(json_data)

        return json_data

    @staticmethod
    def _extract_blocks_from_response(
        content: str,
        start_sep: str,
        end_sep: str,
        multiple: bool = False
    ) -> Union[List[str], str]:
        pattern = re.escape(start_sep) + r"(.*?)" + re.escape(end_sep)
        matches = re.findall(pattern, content, re.DOTALL)
        extracted = [match.strip() for match in matches]
        return extracted if multiple else (extracted[0] if extracted else "")

    @staticmethod
    def extract_json_blocks_from_response(
        content: str,
        multiple: bool = False
    ) -> Union[List[dict], dict]:
        import ast

        def try_parse_all_blocks(candidates):
            parsed = []
            for block in candidates:
                try:
                    if isinstance(block, str) and block.startswith('"') and block.endswith('"'):
                        block = ast.literal_eval(block)  # unescape stringified JSON
                    parsed.append(json.loads(block))
                except Exception:
                    continue
            return parsed

        # 0. First try direct parsing — content *is* a full JSON string
        try:
            direct = json.loads(content)
            return direct if not multiple else [direct]
        except Exception:
            pass

        # 1. Try ```json fenced blocks
        blocks = LLM._extract_blocks_from_response(content, "```json", "```", multiple=True)

        # 2. Try to extract all {...} or [...] using greedy matching
        if not blocks:
            raw_matches = re.findall(r'(\{(?:[^{}]|(?R))*\}|\[(?:[^\[\]]|(?R))*\])', content, re.DOTALL)
            blocks = raw_matches

        # 3. Try finding escaped stringified JSON
        if not blocks:
            escaped_match = re.search(r'"({\\n.*?})"', content)
            if escaped_match:
                try:
                    unescaped = bytes(escaped_match.group(1), "utf-8").decode("unicode_escape")
                    blocks = [unescaped]
                except Exception:
                    pass

        if not blocks:
            return [] if multiple else {}

        parsed = try_parse_all_blocks(blocks)
        return parsed if multiple else (parsed[0] if parsed else {})
