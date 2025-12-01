# CLAI API Reference

Complete API documentation for all public classes and methods.

---

## LLM Module

### `HFClient`

Hugging Face API client for LLM interactions.

```python
from CLAI.llm.adapter_hf import HFClient
from CLAI.llm.config_hf import get_hf_config

config = get_hf_config()
client = HFClient(
    base=config["base"],
    token=config["token"],
    model=config["model"]
)
```

#### Methods

##### `__init__(self, base=None, token=None, model=None)`

Initialize HF client.

**Parameters:**
- `base` (str, optional): Base URL for HF router. Defaults to config.
- `token` (str, optional): API token. Defaults to config.
- `model` (str, optional): Model identifier. Defaults to config.

##### `chat_completions(self, messages, endpoint="/v1/chat/completions", **kwargs) -> dict`

Send chat completion request.

**Parameters:**
- `messages` (List[Dict]): Conversation messages
- `endpoint` (str): API endpoint path
- `**kwargs`: Additional parameters (max_tokens, temperature, etc.)

**Returns:**
- `dict`: OpenAI-compatible response

**Example:**
```python
response = client.chat_completions(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "List files"}
    ],
    max_tokens=500,
    temperature=0.1
)
```

---

### `OpenAITranslator`

OpenAI adapter with structured output support.

```python
from CLAI.llm.adapter_openai import OpenAITranslator

translator = OpenAITranslator()
result = translator.translate("list all files")
```

#### Methods

##### `translate(self, nl_request: str, extra_context: Optional[dict] = None) -> TranslationResult`

Translate natural language to command plan.

**Parameters:**
- `nl_request` (str): User's natural language query
- `extra_context` (dict, optional): Additional context

**Returns:**
- `TranslationResult`: Contains `plan` (dict) and `raw_response` (dict)

---

### `get_hf_config() -> dict`

Load Hugging Face configuration.

**Returns:**
- `dict`: Configuration with keys `base`, `token`, `model`

**Priority:**
1. Environment variables
2. `secrets.hf.json` file
3. Defaults

---

## Sandbox Module

### `SandboxSession`

Persistent sandbox session manager.

```python
from CLAI.sandbox.session import SandboxSession

session = SandboxSession(work_dir="./my_project")
```

#### Methods

##### `start(self) -> SessionState`

Create a new sandbox session by copying the working directory.

**Returns:**
- `SessionState`: Session information

**Side Effects:**
- Creates sandbox directory: `.clai_sandbox_<dirname>_<timestamp>`
- Copies all files (excluding ignored patterns)

##### `run_command(self, command: List[str], cwd: str = ".") -> CommandResult`

Execute a command in the sandbox.

**Parameters:**
- `command` (List[str]): Command as list of strings
- `cwd` (str): Working directory relative to sandbox

**Returns:**
- `CommandResult`: Execution result with stdout, stderr, exit_code

**Example:**
```python
result = session.run_command(["cmd", "/c", "dir"])
print(result.stdout)
print(f"Exit code: {result.exit_code}")
```

##### `run_plan(self, plan: Dict[str, Any]) -> CommandResult`

Execute a command plan from LLM.

**Parameters:**
- `plan` (dict): Plan with `command` and `cwd` keys

**Returns:**
- `CommandResult`: Execution result

##### `get_changes(self) -> List[FileChange]`

Compare sandbox with original directory.

**Returns:**
- `List[FileChange]`: List of changes (added, modified, deleted)

**Example:**
```python
changes = session.get_changes()
for change in changes:
    print(f"{change.change_type}: {change.path}")
```

##### `show_changes(self) -> str`

Get human-readable summary of changes.

**Returns:**
- `str`: Formatted change summary

##### `apply_changes(self) -> bool`

Apply sandbox changes to original directory.

**Returns:**
- `bool`: True if successful

**Side Effects:**
- Copies changed files from sandbox to original
- Deletes files that were removed in sandbox
- Ends current session

##### `discard(self)`

Discard sandbox and all changes.

**Side Effects:**
- Deletes sandbox directory
- Original directory unchanged
- Ends current session

##### `is_active(self) -> bool`

Check if session is currently active.

**Returns:**
- `bool`: True if sandbox exists and is active

##### `get_sandbox_path(self) -> Optional[Path]`

Get path to sandbox directory.

**Returns:**
- `Optional[Path]`: Path object or None

---

### `SandboxRunner`

One-off command execution runner.

```python
from CLAI.sandbox.runner import SandboxRunner, ExecutionMode

runner = SandboxRunner(work_dir="./project")
result = runner.execute(plan, mode=ExecutionMode.SANDBOX)
```

#### Methods

##### `execute(self, plan: Dict[str, Any], mode: ExecutionMode) -> ExecutionResult`

Execute a command plan.

**Parameters:**
- `plan` (dict): Command plan
- `mode` (ExecutionMode): DRY_RUN, SANDBOX, or LIVE

**Returns:**
- `ExecutionResult`: Complete execution details

---

### `CLAILogger`

Thread-safe logging system.

```python
from CLAI.sandbox.logger import CLAILogger

logger = CLAILogger(log_dir="./logs", log_file="CLAI_logs.txt")
```

#### Methods

