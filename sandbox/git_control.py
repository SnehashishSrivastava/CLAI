# file: CLAI/sandbox/git_control.py
# Git-based version control for CLAI sandbox

from __future__ import annotations
import os
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GitStatus:
    """Represents the current git status."""
    is_repo: bool
    branch: Optional[str]
    commit_hash: Optional[str]
    is_clean: bool
    modified_files: List[str]
    untracked_files: List[str]


@dataclass 
class DiffResult:
    """Result of a git diff operation."""
    has_changes: bool
    diff_text: str
    files_changed: List[str]
    insertions: int
    deletions: int


class GitController:
    """
    Git integration for CLAI sandbox.
    Provides version control, snapshots, diffs, and rollback.
    """
    
    def __init__(self, work_dir: Optional[str] = None):
        """
        Initialize GitController.
        
        Args:
            work_dir: Working directory. Defaults to current directory.
        """
        self.work_dir = Path(work_dir) if work_dir else Path.cwd()
        self._git_available = self._check_git()
    
    def _check_git(self) -> bool:
        """Check if git is available on the system."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _run_git(self, *args, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
        """
        Run a git command.
        
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cwd = cwd or self.work_dir
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "Git command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    @property
    def is_available(self) -> bool:
        """Check if git is available."""
        return self._git_available
    
    def is_repo(self, path: Optional[Path] = None) -> bool:
        """Check if directory is a git repository."""
        path = path or self.work_dir
        code, _, _ = self._run_git("rev-parse", "--git-dir", cwd=path)
        return code == 0
    
    def init_repo(self, path: Optional[Path] = None) -> bool:
        """Initialize a new git repository."""
        path = path or self.work_dir
        code, out, err = self._run_git("init", cwd=path)
        if code == 0:
            # Create initial commit
            self._run_git("add", "-A", cwd=path)
            self._run_git("commit", "-m", "CLAI: Initial sandbox state", "--allow-empty", cwd=path)
        return code == 0
    
    def get_status(self, path: Optional[Path] = None) -> GitStatus:
        """Get current git status."""
        path = path or self.work_dir
        
        if not self.is_repo(path):
            return GitStatus(
                is_repo=False,
                branch=None,
                commit_hash=None,
                is_clean=True,
                modified_files=[],
                untracked_files=[]
            )
        
        # Get branch name
        code, branch, _ = self._run_git("rev-parse", "--abbrev-ref", "HEAD", cwd=path)
        branch = branch if code == 0 else None
        
        # Get commit hash
        code, commit, _ = self._run_git("rev-parse", "HEAD", cwd=path)
        commit = commit if code == 0 else None
        
        # Get modified files
        code, modified, _ = self._run_git("diff", "--name-only", cwd=path)
        modified_files = [f for f in modified.split("\n") if f]
        
        # Get untracked files
        code, untracked, _ = self._run_git("ls-files", "--others", "--exclude-standard", cwd=path)
        untracked_files = [f for f in untracked.split("\n") if f]
        
        # Check if clean
        code, status, _ = self._run_git("status", "--porcelain", cwd=path)
        is_clean = len(status) == 0
        
        return GitStatus(
            is_repo=True,
            branch=branch,
            commit_hash=commit,
            is_clean=is_clean,
            modified_files=modified_files,
            untracked_files=untracked_files
        )
    
    def get_current_commit(self, path: Optional[Path] = None) -> Optional[str]:
        """Get the current commit hash."""
        path = path or self.work_dir
        code, commit, _ = self._run_git("rev-parse", "HEAD", cwd=path)
        return commit if code == 0 else None
    
    def create_snapshot(self, message: str = "CLAI snapshot", path: Optional[Path] = None) -> Optional[str]:
        """
        Create a git snapshot (commit all changes).
        
        Returns:
            Commit hash if successful, None otherwise.
        """
        path = path or self.work_dir
        
        if not self.is_repo(path):
            return None
        
        # Stage all changes
        self._run_git("add", "-A", cwd=path)
        
        # Check if there are changes to commit
        code, status, _ = self._run_git("status", "--porcelain", cwd=path)
        if not status:
            # No changes, return current commit
            return self.get_current_commit(path)
        
        # Commit
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"{message} [{timestamp}]"
        code, out, err = self._run_git("commit", "-m", full_message, cwd=path)
        
        if code == 0:
            return self.get_current_commit(path)
        return None
    
    def get_diff(self, from_commit: Optional[str] = None, path: Optional[Path] = None) -> DiffResult:
        """
        Get diff from a commit (or working directory changes).
        
        Args:
            from_commit: Compare from this commit. If None, show uncommitted changes.
        """
        path = path or self.work_dir
        
        if from_commit:
            code, diff, _ = self._run_git("diff", from_commit, cwd=path)
            code2, stat, _ = self._run_git("diff", "--stat", from_commit, cwd=path)
            code3, names, _ = self._run_git("diff", "--name-only", from_commit, cwd=path)
        else:
            code, diff, _ = self._run_git("diff", cwd=path)
            code2, stat, _ = self._run_git("diff", "--stat", cwd=path)
            code3, names, _ = self._run_git("diff", "--name-only", cwd=path)
        
        files = [f for f in names.split("\n") if f]
        
        # Parse insertions/deletions from stat
        insertions = 0
        deletions = 0
        if stat:
            for line in stat.split("\n"):
                if "insertion" in line or "deletion" in line:
                    parts = line.split(",")
                    for part in parts:
                        if "insertion" in part:
                            try:
                                insertions = int(part.strip().split()[0])
                            except:
                                pass
                        if "deletion" in part:
                            try:
                                deletions = int(part.strip().split()[0])
                            except:
                                pass
        
        return DiffResult(
            has_changes=len(diff) > 0,
            diff_text=diff,
            files_changed=files,
            insertions=insertions,
            deletions=deletions
        )
    
    def rollback(self, to_commit: str, path: Optional[Path] = None) -> bool:
        """
        Rollback to a specific commit (hard reset).
        
        WARNING: This discards all changes after the commit!
        """
        path = path or self.work_dir
        code, _, _ = self._run_git("reset", "--hard", to_commit, cwd=path)
        return code == 0
    
    def rollback_last(self, path: Optional[Path] = None) -> bool:
        """Rollback to the previous commit."""
        return self.rollback("HEAD~1", path)
    
    def create_sandbox_copy(self, source_dir: Optional[Path] = None) -> Path:
        """
        Create a temporary sandbox copy of a directory with git initialized.
        
        Returns:
            Path to the sandbox directory.
        """
        source = source_dir or self.work_dir
        
        # Create temp directory
        sandbox_dir = Path(tempfile.mkdtemp(prefix="clai_sandbox_"))
        
        # Copy files (excluding .git if exists)
        for item in source.iterdir():
            if item.name == ".git":
                continue
            dest = sandbox_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
            else:
                shutil.copy2(item, dest)
        
        # Initialize git in sandbox
        self._run_git("init", cwd=sandbox_dir)
        self._run_git("add", "-A", cwd=sandbox_dir)
        self._run_git("commit", "-m", "CLAI: Sandbox initial state", cwd=sandbox_dir)
        
        return sandbox_dir
    
    def cleanup_sandbox(self, sandbox_path: Path):
        """Remove a sandbox directory."""
        if sandbox_path.exists() and "clai_sandbox_" in str(sandbox_path):
            shutil.rmtree(sandbox_path, ignore_errors=True)
    
    def get_log(self, n: int = 10, path: Optional[Path] = None) -> List[dict]:
        """Get recent commit log."""
        path = path or self.work_dir
        code, log, _ = self._run_git(
            "log", f"-{n}", 
            "--pretty=format:%H|%h|%s|%ai",
            cwd=path
        )
        
        commits = []
        for line in log.split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 4:
                    commits.append({
                        "hash": parts[0],
                        "short_hash": parts[1],
                        "message": parts[2],
                        "date": parts[3]
                    })
        return commits


