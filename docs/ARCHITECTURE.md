# CLAI Architecture Documentation

## System Overview

CLAI is built on a modular architecture that separates concerns into distinct layers:

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │     GUI      │  │   Terminal   │  │   Programmatic│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  Execution Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Executor   │  │   Runner     │  │   Session   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  Translation Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Translator  │  │ Prompt Builder│  │   Adapter   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                    LLM Layer                             │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │ Hugging Face │  │   OpenAI     │                    │
│  └──────────────┘  └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### 1. User Interface Layer

**Purpose:** Provide multiple ways to interact with CLAI

**Components:**
- **GUI (`gui/app.py`)**: Modern Tkinter-based interface
- **CLI Scripts**: `test_query.py`, `test_on_workspace.py`
- **Programmatic API**: Direct Python imports

**Responsibilities:**
- User input collection
- Command approval workflow
- Result visualization
- Change review interface

### 2. Execution Layer

**Purpose:** Safely execute commands and manage state

#### 2.1 SandboxSession (`sandbox/session.py`)

**Core Component** - Manages persistent sandbox copies

**State Machine:**
```
INACTIVE → start() → ACTIVE → apply_changes() → INACTIVE
                ↓
            discard() → INACTIVE
```

**Key Operations:**
1. **start()**: Creates copy of original directory
2. **run_command()**: Executes command in sandbox
3. **get_changes()**: Compares sandbox vs original
4. **apply_changes()**: Copies changes to original
5. **discard()**: Deletes sandbox, keeps original

**Data Structures:**
```python
@dataclass
class SessionState:
    session_id: str
    original_dir: Path
    sandbox_dir: Path
    created_at: str
    command_history: List[CommandResult]
    is_active: bool

@dataclass
class CommandResult:
    command: List[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timestamp: str
    success: bool

@dataclass
class FileChange:
    path: str
    change_type: str  # "added", "modified", "deleted"
    diff_lines: Optional[List[str]]
```

#### 2.2 Runner (`sandbox/runner.py`)

**Purpose:** Execute commands with safety limits

**Features:**
- Timeout protection (default: 30s)
- Output size limits (1MB)
- Resource constraints
- Error handling

**Execution Modes:**
- `DRY_RUN`: Preview only, no execution
- `SANDBOX`: Execute in isolated copy
- `LIVE`: Execute directly (with confirmation)

#### 2.3 Executor (`sandbox/executor.py`)

**Purpose:** Orchestrate full workflow

**Workflow:**
```
User Query
    ↓
LLM Translation
    ↓
Plan Validation
    ↓
Safety Check
    ↓
User Approval
    ↓
Sandbox Execution
    ↓
Change Detection
    ↓
Apply/Discard Decision
    ↓
Logging
```

### 3. Translation Layer

**Purpose:** Convert natural language to structured commands

#### 3.1 Translator (`llm/translator.py`)

**Process:**
1. Load system prompt from `base_prompts.py`
2. Add safety policy from `safety_policy.py`
3. Include few-shot examples from `few_shots.py`
4. Apply masking to sensitive data
5. Send to LLM adapter
6. Parse and validate JSON response

**Masking:**
- Emails: `user@example.com` → `__EMAIL_1__`
- IPs: `192.168.1.1` → `__IP_1__`
- Paths: `/home/user/file` → `__PATH_1__`

#### 3.2 Prompt Builder (`prompt_builder/`)

**Modular Prompt System:**

```
SYSTEM_PROMPT (base_prompts.py)
    +
SAFETY_POLICY (safety_policy.py)
    +
FEW_SHOT_EXAMPLES (few_shots.py)
    +
JSON_SCHEMA (schemas/plan_v1.py)
    =
FINAL_PROMPT
```

**Schema Validation:**
- Required fields checked
- Type validation
- Version compatibility
- Command format verification

### 4. LLM Layer

**Purpose:** Interface with language models

#### 4.1 HF Adapter (`llm/adapter_hf.py`)

**Endpoint:** Hugging Face Router API

**Request Format:**
```json
{
  "model": "meta-llama/Llama-3.1-8B-Instruct",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "max_tokens": 500,
  "temperature": 0.1
}
```

**Response Format:**
```json
{
  "choices": [{
    "message": {
      "content": "{\"version\":\"1.0\",\"command\":[...]}"
    }
  }]
}
```

#### 4.2 OpenAI Adapter (`llm/adapter_openai.py`)

**Uses:** OpenAI Responses API with function calling

**Advantages:**
- Structured output guaranteed
- Schema enforcement
- Better JSON compliance

