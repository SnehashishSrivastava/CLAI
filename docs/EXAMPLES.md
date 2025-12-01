# CLAI Usage Examples

Practical examples for common use cases.

---

## Example 1: Basic File Operations

### List Files

**GUI:**
1. Open folder
2. Type in AI bar: `"show me all files"`
3. Approve command
4. See output in terminal

**CLI:**
```bash
python test_query.py "list all files"
```

**Output:**
```
📋 Plan:
   Intent: file_list
   Command: cmd /c dir
   Explain: List all files in directory

✅ Command succeeded
file1.txt
file2.txt
script.py
```

### Create File

**Query:** `"create a file called notes.txt with 'Meeting notes'`

**Generated Command:**
```json
{
  "command": ["cmd", "/c", "echo Meeting notes > notes.txt"],
  "outputs": ["notes.txt"]
}
```

**Result:**
- File created in sandbox
- Change detected: `added: notes.txt`
- Click "Apply" to save to original

### Read File

**Query:** `"show contents of README.md"`

**Generated Command:**
```json
{
  "command": ["cmd", "/c", "type README.md"],
  "inputs": ["README.md"]
}
```

---

## Example 2: File Search

### Find Python Files

**Query:** `"find all python files in this directory"`

**Generated Command:**
```json
{
  "command": ["cmd", "/c", "dir *.py /s"],
  "intent": "file_search"
}
```

### Find Large Files

**Query:** `"show files larger than 1MB"`

**Generated Command:**
```json
{
  "command": ["powershell", "-c", "Get-ChildItem -Recurse | Where-Object {$_.Length -gt 1MB}"]
}
```

---

## Example 3: Batch Operations

### Rename Multiple Files

**Query:** `"rename all .txt files to .bak"`

**Generated Command:**
```json
{
  "command": ["powershell", "-c", "Get-ChildItem *.txt | Rename-Item -NewName {$_.Name -replace '.txt','.bak'}"]
}
```

**Workflow:**
1. Command runs in sandbox
2. Multiple files renamed
3. Changes shown: `modified: file1.bak, file2.bak`
4. Review diff
5. Apply if correct

---

## Example 4: Project Setup

### Initialize Project

**Query:** `"create a new python project with requirements.txt and README.md"`

**Generated Commands:**
```json
[
  {
    "command": ["cmd", "/c", "echo # Project > README.md"],
    "outputs": ["README.md"]
  },
  {
    "command": ["cmd", "/c", "echo requests > requirements.txt"],
    "outputs": ["requirements.txt"]
  }
]
```

**Result:**
- Multiple files created
- All changes in sandbox
- Apply all at once

---

## Example 5: Code Analysis

### Count Lines

**Query:** `"count lines of code in all python files"`

**Generated Command:**
```json
{
  "command": ["powershell", "-c", "(Get-ChildItem *.py | Get-Content | Measure-Object -Line).Lines"]
}
```

### Find TODO Comments

**Query:** `"find all TODO comments in code"`

**Generated Command:**
```json
{
  "command": ["cmd", "/c", "findstr /s /i TODO *.py"]
}
```

---

## Example 6: Safe Deletion

### Delete Old Logs

**Query:** `"delete log files older than 7 days"`

**LLM Response:**
```json
{
  "needs_clarification": true,
  "question": "Which directory? Confirm deletion of old logs?"
}
```

**Safety Check:**
- Deletion detected
- Requires clarification
- User must confirm

**After Confirmation:**
```json
{
  "command": ["powershell", "-c", "Get-ChildItem *.log | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item"]
}
```

---

## Example 7: Git Operations

### Check Status

**Query:** `"show git status"`

**Generated Command:**
```json
{
  "command": ["git", "status"]
}
```

**Note:** Git operations run in sandbox, but changes tracked separately.

### Create Commit

**Query:** `"commit all changes with message 'Update files'"`

**Generated Command:**
```json
{
  "command": ["git", "add", "-A", "&&", "git", "commit", "-m", "Update files"]
}
```

---

## Example 8: Environment Setup

### Create Virtual Environment

**Query:** `"create a python virtual environment"`

**Generated Command:**
```json
{
  "command": ["python", "-m", "venv", "venv"]
}
```

**Result:**
- `venv/` directory created in sandbox
- Review before applying
- Apply to add to project

---

## Example 9: Configuration Management

### Update Config File

