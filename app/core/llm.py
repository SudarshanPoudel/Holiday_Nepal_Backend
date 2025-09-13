import os
import re
import json
from typing import AsyncGenerator, List, Type, Union, Optional, Literal, TypedDict
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

load_dotenv()

# 🔒 Global LLM Type Alias
LLMType = Literal["gemini", "groq"]
DEFAULT_LLM = "groq"

class LLM:
    MODEL_MAP: dict[LLMType, dict] = {
        "gemini": {
            "class": ChatGoogleGenerativeAI,
            "model": "gemini-2.5-flash",
            "key_env": "GEMINI_API_KEY"
        },
        "groq": {
            "class": ChatGroq,
            "model": "llama-3.3-70b-versatile",
            "key_env": "GROQ_API_KEY"
        }
    }

    @staticmethod
    def _get_model_instance(llm: LLMType):
        config = LLM.MODEL_MAP[llm]
        api_key = os.getenv(config["key_env"])
        return config["class"](model=config["model"], api_key=api_key)

    @staticmethod
    async def get_response(prompt: str, llm: LLMType = DEFAULT_LLM) -> str:
        model = LLM._get_model_instance(llm)
        resp = await model.ainvoke(prompt)
        return resp.content
    
        
    @staticmethod
    async def get_stream(prompt: str, llm=DEFAULT_LLM):
        model = LLM._get_model_instance(llm)
        async for chunk in model.astream([prompt]):
            if chunk.content:
                yield chunk.content
    

    @staticmethod
    async def get_structured_response(
        prompt: str,
        schema: Optional[Type[BaseModel]] = None,
        llm: LLMType = DEFAULT_LLM
    ):
        resp = await LLM.get_response(prompt, llm)
        json_data = LLM.extract_json_blocks_from_response(resp)

        if schema:
            if isinstance(json_data, list):
                return [schema.model_validate(item) for item in json_data]
            return schema.model_validate(json_data)

        return json_data
    
    @staticmethod
    async def get_structured_stream(
        prompt: str,
        schema: Optional[Type[BaseModel]] = None,
        llm: LLMType = DEFAULT_LLM
    ) -> AsyncGenerator[dict, None]:
        """
        Stream structured JSON progressively.
        Instead of token-by-token, yield partial valid dicts/lists.
        """

        model = LLM._get_model_instance(llm)
        buffer = ""
        last_yielded = None

        async for chunk in model.astream([prompt]):
            if not chunk.content:
                continue
            buffer += chunk.content

            # Try to close brackets/quotes and parse progressively
            partial_json = LLM._try_make_valid_json(buffer)

            if partial_json is not None and partial_json != last_yielded:
                # Validate with schema if given
                if schema:
                    try:
                        if isinstance(partial_json, list):
                            parsed = [
                                schema.model_validate(item) for item in partial_json
                            ]
                        else:
                            parsed = schema.model_validate(partial_json)
                    except Exception:
                        continue
                    yield parsed
                else:
                    yield partial_json

                last_yielded = partial_json


    @staticmethod
    def _try_make_valid_json(buffer: str):
        """
        Coerce incomplete/midstream LLM output into valid JSON.
        Steps:
        1. Strip junk fences/explanations
        2. Auto-close unbalanced braces/brackets
        3. Trim dangling quotes/colons
        4. Extract largest JSON-like block
        5. Parse
        """
        if not buffer:
            return None

        # 1. Strip markdown fences
        buffer = re.sub(r"^```(?:json)?", "", buffer, flags=re.IGNORECASE|re.MULTILINE)
        buffer = re.sub(r"```$", "", buffer, flags=re.MULTILINE)
        buffer = buffer.strip()

        if not buffer:
            return None

        # 2. Auto-close braces/brackets
        stack = []
        open_to_close = {"{": "}", "[": "]"}
        for ch in buffer:
            if ch in open_to_close:
                stack.append(open_to_close[ch])
            elif stack and ch == stack[-1]:
                stack.pop()
        if stack:
            buffer += "".join(reversed(stack))

        # 3. Patch dangling colon (`{"a":`)
        buffer = re.sub(r':\s*$', ': null', buffer)

        # 3b. Trim unfinished string (dangling quote at end)
        buffer = re.sub(r'"\s*$', '""', buffer)

        # 4. Extract largest JSON-like block
        blocks = LLM._extract_json_like_blocks(buffer)
        if not blocks:
            return None
        candidate = blocks[-1]

        # 5. Parse
        try:
            return json.loads(candidate)
        except Exception:
            return None


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
            blocks = LLM._extract_json_like_blocks(content)


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

    @staticmethod
    def _extract_json_like_blocks(text: str) -> list[str]:
        blocks, stack, start = [], [], None
        for i, ch in enumerate(text):
            if ch in "{[":
                if not stack:
                    start = i
                stack.append(ch)
            elif ch in "}]":
                if stack:
                    stack.pop()
                    if not stack and start is not None:
                        blocks.append(text[start:i+1])
                        start = None
        return blocks
