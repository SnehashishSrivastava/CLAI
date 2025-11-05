# file: CLAI/test_hf_adapter.py
import json
from CLAI.llm.adapter_hf import HFAdapter

print("🔍 Testing Hugging Face Router Adapter...")

# Instantiate (slot=0 uses HF_TOKEN or HF_KEY_0 from .env)
adapter = HFAdapter(slot=0)

# Simple masked text to test
nl_request = "Return JSON: {\"hello\": \"world\"}"

# Call the adapter
try:
    result = adapter.generate_plan_json(nl_request)
except Exception as e:
    print("❌ Adapter error:", e)
    raise SystemExit(1)

print("\n✅ Adapter call succeeded!")
print("HTTP status:", result.http_status)
print("\nRaw response text:\n", result.raw_text[:400], "\n")

print("Parsed JSON plan:")
print(json.dumps(result.model_json, indent=2))