**Query:** `"add DEBUG=True to config.py"`

**Generated Command:**
```json
{
  "command": ["cmd", "/c", "echo DEBUG=True >> config.py"],
  "inputs": ["config.py"],
  "outputs": ["config.py"]
}
```

**Workflow:**
1. File modified in sandbox
2. Diff shows added line
3. Review change
4. Apply if correct

---

## Example 10: Multi-Step Workflow

### Setup New Feature Branch

**User Actions:**
1. `"create new branch called feature-x"`
2. `"create feature.py with basic structure"`
3. `"add feature.py to git"`
4. `"commit with message 'Add feature-x'"`

**Each Step:**
- Runs in sandbox
- Changes accumulate
- Review all at end
- Apply once when ready

---

## Advanced Patterns

### Pattern 1: Conditional Execution

```python
# User: "if file exists, delete it"
# LLM generates:
{
  "command": ["cmd", "/c", "if exist file.txt del file.txt"]
}
```

### Pattern 2: Piped Commands

```python
# User: "list files and count them"
# LLM generates:
{
  "command": ["cmd", "/c", "dir | find /c /v \"\""]
}
```

### Pattern 3: Error Handling

```python
# User: "try to compile, show errors if any"
# LLM generates:
{
  "command": ["python", "-m", "py_compile", "script.py"]
}
# Errors shown in stderr
```

---

## Common Pitfalls

### ❌ Don't Do This

```python
# Direct execution without sandbox
subprocess.run(["rm", "-rf", "/"])  # DANGEROUS!
```

### ✅ Do This Instead

```python
# Use CLAI sandbox
session = SandboxSession(work_dir="./project")
session.start()
result = session.run_command(["cmd", "/c", "dir"])
# Review changes
session.apply_changes()  # Safe!
```

---

## Tips & Tricks

1. **Use descriptive queries** - Better LLM understanding
2. **Review before apply** - Always check changes
3. **Use terminal for quick commands** - Faster than AI
4. **Combine operations** - Multiple commands in one session
5. **Check logs** - `CLAI_logs.txt` has full history

---

## Troubleshooting Examples

### Command Not Found

**Problem:** `'ls' is not recognized`

**Solution:** Use Windows commands
- `ls` → `dir`
- `cat` → `type`
- `rm` → `del`

**Or:** Let AI translate automatically:
- User: `"list files"` → AI: `["cmd", "/c", "dir"]`

### Changes Not Detected

**Problem:** File created but not showing in changes

**Solution:**
1. Check sandbox path is correct
2. Verify file is in sandbox, not original
3. Click "Show Changes" to force refresh
4. Check `.gitignore` patterns

### LLM Returns Invalid JSON

**Problem:** `JSONDecodeError`

**Solution:**
1. Check LLM response in terminal
2. Try rephrasing query
3. Use simpler commands
4. Check model is compatible

---

## Integration Examples

### With CI/CD

```python
# In CI script
from CLAI.sandbox.session import SandboxSession

session = SandboxSession(work_dir="./build")
session.start()
session.run_command(["python", "setup.py", "build"])
changes = session.get_changes()
if changes:
    session.apply_changes()
```

### With Web API

```python
# Flask endpoint
@app.route("/execute", methods=["POST"])
def execute():
    query = request.json["query"]
    plan = get_llm_plan(query)
    result = session.run_plan(plan)
    return jsonify({
        "success": result.success,
        "output": result.stdout,
        "changes": len(session.get_changes())
    })
```

---

## Performance Examples

### Batch Processing

```python
# Process multiple commands efficiently
session = SandboxSession(work_dir="./data")
session.start()

commands = [
    "process file1.txt",
    "process file2.txt",
    "process file3.txt"
]

for cmd in commands:
    plan = get_plan(cmd)
    session.run_plan(plan)

# Apply all at once
session.apply_changes()
```

### Parallel Execution

```python
# Run independent commands in parallel
import threading

def run_cmd(cmd):
    plan = get_plan(cmd)
    return session.run_plan(plan)

threads = [
    threading.Thread(target=run_cmd, args=(cmd,))
    for cmd in commands
]

for t in threads:
    t.start()
for t in threads:
    t.join()
```

---

**For more examples, see test files:**
- `test_query.py` - Single query examples
- `test_on_workspace.py` - Interactive session
- `test_llm_integration.py` - Full integration test

