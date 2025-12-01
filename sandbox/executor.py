# file: CLAI/sandbox/executor.py
# Main executor for CLAI - orchestrates LLM, sandbox, and logging

from __future__ import annotations
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .logger import CLAILogger
from .runner import SandboxRunner, ExecutionMode, ExecutionResult
from .git_control import GitController


class ApprovalAction(Enum):
    """User approval actions."""
    APPROVE = "approve"         # Execute the command
    APPROVE_LIVE = "approve_live"  # Execute directly (skip sandbox)
    REJECT = "reject"           # Reject and cancel
    MODIFY = "modify"           # Request modification
    PREVIEW = "preview"         # Show more details


@dataclass
class ExecutorConfig:
    """Configuration for the Executor."""
    work_dir: str = "."
    log_file: str = "CLAI_logs.txt"
    json_logs: bool = False
    timeout: int = 30
    auto_approve_safe: bool = False  # Auto-approve read-only commands
    require_sandbox_first: bool = True  # Always run in sandbox first


class Executor:
    """
    Main executor that orchestrates the full CLAI pipeline:
    1. Receive plan from LLM translator
    2. Preview and validate
    3. Get user approval
    4. Execute in sandbox or live
    5. Log everything
    """
    
    # Safe intents that can be auto-approved
    SAFE_INTENTS = {"file_search", "file_list", "system_info", "read", "search", "find", "list"}
    
    def __init__(self, config: Optional[ExecutorConfig] = None):
        """Initialize Executor with configuration."""
        self.config = config or ExecutorConfig()
        
        self.work_dir = Path(self.config.work_dir).resolve()
        self.logger = CLAILogger(
            log_dir=str(self.work_dir),
            log_file=self.config.log_file,
            json_mode=self.config.json_logs
        )
        self.runner = SandboxRunner(
            work_dir=str(self.work_dir),
            timeout=self.config.timeout
        )
        self.git = GitController(str(self.work_dir))
        
        self._pending_plan: Optional[Dict[str, Any]] = None
        self._pending_query: Optional[str] = None
        self._sandbox_result: Optional[ExecutionResult] = None
    
    def _is_safe_intent(self, plan: Dict[str, Any]) -> bool:
        """Check if the plan is safe (read-only)."""
        intent = plan.get("intent", "").lower()
        
        # Check against safe intents
        for safe in self.SAFE_INTENTS:
            if safe in intent:
                return True
        
        # Check for explicit write/delete flags
        if plan.get("needs_clarification"):
            return False
        
        # Check command for dangerous patterns
        cmd_str = " ".join(plan.get("command", [])).lower()
        dangerous = ["rm", "del", "remove", "delete", "write", "create", "mv", "move", "cp", "copy", ">", ">>"]
        
        for d in dangerous:
            if d in cmd_str:
                return False
        
        return True
    
    def preview(self, user_query: str, plan: Dict[str, Any]) -> str:
        """
        Generate a preview for the user.
        
        Returns a formatted string showing what will be executed.
        """
        self._pending_plan = plan
        self._pending_query = user_query
        
        preview = self.runner.preview(plan)
        
        # Add approval options
        is_safe = self._is_safe_intent(plan)
        
        lines = [
            preview,
            "",
            "📋 OPTIONS:",
            "  [Y] Approve (run in sandbox first)" if self.config.require_sandbox_first else "  [Y] Approve",
            "  [L] Run LIVE (skip sandbox, direct execution)",
            "  [N] Reject (cancel)",
            "  [P] Show more details",
        ]
        
        if is_safe and self.config.auto_approve_safe:
            lines.append("")
            lines.append("ℹ️  This appears to be a safe read-only command.")
        
        if plan.get("needs_clarification"):
            lines.append("")
            lines.append(f"❓ Clarification needed: {plan.get('question', 'Please confirm.')}")
        
        return "\n".join(lines)
    
    def execute_with_approval(
        self,
        user_query: str,
        plan: Dict[str, Any],
        approval_callback: Optional[Callable[[str], str]] = None,
    ) -> ExecutionResult:
        """
        Execute a plan with user approval workflow.
        
        Args:
            user_query: Original natural language query
            plan: Command plan from LLM
            approval_callback: Function that takes preview string and returns user choice
                              If None, uses terminal input
        
        Returns:
            ExecutionResult
        """
        # Generate preview
        preview_text = self.preview(user_query, plan)
        
        # Get approval
        if approval_callback:
            choice = approval_callback(preview_text)
        else:
            print(preview_text)
            choice = input("\nYour choice [Y/L/N/P]: ").strip().upper()
        
        # Handle choice
        if choice in ["N", "NO", "REJECT", "CANCEL"]:
            self.logger.log_command(
                user_query=user_query,
                plan=plan,
                sandbox_mode="rejected",
                approved=False,
                error="User rejected command"
            )
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="Command rejected by user",
                duration_ms=0,
                command=plan.get("command", []),
                cwd=plan.get("cwd", "."),
                mode=ExecutionMode.DRY_RUN,
                git_before=None,
                git_after=None,
                diff=None,
                error="User rejected"
            )
        
        if choice in ["P", "PREVIEW", "DETAILS"]:
            # Show detailed preview (dry run)
            result = self.runner.execute(plan, ExecutionMode.DRY_RUN)
            print("\n" + result.stdout)
            # Recurse to get actual approval
            return self.execute_with_approval(user_query, plan, approval_callback)
        
        if choice in ["L", "LIVE", "DIRECT"]:
            # Execute directly in live mode
            mode = ExecutionMode.LIVE
        else:
            # Default: sandbox first
            mode = ExecutionMode.SANDBOX
        
        # Execute
        result = self.runner.execute(plan, mode)
        self._sandbox_result = result
        
        # Log the execution
        self.logger.log_command(
            user_query=user_query,
            plan=plan,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_ms=result.duration_ms,
            sandbox_mode=mode.value,
            git_before=result.git_before,
            git_after=result.git_after,
            approved=True,
            error=result.error
        )
        
        # If sandbox mode, offer to apply changes
        if mode == ExecutionMode.SANDBOX and result.success:
            if result.diff and result.diff.has_changes:
                print("\n" + result.summary())
                print("\n📝 Sandbox execution complete. Changes detected:")
                print(f"   Files: {', '.join(result.diff.files_changed)}")
                
                apply = input("\nApply changes to live directory? [Y/N]: ").strip().upper()
                if apply in ["Y", "YES"]:
                    self.runner.apply_sandbox_to_live()
                    print("✅ Changes applied to live directory")
                else:
                    self.runner.discard_sandbox()
                    print("🗑️ Sandbox changes discarded")
            else:
                print("\n✅ Command executed (no file changes)")
        
        return result
    
    def execute_auto(
        self,
        user_query: str,
        plan: Dict[str, Any],
    ) -> ExecutionResult:
        """
        Execute with auto-approval for safe commands.
        Dangerous commands still require manual approval.
        """
        if self._is_safe_intent(plan) and self.config.auto_approve_safe:
            # Auto-approve safe commands
            print(f"🤖 Auto-approving safe command: {plan.get('intent')}")
            mode = ExecutionMode.SANDBOX if self.config.require_sandbox_first else ExecutionMode.LIVE
            result = self.runner.execute(plan, mode)
            
            self.logger.log_command(
                user_query=user_query,
                plan=plan,
                exit_code=result.exit_code,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_ms=result.duration_ms,
                sandbox_mode=mode.value,
                git_before=result.git_before,
                git_after=result.git_after,
                approved=True,
                error=result.error
            )
            
            return result
        else:
            # Require manual approval
            return self.execute_with_approval(user_query, plan)
    
    def quick_execute(
        self,
        user_query: str,
        plan: Dict[str, Any],
        mode: ExecutionMode = ExecutionMode.SANDBOX
    ) -> ExecutionResult:
        """
        Execute immediately without approval (for programmatic use).
        Still logs everything.
        """
        result = self.runner.execute(plan, mode)
        
        self.logger.log_command(
            user_query=user_query,
            plan=plan,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_ms=result.duration_ms,
            sandbox_mode=mode.value,
            git_before=result.git_before,
            git_after=result.git_after,
            approved=True,
            error=result.error
        )
        
        return result
    
    def get_log_path(self) -> Path:
        """Get the path to the log file."""
        return self.logger.get_log_path()
    
    def cleanup(self):
        """Clean up resources."""
        self.runner.cleanup()


