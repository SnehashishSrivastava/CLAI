#!/usr/bin/env python3
"""Integration test for logging in a real workspace"""

import sys
from pathlib import Path

# Add CLAI to path
clai_root = Path(__file__).resolve().parent
sys.path.insert(0, str(clai_root.parent))

from CLAI.sandbox.session import SandboxSession

def main():
    # Use test_workspace if it exists, otherwise current directory
    test_dir = Path("test_workspace")
    if not test_dir.exists():
        test_dir = Path.cwd()
    
    print(f"Testing logging in: {test_dir}")
    print("=" * 60)
    
    # Create session
    session = SandboxSession(work_dir=str(test_dir))
    session.start()
    
    print(f"✅ Session started")
    print(f"   Original dir: {session.original_dir}")
    print(f"   Logger dir: {session.logger.log_dir}")
    print(f"   Log file: {session.logger.get_log_path()}")
    
    # Run a test command
    plan = {
        "version": "1.0",
        "intent": "test",
        "command": ["cmd", "/c", "echo", "Integration test"],
        "cwd": ".",
        "explain": "Testing logging integration"
    }
    
    print("\n🔧 Executing test command...")
    result = session.run_plan(plan, user_query="integration test")
    
    print(f"✅ Command executed: exit_code={result.exit_code}")
    
    # Check log file
    log_path = session.logger.get_log_path()
    print(f"\n📄 Log file: {log_path}")
    print(f"   Exists: {log_path.exists()}")
    
    if log_path.exists():
        size = log_path.stat().st_size
        print(f"   Size: {size} bytes")
        
        # Read and show last entry
        content = log_path.read_text()
        print(f"\n📋 Last log entry:")
        # Get last entry (after last separator)
        entries = content.split("=" * 60)
        if len(entries) > 1:
            print(entries[-1][:500])
        else:
            print(content[-500:])
    
    # Cleanup
    session.discard()
    print("\n✅ Test complete!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

