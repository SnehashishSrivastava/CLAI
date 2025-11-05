# file: CLAI/test_env_load.py
import os
from dotenv import load_dotenv

print("🔍 Checking environment load...")

# Explicitly load .env from your project root
# Adjust the path if your .env is not in the same directory as this file
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if not os.path.exists(dotenv_path):
    print(f"⚠️  No .env file found at {dotenv_path}")
else:
    print(f"📄 Loading .env from: {os.path.abspath(dotenv_path)}")
    load_dotenv(dotenv_path, override=True)

# Print a few key variables
keys = [
    "HF_SLOT",
    "HF_KEY_0",
    "HF_MODEL_0",
    "HF_BASE_0",
    "HF_TOKEN",
    "HF_MODEL",
    "HF_BASE_URL",
]

print("\n🔧 Environment values:")
for key in keys:
    val = os.getenv(key)
    if val:
        shown = val[:10] + "..." if "KEY" in key or "TOKEN" in key else val
        print(f"  {key} = {shown}")
    else:
        print(f"  {key} = ❌ Not set")

# Simple validation
if os.getenv("HF_TOKEN") or os.getenv("HF_KEY_0"):
    print("\n✅ Token detected. You’re good to call the API!")
else:
    print("\n❌ No Hugging Face token found. Check .env format or reload shell.")