### 5. Support Systems

#### 5.1 Logger (`sandbox/logger.py`)

**Thread-Safe Logging:**
- Uses `threading.Lock()` for concurrent access
- Auto-creates log file if missing
- Supports human-readable and JSON modes

**Log Entry Structure:**
```python
LogEntry(
    timestamp: str
    session_id: str
    user_query: str
    plan_version: str
    intent: str
    command: List[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    sandbox_mode: str
    git_commit_before: str
    git_commit_after: str
    approved: bool
    error: Optional[str]
)
```

#### 5.2 Git Controller (`sandbox/git_control.py`)

**Features:**
- Repository detection
- Snapshot creation
- Diff generation
- Rollback support

**Git Operations:**
```python
git.init_repo()           # Initialize repository
git.create_snapshot()     # Commit current state
git.get_diff()            # Get changes
git.rollback()            # Revert to commit
```

## Data Flow Examples

### Example 1: Simple File List

```
User: "list all files"
    ↓
GUI → AICommandBar._on_ai_command()
    ↓
CLAIApp._get_llm_plan()
    ↓
HFClient.chat_completions()
    ↓
LLM Response: {"command": ["cmd", "/c", "dir"]}
    ↓
CLAIApp._execute_plan()
    ↓
SandboxSession.run_plan()
    ↓
subprocess.run() in sandbox
    ↓
Output displayed in terminal
    ↓
No file changes → No apply needed
```

### Example 2: File Creation with Apply

```
User: "create hello.txt"
    ↓
[Same translation flow...]
    ↓
Command: echo hello > hello.txt
    ↓
Executed in sandbox
    ↓
File created: .clai_sandbox_xxx/hello.txt
    ↓
get_changes() detects: added: hello.txt
    ↓
GUI shows: "🟡 1 changes"
    ↓
User clicks "Apply"
    ↓
apply_changes() copies hello.txt to original
    ↓
New sandbox session started
```

## Security Architecture

### Sandbox Isolation

```
Original Directory: /project/
    ↓ (copy)
Sandbox: /project/.clai_sandbox_project_20251130_153045/
    ↓ (commands execute here)
Changes detected
    ↓ (user approval)
Applied to: /project/
```

### Masking Pipeline

```
User Input: "Send email to user@example.com"
    ↓
mask_text()
    ↓
Masked: "Send email to __EMAIL_1__"
    ↓
Sent to LLM
    ↓
Response received
    ↓
deep_unmask() (for local logs only)
```

### Safety Checks

1. **Command Validation**
   - Check against allowlist
   - Detect dangerous patterns
   - Verify command structure

2. **Resource Limits**
   - Timeout: 30s default
   - Output size: 1MB max
   - Memory limits (future)

3. **Change Review**
   - Show diff before apply
   - List all changed files
   - Require explicit approval

## Error Handling

### LLM Errors
- Invalid JSON → Retry with clearer prompt
- Timeout → Show error, allow retry
- API error → Log and notify user

### Execution Errors
- Command not found → Show helpful message
- Permission denied → Log and continue
- Timeout → Kill process, show error

### Sandbox Errors
- Copy failure → Retry or show error
- Apply failure → Keep sandbox, show error
- Cleanup failure → Log warning

## Performance Considerations

### Caching
- Prompt templates cached in memory
- Config loaded once at startup
- LLM responses not cached (always fresh)

### Concurrency
- Logger uses locks for thread safety
- GUI updates on main thread
- LLM calls in background threads

### Resource Usage
- Sandbox copies: ~same size as original
- Memory: Minimal (Python overhead)
- Network: Only for LLM calls

## Extension Points

### Adding New LLM Providers

1. Create `adapter_<provider>.py`
2. Implement `chat_completions()` method
3. Return OpenAI-compatible format
4. Add to `__init__.py`

### Adding New Command Types

1. Update `few_shots.py` with examples
2. Add to `safety_policy.py` if needed
3. Update schema in `plan_v1.py` if structure changes

### Custom Logging

1. Subclass `CLAILogger`
2. Override `log()` method
3. Add custom fields to `LogEntry`

## Future Enhancements

### Planned Features
- [ ] Docker sandbox support
- [ ] Network isolation
- [ ] Resource quotas (CPU, memory)
- [ ] Command history search
- [ ] Multi-session support
- [ ] Cloud sync for logs
- [ ] Plugin system

### Performance Improvements
- [ ] Incremental sandbox updates
- [ ] Parallel command execution
- [ ] Response caching
- [ ] Lazy loading

