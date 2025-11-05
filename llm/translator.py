import json
from typing import Dict, List, Tuple
from .masking import mask_text, deep_unmask

# import prompt builder modules
from importlib import import_module

def _load_prompt_module(module: str) -> str:
    """Try loading SYSTEM_PROMPT or BASE_PROMPT strings from prompt_builder modules."""
    try:
        mod = import_module(f"CLAI.prompt_builder.{module}")
        for attr in ["SYSTEM_PROMPT", "BASE_PROMPT", "DEFAULT_PROMPT", "PROMPT"]:
            if hasattr(mod, attr):
                return getattr(mod, attr)
        return ""
    except Exception:
        return ""

def _compose_system_prompt() -> str:
    """Combine base, safety, and few-shot prompts."""
    base = _load_prompt_module("base_prompts")
    safety = _load_prompt_module("safety_policy")
    few = _load_prompt_module("few_shots")

    system_prompt = (
        f"{base}\n\n"
        "### Safety Policy\n"
        f"{safety}\n\n"
        "### Few-Shot Examples\n"
        f"{few}\n\n"
        "### Task\nYou are a Shell+LLM assistant that converts natural-language "
        "queries into safe, auditable shell commands."
    )
    return system_prompt.strip()


def build_messages(
    user_text: str,
    system_text: str | None = None,
    context: Dict | None = None,
) -> Tuple[List[Dict], Dict]:
    """
    Build model-ready message list using masking, with system_text automatically
    constructed from prompt_builder if not provided.
    """
    context = context or {}
    if system_text is None:
        system_text = _compose_system_prompt()

    # Mask all segments
    sys_masked, map_sys = mask_text(system_text)
    usr_masked, map_usr = mask_text(user_text)
    ctx_json = json.dumps(context, ensure_ascii=False)
    ctx_masked, map_ctx = mask_text(ctx_json)

    # Combine messages
    messages = [
        {"role": "system", "content": sys_masked},
        {"role": "user", "content": f"{usr_masked}\n\n[context]\n{ctx_masked}"},
    ]
    mapping = {**map_sys, **map_usr, **map_ctx}
    return messages, mapping


def unmask_local(text: str, mapping: Dict) -> str:
    """Optional helper for local logs only."""
    return deep_unmask(text, mapping)