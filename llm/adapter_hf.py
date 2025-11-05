import requests
from .config_hf import get_hf_config

class HFClient:
    def __init__(self, base=None, token=None, model=None):
        cfg = get_hf_config()
        self.base  = (base  or cfg["base"]).rstrip("/")
        self.token =  token or cfg["token"]
        self.model =  model or cfg["model"]

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def chat_completions(self, messages, endpoint="/v1/chat/completions", **kwargs):
        """
        Uses an OpenAI style endpoint if your router provides it.
        You control the endpoint path. No auto '/hf-inference'.
        """
        url = f"{self.base}{endpoint}"
        payload = {
            "model": self.model,
            "messages": messages,
            **kwargs
        }
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()