# file: CLAI/prompt_builder/few_shots.py

FEW_SHOTS = [
    {
        "role": "user",
        "content": "list python files larger than 10 MB modified this week",
    },
    {
        "role": "assistant",
        "tool_calls": [{
            "id": "tool_1",
            "type": "function",
            "function": {
                "name": "emit_plan_v1",
                "arguments": {
                    "version": "1.0",
                    "intent": "file_search",
                    "command": ["bash","-lc","find . -type f -name '*.py' -mtime -7 -size +10M -print"],
                    "cwd": ".",
                    "inputs": [],
                    "outputs": [],
                    "explain": "Find *.py changed in 7 days and larger than 10MB."
                }
            }
        }],
    },
    {
        "role": "user",
        "content": "delete the big logs",
    },
    {
        "role": "assistant",
        "tool_calls": [{
            "id": "tool_2",
            "type": "function",
            "function": {
                "name": "emit_plan_v1",
                "arguments": {
                    "version": "1.0",
                    "intent": "file_delete",
                    "command": ["bash","-lc","echo 'awaiting confirmation'"],
                    "cwd": ".",
                    "inputs": [],
                    "outputs": [],
                    "explain": "Deletion is destructive; request scope/confirmation first.",
                    "needs_clarification": True,
                    "question": "Which directory and size threshold? Preview first?"
                }
            }
        }],
    },
]
