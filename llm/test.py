# SPDX-License-Identifier: MIT
# file: CLAI/llm/test_interactive.py

import json
import uuid
from CLAI.llm.config_hf import get_hf_config
from CLAI.llm.adapter_hf import HFClient
from CLAI.llm.translator import build_messages, unmask_local


def pretty(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)


def main():
    print("🔍 Interactive Shell+LLM test (prompt_builder → translator → adapter)\n")

    # Load config and init client
    cfg = get_hf_config()
    client = HFClient()
    print(f"✅ Loaded model: {cfg['model']}\n")

    # Keep asking user input until they type 'exit'
    while True:
        user_input = input("💬 Enter your question (or type 'exit'): ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Exiting interactive test.")
            break

        # Build full system prompt via translator (pulls from prompt_builder)
        context = {"session": "interactive_test", "cwd": "/home/user"}
        messages, mapping = build_messages(user_input, context=context)

        print("\n--- Stage 1: Final prompt (masked) ---")
        print(pretty({"messages": messages}))

        payload = {
            "model": cfg["model"],
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 256,
        }

        print("\n⚙️ Sending to adapter...")
        try:
            resp = client.chat_completions(**payload)
        except Exception as e:
            print(f"❌ Adapter error: {e}")
            continue

        print("\n--- Stage 2: Raw model response (masked) ---")
        print(pretty(resp))

        raw_text = resp["choices"][0]["message"]["content"]
        unmasked = unmask_local(raw_text, mapping)

        print("\n--- Stage 3: Unmasked response (local view) ---")
        print(unmasked)

        # Prepare final JSON payload (like runner input)
        final_json = {
            "id": str(uuid.uuid4()),
            "user_input": user_input,
            "assistant_unmasked": unmasked,
            "masked_messages": messages,
            "model": cfg["model"],
        }

        print("\n--- Stage 4: Final JSON to forward to runner ---")
        print(pretty(final_json))
       


if __name__ == "__main__":
    main()
