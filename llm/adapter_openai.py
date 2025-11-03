# SPDX-License-Identifier: MIT
# file: CLAI/llm/adapter_openai.py

from __future__ import annotations
import json, os
from dataclasses import dataclass
from typing import Any, Dict, Optional
from dotenv import load_dotenv; load_dotenv()
# ---- import your prompt + schema (matches your current tree) ----
from ..prompt_builder.base_prompts import SYSTEM_PROMPT
from ..prompt_builder.few_shots import FEW_SHOTS
from ..prompt_builder.schemas.plan_v1 import PLAN_JSON_SCHEMA, PLAN_FN_NAME, PLAN_VERSION 
try:
    # OpenAI Python SDK >= 1.0
    from openai import OpenAI
except Exception:
    OpenAI = None  # type: ignore


@dataclass
class TranslationResult:
    plan: Dict[str, Any]
    raw_response: Dict[str, Any]


class OpenAITranslator:
    """
    Structured-output translator via OpenAI Responses API.
    Env:
      OPENAI_API_KEY        (required)
      OPENAI_BASE_URL       (optional)
      CLAI_OPENAI_MODEL     (optional, default 'gpt-4.1-mini')
    """
    def __init__(self, model: Optional[str] = None, base_url: Optional[str] = None):
        if OpenAI is None:
            raise RuntimeError("Install the SDK: pip install openai>=1.40")
        self.client = OpenAI(base_url=base_url or os.environ.get("OPENAI_BASE_URL"))
        self.model = model or os.environ.get("CLAI_OPENAI_MODEL", "gpt-4.1-mini")

    def translate(self, nl_request: str, extra_context: Optional[dict] = None) -> TranslationResult:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *FEW_SHOTS,
            {"role": "user", "content": self._format_user(nl_request, extra_context)},
        ]

        resp = self.client.responses.create(
            model=self.model,
            messages=messages,
            tools=[{
                "type": "function",
                "function": {
                    "name": PLAN_FN_NAME,
                    "description": f"Emit CLAI plan JSON v{PLAN_VERSION}. Must adhere to schema.",
                    "parameters": PLAN_JSON_SCHEMA,
                    "strict": True,   # enforce schema-compatible args
                }
            }],
            tool_choice={"type": "function", "function": {"name": PLAN_FN_NAME}},
            temperature=0,
        )

        plan = self._extract_plan_args(resp)
        self._validate_basic(plan)
        return TranslationResult(plan=plan, raw_response=_to_dict(resp))

    # ---------- helpers ----------
    def _format_user(self, nl_request: str, extra: Optional[dict]) -> str:
        if not extra:
            return nl_request
        ctx = "\n".join(f"{k}: {v}" for k, v in extra.items())
        return f"{nl_request}\n\n[context]\n{ctx}"

    def _extract_plan_args(self, resp) -> Dict[str, Any]:
        # Preferred path for recent SDKs
        try:
            for item in resp.output:
                if item.type == "tool_call" and item.tool_call.type == "function":
                    if item.tool_call.function.name == PLAN_FN_NAME:
                        args = item.tool_call.function.arguments
                        return args if isinstance(args, dict) else json.loads(args)
        except Exception:
            pass
        # Fallback: walk dict form
        data = _to_dict(resp)
        for ch in data.get("output", []) or data.get("choices", []):
            msg = ch.get("message") or ch.get("delta") or {}
            for tc in msg.get("tool_calls", []) or []:
                fn = tc.get("function") or {}
                if fn.get("name") == PLAN_FN_NAME:
                    return json.loads(fn.get("arguments", "{}"))
        raise RuntimeError("No function/tool call with plan arguments found.")

    def _validate_basic(self, plan: Dict[str, Any]) -> None:
        for k in ["version", "intent", "command", "cwd", "inputs", "outputs", "explain"]:
            if k not in plan:
                raise ValueError(f"Plan missing required field: {k}")
        if plan["version"] != PLAN_VERSION:
            raise ValueError(f"Unsupported plan version: {plan['version']}")
        if not isinstance(plan["command"], list) or not all(isinstance(s, str) for s in plan["command"]):
            raise ValueError("command must be a list[str]")


def _to_dict(obj: Any) -> Dict[str, Any]:
    try:
        if hasattr(obj, "model_dump_json"):
            import json as _json
            return _json.loads(obj.model_dump_json())
        if hasattr(obj, "to_dict"):
            return obj.to_dict()  # type: ignore
    except Exception:
        pass
    import json as _json
    return _json.loads(_json.dumps(obj, default=lambda o: getattr(o, "__dict__", str(o))))
