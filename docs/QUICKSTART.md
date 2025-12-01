# CLAI Quick Start Guide

Get up and running with CLAI in 5 minutes.

---

## Step 1: Installation (2 minutes)

### Prerequisites Check
```bash
python --version  # Should be 3.12+
git --version     # Should be installed
```

### Install Dependencies
```bash
cd CLAI
pip install -r requirements.txt
```

### Configure API Access

Create `CLAI/.env`:
```env
HF_TOKEN=hf_your_token_here
HF_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

**Get Hugging Face Token:**
1. Go to https://huggingface.co/settings/tokens
2. Create new token
3. Copy to `.env` file

---

## Step 2: Verify Setup (1 minute)

```bash
python test_llm_integration.py
```

**Expected Output:**
```
✅ Config loaded successfully
✅ HF connection working
✅ Prompt builder modules loaded
✅ Translation pipeline working
✅ Masking/unmasking works correctly

🎉 All tests passed!
```

If all tests pass, you're ready!

---

## Step 3: First Command (2 minutes)

### Option A: GUI (Recommended)

```bash
python run_gui.py
```

1. Click **📁 Open Folder**
2. Select any directory (e.g., `test_workspace`)
3. Type in AI bar: `"list all files"`
4. Click **Execute**
5. Approve the command
6. See results in terminal!

### Option B: Command Line

```bash
python test_query.py "list all files"
```

**Output:**
```
📋 Plan:
   Intent: file_list
   Command: cmd /c dir
   Explain: List all files

✅ Generated Plan:
{
  "version": "1.0",
  "intent": "file_list",
  "command": ["cmd", "/c", "dir"],
  ...
}
```

---

## Step 4: Create Your First File

### In GUI:
1. Type: `"create a file called hello.txt with hello world"`
2. Approve command
3. See file appear in browser
4. Click **📋 Changes** to see: `added: hello.txt`
5. Click **✓ Apply** to save to original directory

### In CLI:
```bash
python test_query.py "create hello.txt with hello world"
```

---

## Common First Commands

Try these to get familiar:

| Command | What It Does |
|---------|--------------|
| `"list all files"` | Shows directory contents |
| `"show contents of README.md"` | Displays file content |
| `"create test.txt with test"` | Creates new file |
| `"count lines in all python files"` | Analyzes code |
| `"find files larger than 1MB"` | Searches by size |

---

## Understanding the Workflow

```
1. Type Command (Natural Language)
        ↓
2. LLM Translates to Command
        ↓
3. Command Runs in SANDBOX (copy)
        ↓
4. Changes Detected
        ↓
5. Review Changes
        ↓
6. Apply or Discard
```

**Key Point:** Original directory stays untouched until you click "Apply"!

---

## Next Steps

- Read [README.md](../README.md) for full documentation
- Check [EXAMPLES.md](EXAMPLES.md) for use cases
- Review [API.md](API.md) for programmatic usage
- Explore [ARCHITECTURE.md](ARCHITECTURE.md) for system design

---

## Troubleshooting

### "HF_TOKEN is empty"
→ Create `CLAI/.env` with your token

### "Command not found"
→ Use Windows commands: `dir` not `ls`

### "No changes detected"
→ Make sure you're looking at sandbox, not original

### "LLM error"
→ Check internet connection and token validity

---

**You're all set!** Start using CLAI to make your command-line work easier and safer.

