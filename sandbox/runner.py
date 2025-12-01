# file: CLAI/sandbox/runner.py
# Sandbox runner for safe command execution

from __future__ import annotations
import os
import subprocess
import time
import signal
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

from .git_control import GitController, DiffResult


class ExecutionMode(Enum):
    """Execution mode for commands."""
    DRY_RUN = "dry_run"      # Don't execute, just show what would happen
    SANDBOX = "sandbox"      # Execute in isolated temp directory
    LIVE = "live"            # Execute in actual directory (with confirmation)


@dataclass
class ExecutionResult:
    """Result of a command execution."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    command: List[str]
    cwd: str
    mode: ExecutionMode
    git_before: Optional[str]
    git_after: Optional[str]
    diff: Optional[DiffResult]
    error: Optional[str]
    
    def summary(self) -> str:
        """Get a human-readable summary."""
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        lines = [
            f"{status} (exit code: {self.exit_code})",
            f"Command: {' '.join(self.command)}",
            f"Duration: {self.duration_ms:.0f}ms",
            f"Mode: {self.mode.value}",
        ]
        if self.stdout:
            lines.append(f"\n📤 STDOUT:\n{self.stdout[:1000]}{'...' if len(self.stdout) > 1000 else ''}")
        if self.stderr:
            lines.append(f"\n📥 STDERR:\n{self.stderr[:500]}{'...' if len(self.stderr) > 500 else ''}")
        if self.diff and self.diff.has_changes:
            lines.append(f"\n📝 Changes: {len(self.diff.files_changed)} files (+{self.diff.insertions}/-{self.diff.deletions})")
        if self.error:
            lines.append(f"\n⚠️ Error: {self.error}")
        return "\n".join(lines)


class SandboxRunner:
    """
    Executes commands in a sandboxed environment.
    
    Features:
    - Dry run mode (preview without execution)
    - Sandbox mode (execute in temp directory copy)
    - Live mode (execute with git snapshots)
    - Timeout protection
    - Resource limits
    """
    
    # Default safety limits
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_OUTPUT_SIZE = 1024 * 1024  # 1MB
    
    def __init__(
        self,
        work_dir: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize SandboxRunner.
        
        Args:
            work_dir: Working directory for execution.
            timeout: Maximum execution time in seconds.
        """
        self.work_dir = Path(work_dir) if work_dir else Path.cwd()
        self.timeout = timeout
        self.git = GitController(str(self.work_dir))
        self._sandbox_path: Optional[Path] = None
    
    def _is_windows(self) -> bool:
        """Check if running on Windows."""
        return os.name == 'nt'
    
    def _prepare_command(self, command: List[str]) -> Tuple[List[str], bool]:
        """
        Prepare command for execution.
        
        Returns:
            Tuple of (prepared_command, use_shell)
        """
        if not command:
            return [], False
        
        # Check if it's a bash command
        if command[0] == "bash" and len(command) >= 3 and command[1] in ["-c", "-lc"]:
            if self._is_windows():
                # Try to use Git Bash or WSL on Windows
                git_bash = r"C:\Program Files\Git\bin\bash.exe"
                if os.path.exists(git_bash):
                    return [git_bash, command[1], command[2]], False
                # Fall back to cmd with the command converted
                return ["cmd", "/c", command[2]], False
            return command, False
        
        # Regular command
        return command, False
    
    def preview(self, plan: Dict[str, Any]) -> str:
        """
        Generate a preview of what would be executed.
        
        Args:
            plan: The command plan from LLM.
            
        Returns:
            Human-readable preview string.
        """
        command = plan.get("command", [])
        cwd = plan.get("cwd", ".")
        intent = plan.get("intent", "unknown")
        explain = plan.get("explain", "")
        
        # Resolve cwd
        exec_path = self.work_dir / cwd if cwd != "." else self.work_dir
        
        lines = [
            "=" * 50,
            "📋 COMMAND PREVIEW",
            "=" * 50,
            f"Intent: {intent}",
            f"Explanation: {explain}",
            "",
            f"Command: {' '.join(command)}",
            f"Directory: {exec_path}",
            "",
        ]
        
        # Add safety warnings
        warnings = self._check_safety(command)
        if warnings:
            lines.append("⚠️ WARNINGS:")
            for w in warnings:
                lines.append(f"   - {w}")
            lines.append("")
        
        # Check if directory exists
        if not exec_path.exists():
            lines.append(f"❌ Directory does not exist: {exec_path}")
        
        lines.append("=" * 50)
        return "\n".join(lines)
    
    def _check_safety(self, command: List[str]) -> List[str]:
        """Check command for safety concerns."""
        warnings = []
        cmd_str = " ".join(command).lower()
        
        dangerous_patterns = [
            ("rm -rf", "Recursive force delete detected"),
            ("rm -r", "Recursive delete detected"),
            ("del /s", "Windows recursive delete detected"),
            ("format", "Disk format command detected"),
            ("mkfs", "Filesystem creation detected"),
            ("> /dev/", "Writing to device detected"),
            ("dd if=", "Disk dump command detected"),
            ("chmod 777", "Overly permissive chmod detected"),
            ("sudo", "Sudo/elevated privileges detected"),
            ("powershell", "PowerShell execution detected"),
            (":(){:|:&};:", "Fork bomb detected"),
            ("shutdown", "Shutdown command detected"),
            ("reboot", "Reboot command detected"),
        ]
        
        for pattern, warning in dangerous_patterns:
            if pattern in cmd_str:
                warnings.append(warning)
        
        return warnings
    
    def execute(
        self,
        plan: Dict[str, Any],
        mode: ExecutionMode = ExecutionMode.SANDBOX,
    ) -> ExecutionResult:
        """
        Execute a command plan.
        
        Args:
            plan: The command plan from LLM.
            mode: Execution mode (dry_run, sandbox, or live).
            
        Returns:
            ExecutionResult with all details.
        """
        command = plan.get("command", [])
        cwd = plan.get("cwd", ".")
        
        # Dry run - just return preview info
        if mode == ExecutionMode.DRY_RUN:
            return ExecutionResult(
                success=True,
                exit_code=0,
                stdout=self.preview(plan),
                stderr="",
                duration_ms=0,
                command=command,
                cwd=cwd,
                mode=mode,
                git_before=None,
                git_after=None,
                diff=None,
                error=None,
            )
        
        # Determine execution directory
        if mode == ExecutionMode.SANDBOX:
            # Create sandbox copy
            self._sandbox_path = self.git.create_sandbox_copy(self.work_dir)
            exec_dir = self._sandbox_path / cwd if cwd != "." else self._sandbox_path
            sandbox_git = GitController(str(self._sandbox_path))
        else:
            exec_dir = self.work_dir / cwd if cwd != "." else self.work_dir
            sandbox_git = self.git
        
        # Get git state before
        git_before = sandbox_git.get_current_commit()
        
        # Prepare and execute command
        prepared_cmd, use_shell = self._prepare_command(command)
        
        if not prepared_cmd:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                duration_ms=0,
                command=command,
                cwd=cwd,
                mode=mode,
                git_before=git_before,
                git_after=None,
                diff=None,
                error="Empty command",
            )
        
        start_time = time.time()
        error_msg = None
        
        try:
            result = subprocess.run(
                prepared_cmd,
                cwd=str(exec_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                shell=use_shell,
            )
            exit_code = result.returncode
            stdout = result.stdout[:self.MAX_OUTPUT_SIZE]
            stderr = result.stderr[:self.MAX_OUTPUT_SIZE]
            
        except subprocess.TimeoutExpired:
            exit_code = -1
            stdout = ""
            stderr = ""
            error_msg = f"Command timed out after {self.timeout}s"
            
        except FileNotFoundError as e:
            exit_code = -1
            stdout = ""
            stderr = str(e)
            error_msg = f"Command not found: {prepared_cmd[0]}"
            
        except Exception as e:
            exit_code = -1
            stdout = ""
            stderr = str(e)
            error_msg = f"Execution error: {type(e).__name__}"
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Create snapshot and get diff
        git_after = sandbox_git.create_snapshot(f"CLAI: After '{plan.get('intent', 'command')}'")
        diff = sandbox_git.get_diff(git_before) if git_before else None
        
        return ExecutionResult(
            success=exit_code == 0,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            command=command,
            cwd=cwd,
            mode=mode,
            git_before=git_before,
            git_after=git_after,
            diff=diff,
            error=error_msg,
        )
    
    def get_sandbox_diff(self) -> Optional[DiffResult]:
        """Get the diff of changes in the current sandbox."""
        if self._sandbox_path:
            sandbox_git = GitController(str(self._sandbox_path))
            return sandbox_git.get_diff()
        return None
    
    def apply_sandbox_to_live(self) -> bool:
        """
        Apply sandbox changes to the live directory.
        
        Returns:
            True if successful.
        """
        if not self._sandbox_path or not self._sandbox_path.exists():
            return False
        
        # Get the diff from sandbox
        sandbox_git = GitController(str(self._sandbox_path))
        diff = sandbox_git.get_diff("HEAD~1")  # Changes since initial state
        
        if not diff.has_changes:
            return True  # Nothing to apply
        
        # Copy changed files from sandbox to live
        for file in diff.files_changed:
            src = self._sandbox_path / file
            dst = self.work_dir / file
            
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(src, dst)
            elif dst.exists():
                # File was deleted in sandbox
                dst.unlink()
        
        # Create snapshot in live directory
        self.git.create_snapshot("CLAI: Applied sandbox changes")
        
        return True
    
    def discard_sandbox(self):
        """Discard the current sandbox without applying changes."""
        if self._sandbox_path:
            self.git.cleanup_sandbox(self._sandbox_path)
            self._sandbox_path = None
    
    def cleanup(self):
        """Clean up any temporary resources."""
        self.discard_sandbox()