##### `log_command(self, user_query: str, plan: dict, exit_code: int, ...)`

Log a command execution.

**Parameters:**
- `user_query` (str): Original user input
- `plan` (dict): Command plan
- `exit_code` (int): Command exit code
- `stdout` (str): Standard output
- `stderr` (str): Standard error
- `duration_ms` (float): Execution time
- `sandbox_mode` (str): Execution mode
- `git_before` (str, optional): Git commit before
- `git_after` (str, optional): Git commit after
- `approved` (bool): User approval status
- `error` (str, optional): Error message

##### `get_log_path(self) -> Path`

Get path to log file.

**Returns:**
- `Path`: Log file path

---

### `GitController`

Git repository management.

```python
from CLAI.sandbox.git_control import GitController

git = GitController(work_dir="./project")
```

#### Methods

##### `is_repo(self, path: Optional[Path] = None) -> bool`

Check if directory is a git repository.

##### `init_repo(self, path: Optional[Path] = None) -> bool`

Initialize a new git repository.

##### `get_status(self, path: Optional[Path] = None) -> GitStatus`

Get current git status.

**Returns:**
- `GitStatus`: Status with branch, commit, modified files

##### `create_snapshot(self, message: str, path: Optional[Path] = None) -> Optional[str]`

Create a git snapshot (commit).

**Returns:**
- `Optional[str]`: Commit hash if successful

##### `get_diff(self, from_commit: Optional[str] = None, path: Optional[Path] = None) -> DiffResult`

Get diff between commits or working directory.

**Returns:**
- `DiffResult`: Diff with files changed, insertions, deletions

##### `rollback(self, to_commit: str, path: Optional[Path] = None) -> bool`

Rollback to a specific commit.

**Warning:** Discards all changes after the commit!

---

## GUI Module

### `CLAIApp`

Main GUI application class.

```python
from CLAI.gui.app import CLAIApp

app = CLAIApp()
app.run()
```

#### Methods

##### `run(self)`

Start the GUI application and enter main loop.

---

## Data Classes

### `CommandResult`

```python
@dataclass
class CommandResult:
    command: List[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timestamp: str
    success: bool
```

### `FileChange`

```python
@dataclass
class FileChange:
    path: str
    change_type: str  # "added", "modified", "deleted"
    diff_lines: Optional[List[str]]
```

### `SessionState`

```python
@dataclass
class SessionState:
    session_id: str
    original_dir: Path
    sandbox_dir: Path
    created_at: str
    command_history: List[CommandResult]
    is_active: bool
```

### `GitStatus`

```python
@dataclass
class GitStatus:
    is_repo: bool
    branch: Optional[str]
    commit_hash: Optional[str]
    is_clean: bool
    modified_files: List[str]
    untracked_files: List[str]
```

### `DiffResult`

```python
@dataclass
class DiffResult:
    has_changes: bool
    diff_text: str
    files_changed: List[str]
    insertions: int
    deletions: int
```

---

## Constants

### Plan Schema

```python
PLAN_VERSION = "1.0"
PLAN_FN_NAME = "emit_plan_v1"
```

### Safety Policy

```python
SAFETY_POLICY = {
    "limits": {
        "cpu_seconds": 20,
        "memory_mb": 512,
        "network": False,
        "file_write": False
    },
    "deny_keywords": [
        " rm ", " mkfs", " dd ", " shutdown", " reboot"
    ]
}
```

---

## Error Handling

### Common Exceptions

- `RuntimeError`: Sandbox session not active
- `ValueError`: Invalid configuration or plan
- `FileNotFoundError`: Command or file not found
- `subprocess.TimeoutExpired`: Command timeout
- `json.JSONDecodeError`: Invalid LLM response

### Error Recovery

Most errors are logged and displayed to user. Critical errors may require:
- Restarting sandbox session
- Checking configuration
- Verifying LLM connectivity

---

## Examples

### Complete Workflow

```python
from CLAI.sandbox.session import SandboxSession
from CLAI.llm.adapter_hf import HFClient
from CLAI.llm.config_hf import get_hf_config
from CLAI.sandbox.logger import CLAILogger

# Setup
config = get_hf_config()
client = HFClient(**config)
logger = CLAILogger()
session = SandboxSession(work_dir="./project")

# Start session
session.start()

# Get plan from LLM
messages = [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "list all files"}
]
response = client.chat_completions(messages)
plan = json.loads(response["choices"][0]["message"]["content"])

# Execute
result = session.run_plan(plan)

# Log
logger.log_command(
    user_query="list all files",
    plan=plan,
    exit_code=result.exit_code,
    stdout=result.stdout,
    stderr=result.stderr,
    duration_ms=result.duration_ms,
    sandbox_mode="sandbox",
    approved=True
)

# Review changes
changes = session.get_changes()
if changes:
    print(f"Found {len(changes)} changes")
    if user_approves:
        session.apply_changes()
    else:
        session.discard()
```

---

## Best Practices

1. **Always check session state** before operations
2. **Review changes** before applying
3. **Handle errors gracefully** with try/except
4. **Log all operations** for debugging
5. **Use sandbox first** for destructive commands
6. **Validate plans** before execution
7. **Clean up sessions** when done

