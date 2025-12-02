# file: CLAI/sandbox/logger.py
# Logging system for CLAI - records all executed commands

from __future__ import annotations
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import threading

# Default log file name
DEFAULT_LOG_FILE = "CLAI_logs.txt"


@dataclass
class LogEntry:
    """Single log entry for a command execution."""
    timestamp: str
    session_id: str
    user_query: str
    plan_version: str
    intent: str
    command: list[str]
    cwd: str
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    duration_ms: Optional[float]
    sandbox_mode: str  # "sandbox", "live", "dry_run"
    git_commit_before: Optional[str]
    git_commit_after: Optional[str]
    approved: bool
    error: Optional[str]
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)
    
    def to_human_readable(self) -> str:
        """Format for human-readable log."""
        lines = [
            f"{'='*60}",
            f"[{self.timestamp}] Session: {self.session_id}",
            f"Query: {self.user_query}",
            f"Intent: {self.intent}",
            f"Command: {' '.join(self.command)}",
            f"CWD: {self.cwd}",
            f"Mode: {self.sandbox_mode} | Approved: {self.approved}",
        ]
        if self.exit_code is not None:
            lines.append(f"Exit Code: {self.exit_code} | Duration: {self.duration_ms:.0f}ms" if self.duration_ms else f"Exit Code: {self.exit_code}")
        if self.git_commit_before:
            lines.append(f"Git Before: {self.git_commit_before[:8]}")
        if self.git_commit_after:
            lines.append(f"Git After: {self.git_commit_after[:8]}")
        if self.stdout:
            lines.append(f"STDOUT:\n{self.stdout[:500]}{'...' if len(self.stdout) > 500 else ''}")
        if self.stderr:
            lines.append(f"STDERR:\n{self.stderr[:300]}{'...' if len(self.stderr) > 300 else ''}")
        if self.error:
            lines.append(f"ERROR: {self.error}")
        lines.append(f"{'='*60}\n")
        return "\n".join(lines)


class CLAILogger:
    """
    Thread-safe logger for CLAI command executions.
    Auto-creates log file in parent directory if not exists.
    """
    
    _lock = threading.Lock()
    
    def __init__(
        self, 
        log_dir: Optional[str] = None,
        log_file: str = DEFAULT_LOG_FILE,
        json_mode: bool = False
    ):
        """
        Initialize logger.
        
        Args:
            log_dir: Directory for log file. Defaults to current working directory.
            log_file: Name of log file.
            json_mode: If True, log as JSON lines. If False, human-readable.
        """
        if log_dir is None:
            # Default to current working directory (where CLAI is being used)
            log_dir = str(Path.cwd())
        
        self.log_dir = Path(log_dir)
        self.log_file = log_file
        self.log_path = self.log_dir / log_file
        self.json_mode = json_mode
        self.session_id = self._generate_session_id()
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with header if it doesn't exist
        self._ensure_log_file()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _ensure_log_file(self):
        """Create log file with header if it doesn't exist."""
        if not self.log_path.exists():
            with open(self.log_path, "w", encoding="utf-8") as f:
                header = [
                    "#" * 60,
                    "# CLAI Command Execution Log",
                    f"# Created: {datetime.now().isoformat()}",
                    f"# Format: {'JSON Lines' if self.json_mode else 'Human Readable'}",
                    "#" * 60,
                    "",
                ]
                f.write("\n".join(header))
            print(f"📁 Created log file: {self.log_path}")
    
    def log(self, entry: LogEntry):
        """Write a log entry (thread-safe)."""
        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                if self.json_mode:
                    f.write(entry.to_json() + "\n")
                else:
                    f.write(entry.to_human_readable())
    
    def log_command(
        self,
        user_query: str,
        plan: Dict[str, Any],
        exit_code: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        duration_ms: Optional[float] = None,
        sandbox_mode: str = "sandbox",
        git_before: Optional[str] = None,
        git_after: Optional[str] = None,
        approved: bool = False,
        error: Optional[str] = None,
    ):
        """
        Convenience method to log a command execution.
        
        Args:
            user_query: Original natural language query
            plan: The plan dict from LLM
            exit_code: Command exit code (None if not executed)
            stdout: Standard output
            stderr: Standard error
            duration_ms: Execution time in milliseconds
            sandbox_mode: "sandbox", "live", or "dry_run"
            git_before: Git commit hash before execution
            git_after: Git commit hash after execution
            approved: Whether user approved the command
            error: Error message if something went wrong
        """
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            user_query=user_query,
            plan_version=plan.get("version", "unknown"),
            intent=plan.get("intent", "unknown"),
            command=plan.get("command", []),
            cwd=plan.get("cwd", "."),
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            sandbox_mode=sandbox_mode,
            git_commit_before=git_before,
            git_commit_after=git_after,
            approved=approved,
            error=error,
        )
        self.log(entry)
        return entry
    
    def get_log_path(self) -> Path:
        """Return the path to the log file."""
        return self.log_path
    
    def read_recent(self, n: int = 10) -> str:
        """Read last n entries from log (approximate for human-readable mode)."""
        if not self.log_path.exists():
            return "Log file not found."
        
        with open(self.log_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if self.json_mode:
            lines = [l for l in content.strip().split("\n") if l and not l.startswith("#")]
            return "\n".join(lines[-n:])
        else:
            # Split by entry separator
            entries = content.split("=" * 60)
            recent = entries[-(n*2+1):]  # Each entry has 2 separators
            return ("=" * 60).join(recent)


