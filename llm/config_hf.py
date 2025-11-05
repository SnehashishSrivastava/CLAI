import json
import os
from pathlib import Path

try:
    # ok if python-dotenv is not installed
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()  # loads .env if present
except Exception:
    pass

_SECRETS_FILE = Path(__file__).resolve().parent / "secrets.hf.json"

def _load_json_store():
    if _SECRETS_FILE.exists():
        try:
            with open(_SECRETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {k: str(v) for k, v in data.items()}
        except Exception:
            pass
    return {}

def get_hf_config():
    """
    Returns a plain dict with base, token, model.
    Priority: environment -> JSON store -> built in defaults.
    No special casing. No path forcing.
    """
    store = _load_json_store()

    base  = os.getenv("HF_BASE_URL", store.get("HF_BASE_URL", "https://router.huggingface.co")).strip()
    token = os.getenv("HF_TOKEN",    store.get("HF_TOKEN",    "")).strip()
    model = os.getenv("HF_MODEL",    store.get("HF_MODEL",    "meta-llama/Meta-Llama-3.1-8B-Instruct")).strip()

    if not base:
        raise ValueError("HF_BASE_URL is empty")
    if not token:
        raise ValueError("HF_TOKEN is empty")
    if not model:
        raise ValueError("HF_MODEL is empty")

    # normalize base to avoid accidental double slashes later
    base = base.rstrip("/")

    return {"base": base, "token": token, "model": model}