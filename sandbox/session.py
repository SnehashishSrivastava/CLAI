# file: CLAI/sandbox/session.py
# Persistent sandbox session for CLAI
# Keeps a working copy while preserving the original directory

from __future__ import annotations
import os
import shutil
import subprocess
import time
import filecmp
import difflib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field


@dataclass
class CommandResult:
    """Result of a single command execution."""
    command: List[str]
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timestamp: str
    success: bool
    
    def summary(self) -> str:
        status = "✅" if self.success else "❌"
        return f"{status} [{self.timestamp}] {' '.join(self.command)} (exit: {self.exit_code}, {self.duration_ms:.0f}ms)"


@dataclass
class FileChange:
    """Represents a file change between original and sandbox."""
    path: str
    change_type: str  # "added", "modified", "deleted"
    diff_lines: Optional[List[str]] = None


@dataclass
class SessionState:
    """Current state of a sandbox session."""
    session_id: str
    original_dir: Path
    sandbox_dir: Path
    created_at: str
    command_history: List[CommandResult] = field(default_factory=list)
    is_active: bool = True


class SandboxSession:
    """
    Persistent sandbox session that:
    1. Creates a copy of the working directory
    2. Runs all commands in the copy
    3. Preserves original until user decides to apply or discard
    4. Tracks all changes and command history
    """
    
    SANDBOX_PREFIX = ".clai_sandbox_"
    
    def __init__(self, work_dir: Optional[str] = None, timeout: int = 60):
        """
        Initialize a sandbox session.
        
        Args:
            work_dir: The original working directory to sandbox.
            timeout: Default timeout for commands in seconds.
        """
        self.original_dir = Path(work_dir).resolve() if work_dir else Path.cwd().resolve()
        self.timeout = timeout
        self.state: Optional[SessionState] = None
        self._ignore_patterns = [
            '.git', '__pycache__', '*.pyc', '.clai_sandbox_*', 
            'node_modules', '.venv', 'venv', 'clai_env', '*.egg-info',
            'CLAI_logs.txt', 'last_runner_payload.json'  # Don't copy logs/temp files
        ]
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _get_sandbox_path(self, session_id: str) -> Path:
        """Get the sandbox directory path (sibling to original)."""
        return self.original_dir.parent / f"{self.SANDBOX_PREFIX}{self.original_dir.name}_{session_id}"
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored during copy/compare."""
        # Check full path for .git directories
        path_str = str(path)
        if '.git' in path_str.split(os.sep):
            return True
        
        name = path.name
        for pattern in self._ignore_patterns:
            if pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern.endswith('*'):
                if name.startswith(pattern[:-1]):
                    return True
            elif name == pattern:
                return True
        return False
    
    def _copy_directory(self, src: Path, dst: Path):
        """Copy directory with ignore patterns."""
        dst.mkdir(parents=True, exist_ok=True)
        
        for item in src.iterdir():
            if self._should_ignore(item):
                continue
            
            dest_item = dst / item.name
            
            if item.is_dir():
                self._copy_directory(item, dest_item)
            else:
                shutil.copy2(item, dest_item)
    
    def start(self) -> SessionState:
        """
        Start a new sandbox session.
        Creates a copy of the working directory.
        
        Returns:
            SessionState with session details.
        """
        if self.state and self.state.is_active:
            print(f"⚠️ Session already active: {self.state.session_id}")
            return self.state
        
        session_id = self._generate_session_id()
        sandbox_dir = self._get_sandbox_path(session_id)
        
        print(f"📦 Creating sandbox copy...")
        print(f"   Original: {self.original_dir}")
        print(f"   Sandbox:  {sandbox_dir}")
        
        # Copy directory
        self._copy_directory(self.original_dir, sandbox_dir)
        
        self.state = SessionState(
            session_id=session_id,
            original_dir=self.original_dir,
            sandbox_dir=sandbox_dir,
            created_at=datetime.now().isoformat(),
            command_history=[],
            is_active=True
        )
        
        print(f"✅ Sandbox session started: {session_id}")
        print(f"   All commands will run in the sandbox.")
        print(f"   Original directory is preserved.\n")
        
        return self.state
    
    def _is_windows(self) -> bool:
        """Check if running on Windows."""
        return os.name == 'nt'
    
    def _prepare_command(self, command: List[str]) -> List[str]:
        """Prepare command for execution."""
        if not command:
            return []
        
        # Handle bash commands on Windows
        if command[0] == "bash" and len(command) >= 3:
            if self._is_windows():
                git_bash = r"C:\Program Files\Git\bin\bash.exe"
                if os.path.exists(git_bash):
                    return [git_bash, command[1], command[2]]
                # Convert to cmd
                return ["cmd", "/c", command[2]]
        
        return command
    
    def run_command(self, command: List[str], cwd: str = ".") -> CommandResult:
        """
        Execute a command in the sandbox.
        
        Args:
            command: Command as list of strings.
            cwd: Relative working directory within sandbox.
            
        Returns:
            CommandResult with execution details.
        """
        if not self.state or not self.state.is_active:
            raise RuntimeError("No active sandbox session. Call start() first.")
        
        # Resolve execution directory within sandbox
        exec_dir = self.state.sandbox_dir / cwd if cwd != "." else self.state.sandbox_dir
        
        if not exec_dir.exists():
            exec_dir.mkdir(parents=True, exist_ok=True)
        
        prepared_cmd = self._prepare_command(command)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n🔧 Executing in sandbox: {' '.join(command)}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                prepared_cmd,
                cwd=str(exec_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr
            
        except subprocess.TimeoutExpired:
            exit_code = -1
            stdout = ""
            stderr = f"Command timed out after {self.timeout}s"
            
        except FileNotFoundError as e:
            exit_code = -1
            stdout = ""
            stderr = f"Command not found: {prepared_cmd[0] if prepared_cmd else 'empty'}"
            
        except Exception as e:
            exit_code = -1
            stdout = ""
            stderr = str(e)
        
        duration_ms = (time.time() - start_time) * 1000
        
        cmd_result = CommandResult(
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            timestamp=timestamp,
            success=exit_code == 0
        )
        
        self.state.command_history.append(cmd_result)
        
        # Show result
        if cmd_result.success:
            print(f"✅ Command succeeded (exit: 0)")
        else:
            print(f"❌ Command failed (exit: {exit_code})")
        
        if stdout:
            print(f"\n📤 Output:\n{stdout[:2000]}{'...' if len(stdout) > 2000 else ''}")
        if stderr:
            print(f"\n⚠️ Stderr:\n{stderr[:500]}")
        
        return cmd_result
    
    def run_plan(self, plan: Dict[str, Any]) -> CommandResult:
        """
        Execute a plan from the LLM.
        
        Args:
            plan: Plan dict with 'command' and 'cwd' keys.
        """
        command = plan.get("command", [])
        cwd = plan.get("cwd", ".")
        return self.run_command(command, cwd)
    
    def get_changes(self) -> List[FileChange]:
        """
        Compare sandbox with original and return list of changes.
        
        Returns:
            List of FileChange objects describing all modifications.
        """
        if not self.state or not self.state.is_active:
            return []
        
        if not self.state.sandbox_dir.exists():
            return []
        
        changes = []
        
        # Get all files in both directories
        original_files = set()
        sandbox_files = set()
        
        # Scan original directory
        if self.original_dir.exists():
            for f in self.original_dir.rglob("*"):
                try:
                    if f.is_file() and not self._should_ignore(f):
                        rel = f.relative_to(self.original_dir)
                        # Normalize path separators
                        original_files.add(str(rel).replace("\\", "/"))
                except Exception:
                    pass
        
        # Scan sandbox directory
        for f in self.state.sandbox_dir.rglob("*"):
            try:
                if f.is_file() and not self._should_ignore(f):
                    rel = f.relative_to(self.state.sandbox_dir)
                    # Normalize path separators
                    sandbox_files.add(str(rel).replace("\\", "/"))
            except Exception:
                pass
        
        # Find added files (in sandbox but not in original)
        added = sandbox_files - original_files
        for f in added:
            changes.append(FileChange(path=f, change_type="added"))
        
        # Find deleted files (in original but not in sandbox)
        deleted = original_files - sandbox_files
        for f in deleted:
            changes.append(FileChange(path=f, change_type="deleted"))
        
        # Find modified files (in both, compare content)
        common = original_files & sandbox_files
        for f in common:
            # Use forward slashes for path construction
            orig_path = self.original_dir / f.replace("/", os.sep)
            sand_path = self.state.sandbox_dir / f.replace("/", os.sep)
            
            try:
                if orig_path.exists() and sand_path.exists():
                    if not filecmp.cmp(str(orig_path), str(sand_path), shallow=False):
                        # Generate diff for text files
                        diff_lines = None
                        try:
                            with open(orig_path, 'r', encoding='utf-8') as fo:
                                orig_lines = fo.readlines()
                            with open(sand_path, 'r', encoding='utf-8') as fs:
                                sand_lines = fs.readlines()
                            
                            diff = list(difflib.unified_diff(
                                orig_lines, sand_lines,
                                fromfile=f"original/{f}",
                                tofile=f"sandbox/{f}",
                                lineterm=""
                            ))
                            diff_lines = diff[:100]  # Limit diff size
                        except:
                            pass  # Binary file or encoding issue
                        
                        changes.append(FileChange(
                            path=f, 
                            change_type="modified",
                            diff_lines=diff_lines
                        ))
            except Exception:
                pass
        
        return changes
    
    def show_changes(self) -> str:
        """
        Display a summary of all changes between original and sandbox.
        
        Returns:
            Formatted string showing all changes.
        """
        changes = self.get_changes()
        
        if not changes:
            return "📋 No changes detected between original and sandbox."
        
        lines = [
            "=" * 60,
            "📋 SANDBOX CHANGES SUMMARY",
            "=" * 60,
            ""
        ]
        
        added = [c for c in changes if c.change_type == "added"]
        modified = [c for c in changes if c.change_type == "modified"]
        deleted = [c for c in changes if c.change_type == "deleted"]
        
        if added:
            lines.append(f"➕ Added ({len(added)} files):")
            for c in added:
                lines.append(f"   + {c.path}")
            lines.append("")
        
        if modified:
            lines.append(f"📝 Modified ({len(modified)} files):")
            for c in modified:
                lines.append(f"   ~ {c.path}")
                if c.diff_lines:
                    for dl in c.diff_lines[:20]:
                        lines.append(f"      {dl.rstrip()}")
                    if len(c.diff_lines) > 20:
                        lines.append(f"      ... ({len(c.diff_lines) - 20} more lines)")
            lines.append("")
        
        if deleted:
            lines.append(f"➖ Deleted ({len(deleted)} files):")
            for c in deleted:
                lines.append(f"   - {c.path}")
            lines.append("")
        
        lines.append(f"Total: {len(added)} added, {len(modified)} modified, {len(deleted)} deleted")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def show_history(self) -> str:
        """Show command history for this session."""
        if not self.state:
            return "No active session."
        
        lines = [
            f"📜 Command History (Session: {self.state.session_id})",
            "-" * 40
        ]
        
        for i, cmd in enumerate(self.state.command_history, 1):
            lines.append(f"{i}. {cmd.summary()}")
        
        if not self.state.command_history:
            lines.append("   (no commands executed yet)")
        
        return "\n".join(lines)
    
    def apply_changes(self) -> bool:
        """
        Apply sandbox changes to the original directory.
        This replaces the original with the sandbox contents.
        
        Returns:
            True if successful.
        """
        if not self.state or not self.state.is_active:
            print("❌ No active sandbox session.")
            return False
        
        changes = self.get_changes()
        if not changes:
            print("ℹ️ No changes to apply.")
            self.discard()
            return True
        
        print(f"\n🔄 Applying {len(changes)} changes to original directory...")
        
        try:
            # Process each change
            for change in changes:
                orig_path = self.original_dir / change.path
                sand_path = self.state.sandbox_dir / change.path
                
                if change.change_type == "added":
                    # Copy new file from sandbox to original
                    orig_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(sand_path, orig_path)
                    print(f"   ➕ Added: {change.path}")
                    
                elif change.change_type == "modified":
                    # Replace original with sandbox version
                    shutil.copy2(sand_path, orig_path)
                    print(f"   📝 Updated: {change.path}")
                    
                elif change.change_type == "deleted":
                    # Remove from original
                    if orig_path.exists():
                        orig_path.unlink()
                        print(f"   ➖ Deleted: {change.path}")
            
            print(f"\n✅ All changes applied successfully!")
            
            # Clean up sandbox
            self._cleanup_sandbox()
            self.state.is_active = False
            
            return True
            
        except Exception as e:
            print(f"❌ Error applying changes: {e}")
            return False
    
    def discard(self):
        """
        Discard the sandbox and all changes.
        Original directory remains untouched.
        """
        if not self.state:
            print("No active session to discard.")
            return
        
        print(f"\n🗑️ Discarding sandbox session: {self.state.session_id}")
        self._cleanup_sandbox()
        self.state.is_active = False
        print("✅ Sandbox discarded. Original directory unchanged.")
    
    def _cleanup_sandbox(self):
        """Remove the sandbox directory."""
        if self.state and self.state.sandbox_dir.exists():
            try:
                shutil.rmtree(self.state.sandbox_dir)
            except Exception as e:
                print(f"⚠️ Could not fully clean up sandbox: {e}")
    
    def get_sandbox_path(self) -> Optional[Path]:
        """Get the path to the sandbox directory."""
        return self.state.sandbox_dir if self.state else None
    
    def is_active(self) -> bool:
        """Check if a session is currently active."""
        return self.state is not None and self.state.is_active
    
    def end_session(self, apply: bool = False) -> bool:
        """
        End the session with a final decision.
        
        Args:
            apply: If True, apply changes. If False, discard.
            
        Returns:
            True if session ended successfully.
        """
        if apply:
            return self.apply_changes()
        else:
            self.discard()
            return True

