

from __future__ import annotations
import os, re
from typing import Dict, Tuple, Any

_PATH_RE = re.compile(
    r"""(?x)
    ( # Windows absolute C:\... or UNC \\server\share
      (?:[A-Za-z]:\\[^\s"']+)
      |(?:\\\\[^\s\\/]+\\[^\s"']+)
      # or POSIX /home/user/... or ./rel or ../rel
      |(?:\/(?:[^ \n\r\t"'\\]|\\.)+)
      |(?:\.\.?\/(?:[^ \n\r\t"'\\]|\\.)+)
    )
    """
)

_FILENAME_RE = re.compile(r"""(?i)\b([A-Za-z0-9_\-]+\.(?:log|txt|csv|json|py|sh|zip|tar|gz|yml|yaml))\b""")

_EMAIL_RE = re.compile(r"""(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b""")

_IP_RE = re.compile(r"""\b(?:(?:\d{1,3}\.){3}\d{1,3})\b""")

def _token(tok_type: str, idx: int) -> str:
    return f"__{tok_type}_{idx}__"

def mask_text(s: str) -> Tuple[str, Dict[str, str]]:
    """
    Mask sensitive tokens in a string. Returns (masked_string, mapping_dict)
    where mapping_dict maps TOKEN -> original.
    """
    mapping: Dict[str, str] = {}
    def replace_all(pattern, typ, text):
        idx = 1
        def repl(m):
            nonlocal idx
            orig = m.group(0)
            t = _token(typ, idx)
            idx += 1
            mapping[t] = orig
            return t
        return pattern.sub(repl, text)

    s1 = replace_all(_EMAIL_RE, "EMAIL", s)
    s2 = replace_all(_IP_RE, "IP", s1)
    s3 = replace_all(_PATH_RE, "PATH", s2)
    s4 = replace_all(_FILENAME_RE, "FILE", s3)
    return s4, mapping

def deep_unmask(obj: Any, mapping: Dict[str, str]) -> Any:
    """Recursively replace tokens back using mapping."""
    if isinstance(obj, str):
        out = obj
        for tok, orig in mapping.items():
            out = out.replace(tok, orig)
        return out
    if isinstance(obj, list):
        return [deep_unmask(x, mapping) for x in obj]
    if isinstance(obj, dict):
        return {k: deep_unmask(v, mapping) for k, v in obj.items()}
    return obj
