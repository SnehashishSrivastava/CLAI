# CLAI - Command Line AI Assistant

A safe, intelligent command-line assistant that uses Large Language Models (LLMs) to translate natural language into executable commands, with built-in sandboxing, version control, and a modern GUI.

## 🎯 Overview

CLAI bridges the gap between natural language and command execution by:
- **Translating** user intent into structured command plans using LLMs
- **Sandboxing** all commands in isolated copies before execution
- **Logging** all operations for audit and analysis
- **Providing** a modern GUI for interactive use

### Key Features

✅ **AI-Powered Translation** - Natural language → Structured command plans  
✅ **Safe Execution** - All commands run in sandboxed copies first  
✅ **Version Control** - Git integration for change tracking  
✅ **Modern GUI** - Clean, intuitive interface with real-time feedback  
✅ **Comprehensive Logging** - All commands logged to `CLAI_logs.txt`  
✅ **Multi-LLM Support** - Hugging Face and OpenAI adapters  

---

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Components](#components)
- [Usage](#usage)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Development](#development)
- [Documentation](#documentation)

---

## 🚀 Installation

### Prerequisites

- Python 3.12+
- Git (for version control features)
- Hugging Face API token (or OpenAI API key)

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd CLAI
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   
   Create `CLAI/.env` file:
   ```env
   # Hugging Face Configuration
   HF_BASE_URL=https://router.huggingface.co
   HF_TOKEN=hf_your_token_here
   HF_MODEL=meta-llama/Llama-3.1-8B-Instruct
   
   # Optional: OpenAI Configuration
   # OPENAI_API_KEY=sk-your_key_here
   # OPENAI_BASE_URL=https://api.openai.com/v1
   # CLAI_OPENAI_MODEL=gpt-4.1-mini
   ```

4. **Verify installation**
   ```bash
   python test_llm_integration.py
   ```

---

## ⚡ Quick Start

### GUI Mode (Recommended)

```bash
cd CLAI
python run_gui.py
```

1. Click **📁 Open Folder** to select a directory
2. Type natural language commands in the **AI Assistant** bar
3. Review and approve commands
4. Use **Apply** to save changes or **Discard** to revert

### Command Line Mode

```bash
# Test a single query
python test_query.py "list all python files"

# Interactive sandbox session
python test_on_workspace.py
```

---

## 🏗️ Architecture

```
CLAI/
├── llm/                    # LLM Integration
│   ├── adapter_hf.py      # Hugging Face adapter
│   ├── adapter_openai.py   # OpenAI adapter
│   ├── config_hf.py       # HF configuration
│   ├── translator.py       # Prompt building
│   └── masking.py         # Security masking
│
├── prompt_builder/         # Prompt Engineering
│   ├── base_prompts.py    # System prompts
│   ├── few_shots.py       # Examples
│   ├── safety_policy.py   # Safety rules
│   └── schemas/           # JSON schemas
│
├── sandbox/                # Safe Execution
│   ├── session.py         # Persistent sandbox
│   ├── runner.py          # Command runner
│   ├── executor.py        # Execution orchestrator
│   ├── logger.py          # Logging system
│   └── git_control.py     # Version control
│
└── gui/                    # User Interface
    └── app.py             # Main GUI application
```

### Data Flow

```
User Input (Natural Language)
    ↓
LLM Translator (adapter_hf.py)
    ↓
Structured Plan (JSON)
    ↓
Sandbox Session (session.py)
    ↓
Command Execution (runner.py)
    ↓
Change Detection (git_control.py)
    ↓
User Approval → Apply/Discard
    ↓
Logger (logger.py) → CLAI_logs.txt
```

---

## 📦 Components

### 1. LLM Module (`llm/`)

Handles all interactions with language models.

#### `adapter_hf.py`
- Hugging Face API client
- OpenAI-compatible endpoint support
- Error handling and retries

#### `adapter_openai.py`
- OpenAI Responses API integration
- Structured output with JSON schemas
- Function calling support

#### `config_hf.py`
- Environment variable management
- Configuration loading from `.env` or JSON
- Model and endpoint selection

#### `translator.py`
- Builds system prompts
- Combines base prompts, safety rules, and few-shot examples
- Handles masking/unmasking of sensitive data

#### `masking.py`
- Removes sensitive tokens (emails, IPs, paths)
- Prevents data leakage to LLM
- Reversible unmasking for local logs

### 2. Prompt Builder (`prompt_builder/`)

Controls LLM output format and safety.

#### `base_prompts.py`
- System prompt template
- Command format rules
- Safety checklist

#### `few_shots.py`
- Example user queries and responses
- Demonstrates expected JSON structure
- Platform-specific examples (Windows/Linux)

#### `safety_policy.py`
- Denied command patterns
- Resource limits (CPU, memory, network)
- Risk assessment rules

#### `schemas/plan_v1.py`
- JSON schema for command plans
- Version: `1.0`
- Required fields: `version`, `intent`, `command`, `cwd`, `inputs`, `outputs`, `explain`

### 3. Sandbox Module (`sandbox/`)

Provides safe command execution.

#### `session.py` ⭐ Core Component
- **Persistent sandbox sessions**
- Creates copy of working directory
- Tracks all changes vs original
- Supports apply/discard workflow

**Key Methods:**
```python
session = SandboxSession(work_dir="/path/to/dir")
session.start()                    # Create sandbox copy
result = session.run_command(cmd)   # Execute in sandbox
changes = session.get_changes()     # Get diff
session.apply_changes()             # Apply to original
session.discard()                   # Discard changes
```

#### `runner.py`
- Command execution engine
- Timeout protection
- Resource limits
- Output capture

#### `executor.py`
- Orchestrates LLM → Sandbox → Logging
- Approval workflow
- Auto-approval for safe commands

#### `logger.py`
- Thread-safe logging
- Auto-creates `CLAI_logs.txt`
- Human-readable and JSON modes
- Logs: commands, outputs, git commits, timestamps

#### `git_control.py`
- Git repository management
- Snapshot creation
- Diff generation
- Rollback support

### 4. GUI Module (`gui/`)

Modern graphical interface.

#### `app.py`
- Main application window
- Directory browser
- AI command input
- Terminal panel
- Sandbox controls

**Features:**
- Real-time directory updates
- Colored terminal output
- Change visualization
- One-click apply/discard

---

## 💻 Usage

### GUI Usage

1. **Launch GUI**
   ```bash
   python run_gui.py
   ```

2. **Open a Directory**
   - Click "📁 Open Folder"
   - Select your working directory
   - Sandbox is created automatically

3. **Run Commands**
   
   **Via AI Assistant:**
   - Type: `"list all files"`
   - Review the generated command
   - Approve to execute
   
   **Via Terminal:**
   - Type: `dir` (Windows) or `ls` (Linux)
   - Press Enter or click "Run"
   - See output immediately

4. **Review Changes**
   - Click "📋 Changes" to see diff
   - Status bar shows change count

5. **Apply or Discard**
   - **Apply**: Saves changes to original directory
   - **Discard**: Throws away sandbox, keeps original

### Command Line Usage

#### Test LLM Connection
```bash
python test_llm_integration.py
```

#### Single Query
```bash
python test_query.py "create a file called hello.txt with hello world"
```

#### Interactive Session
```bash
python test_on_workspace.py
```

**Session Commands:**
- Type natural language → LLM translates → Execute
- `changes` - Show all changes
- `history` - Show command history
- `apply` - Apply changes to original
- `discard` - Discard all changes
- `quit` - Exit

### Programmatic Usage

```python
from CLAI.sandbox.session import SandboxSession
from CLAI.llm.adapter_hf import HFClient
from CLAI.llm.config_hf import get_hf_config

# Initialize
session = SandboxSession(work_dir="./my_project")
session.start()

# Get plan from LLM
config = get_hf_config()
client = HFClient(base=config["base"], token=config["token"], model=config["model"])
# ... build messages and get plan ...

# Execute in sandbox
result = session.run_plan(plan)

# Review changes
changes = session.get_changes()
print(f"Found {len(changes)} changes")

# Apply or discard
if user_approves:
    session.apply_changes()
else:
    session.discard()
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HF_BASE_URL` | Hugging Face router URL | `https://router.huggingface.co` |
| `HF_TOKEN` | Hugging Face API token | Required |
| `HF_MODEL` | Model identifier | `meta-llama/Llama-3.1-8B-Instruct` |
| `OPENAI_API_KEY` | OpenAI API key | Optional |
| `OPENAI_BASE_URL` | OpenAI endpoint | `https://api.openai.com/v1` |
| `CLAI_OPENAI_MODEL` | OpenAI model | `gpt-4.1-mini` |

### Configuration Files

**`.env`** (in `CLAI/` directory)
```env
HF_TOKEN=hf_xxxxxxxxxxxxx
HF_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

**`secrets.hf.json`** (alternative, in `CLAI/llm/`)
```json
{
  "HF_BASE_URL": "https://router.huggingface.co",
  "HF_TOKEN": "hf_xxxxxxxxxxxxx",
  "HF_MODEL": "meta-llama/Llama-3.1-8B-Instruct"
}
```

### Logging Configuration

Logs are written to `CLAI_logs.txt` in the parent directory of the CLAI package.

**Log Format:**
```
============================================================
[2025-11-30T15:30:45] Session: 20251130_153045
Query: list all files
Intent: file_list
Command: cmd /c dir
CWD: .
Mode: sandbox | Approved: True
Exit Code: 0 | Duration: 234ms
Git Before: abc12345
Git After: def67890
STDOUT:
file1.txt
file2.txt
============================================================
```

---

## 📚 API Reference

### SandboxSession

```python
class SandboxSession:
    def __init__(self, work_dir: Optional[str] = None, timeout: int = 60)
    def start() -> SessionState
    def run_command(command: List[str], cwd: str = ".") -> CommandResult
    def run_plan(plan: Dict[str, Any]) -> CommandResult
    def get_changes() -> List[FileChange]
    def show_changes() -> str
    def apply_changes() -> bool
    def discard()
    def is_active() -> bool
```

### HFClient

```python
class HFClient:
    def __init__(self, base=None, token=None, model=None)
    def chat_completions(messages, endpoint="/v1/chat/completions", **kwargs) -> dict
```

### CLAILogger

```python
class CLAILogger:
    def __init__(log_dir=None, log_file="CLAI_logs.txt", json_mode=False)
    def log_command(user_query, plan, exit_code, stdout, stderr, ...)
    def get_log_path() -> Path
```

### GitController

```python
class GitController:
    def __init__(work_dir: Optional[str] = None)
    def is_repo(path) -> bool
    def init_repo(path) -> bool
    def get_status(path) -> GitStatus
    def create_snapshot(message, path) -> Optional[str]
    def get_diff(from_commit, path) -> DiffResult
    def rollback(to_commit, path) -> bool
```

---

## 📖 Examples

### Example 1: List Files

**User Input:**
```
"show me all python files in this directory"
```

**LLM Output:**
```json
{
  "version": "1.0",
  "intent": "file_search",
  "command": ["cmd", "/c", "dir *.py"],
  "cwd": ".",
  "inputs": [],
  "outputs": [],
  "explain": "List all Python files in current directory"
}
```

**Execution:**
- Command runs in sandbox
- Output displayed in terminal
- No file changes → No apply needed

### Example 2: Create File

**User Input:**
```
"create a file called config.json with empty object"
```

**LLM Output:**
```json
{
  "version": "1.0",
  "intent": "file_create",
  "command": ["cmd", "/c", "echo {} > config.json"],
  "cwd": ".",
  "inputs": [],
  "outputs": ["config.json"],
  "explain": "Create config.json with empty JSON object"
}
```

**Execution:**
- Command runs in sandbox
- `config.json` created in sandbox
- Change detected: `added: config.json`
- User clicks "Apply" → File copied to original

### Example 3: Modify File

**User Input:**
```
"add a new line to README.md saying 'Updated by CLAI'"
```

**LLM Output:**
```json
{
  "version": "1.0",
  "intent": "file_modify",
  "command": ["cmd", "/c", "echo Updated by CLAI >> README.md"],
  "cwd": ".",
  "inputs": ["README.md"],
  "outputs": ["README.md"],
  "explain": "Append line to README.md"
}
```

**Execution:**
- Command runs in sandbox
- `README.md` modified in sandbox
- Change detected: `modified: README.md`
- Diff shown to user
- User clicks "Apply" → Changes copied to original

---

## 🔧 Development

### Project Structure

```
CLAI/
├── __init__.py
├── README.md
├── requirements.txt
├── Dockerfile
├── run_gui.py
│
├── llm/
│   ├── __init__.py
│   ├── adapter_hf.py
│   ├── adapter_openai.py
│   ├── config_hf.py
│   ├── masking.py
│   └── translator.py
│
├── prompt_builder/
│   ├── __init__.py
│   ├── base_prompts.py
│   ├── few_shots.py
│   ├── safety_policy.py
│   └── schemas/
│       └── plan_v1.py
│
├── sandbox/
│   ├── __init__.py
│   ├── session.py
│   ├── runner.py
│   ├── executor.py
│   ├── logger.py
│   └── git_control.py
│
└── gui/
    ├── __init__.py
    └── app.py
```

### Running Tests

```bash
# Full integration test
python test_llm_integration.py

# HF adapter test
python test_hf_adapter.py

# Environment test
python test_env_load.py

# Sandbox demo
python test_sandbox_session.py --demo
```

### Adding New LLM Adapters

1. Create `adapter_<provider>.py` in `llm/`
2. Implement `chat_completions(messages, **kwargs)` method
3. Return OpenAI-compatible response format
4. Update `__init__.py` to export new adapter

### Extending Prompt Builder

1. Add examples to `few_shots.py`
2. Update safety rules in `safety_policy.py`
3. Modify system prompt in `base_prompts.py`
4. Update schema in `schemas/plan_v1.py` if needed

---

## 🐳 Docker Support

### Build Image

```bash
docker build -t clai .
```

### Run Container

```bash
docker run -it \
  --env-file CLAI/.env \
  -v $(pwd)/workspace:/workspace \
  -v $(pwd)/CLAI_logs.txt:/app/CLAI_logs.txt \
  clai
```

### Docker Compose

```bash
docker-compose up
```

See `docker-compose.yml` for configuration.

---

## 🔒 Security

### Safety Features

- **Sandboxing**: All commands run in isolated copies
- **Masking**: Sensitive data removed before sending to LLM
- **Approval Workflow**: User must approve before execution
- **Change Review**: Diff shown before applying changes
- **Logging**: Complete audit trail of all operations

### Best Practices

1. **Review all commands** before approval
2. **Check diffs** before applying changes
3. **Use sandbox first** for destructive operations
4. **Keep logs** for compliance and debugging
5. **Rotate API keys** regularly

---

## 📝 Logging

All commands are logged to `CLAI_logs.txt` with:

- Timestamp
- Session ID
- User query
- Generated command
- Exit code and output
- Git commit hashes (before/after)
- Approval status
- Execution duration

**Log Location:**
- Default: Parent directory of CLAI package
- Configurable via `CLAILogger(log_dir=...)`

---

## 🐛 Troubleshooting

### LLM Connection Issues

**Problem:** "400 Bad Request" or connection timeout

**Solutions:**
- Check `HF_TOKEN` is set correctly
- Verify `HF_BASE_URL` is accessible
- Try different model: `HF_MODEL=meta-llama/Llama-3.1-8B-Instruct`
- Check network/firewall settings

### Sandbox Not Detecting Changes

**Problem:** Changes not showing in GUI

**Solutions:**
- Click "📋 Changes" to force refresh
- Check sandbox directory exists: `session.get_sandbox_path()`
- Verify files are in sandbox, not original
- Check `.gitignore` patterns aren't excluding files

### Commands Not Executing

**Problem:** Commands fail with "not found"

**Solutions:**
- Use Windows commands: `dir` not `ls`, `type` not `cat`
- Check command path is correct
- Verify sandbox directory is accessible
- Check terminal shows correct working directory

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

[Add your license here]

---

## 🙏 Acknowledgments

- Hugging Face for LLM infrastructure
- Meta for Llama models
- OpenAI for API design inspiration

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review test files for examples

---

## 📚 Documentation

Complete documentation is available in the `docs/` directory:

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design and data flow
- **[API.md](docs/API.md)** - Complete API reference
- **[EXAMPLES.md](docs/EXAMPLES.md)** - Practical usage examples

---

**Version:** 1.0.0  
**Last Updated:** November 2025
