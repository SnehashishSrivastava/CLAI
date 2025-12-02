#!/usr/bin/env python3
"""Test script to verify logging functionality"""

import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add CLAI to path
clai_root = Path(__file__).resolve().parent
sys.path.insert(0, str(clai_root.parent))

from CLAI.sandbox.session import SandboxSession
from CLAI.sandbox.logger import CLAILogger

def test_logger_location():
    """Test that logger uses the correct directory"""
    print("=" * 60)
    print("TEST 1: Logger Location")
    print("=" * 60)
    
    # Create a temporary directory
    test_dir = Path(tempfile.mkdtemp(prefix="clai_test_"))
    print(f"Test directory: {test_dir}")
    
    try:
        # Create logger with test directory
        logger = CLAILogger(log_dir=str(test_dir))
        log_path = logger.get_log_path()
        
        print(f"Expected log path: {test_dir / 'CLAI_logs.txt'}")
        print(f"Actual log path: {log_path}")
        
        assert log_path == test_dir / "CLAI_logs.txt", f"Log path mismatch: {log_path}"
        assert log_path.exists(), "Log file should be created automatically"
        
        print("✅ PASS: Logger uses correct directory")
        print(f"✅ PASS: Log file created at {log_path}")
        
        # Read log file
        content = log_path.read_text()
        print(f"\nLog file content (first 200 chars):")
        print(content[:200])
        
        return True
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

def test_session_logging():
    """Test that SandboxSession logs commands"""
    print("\n" + "=" * 60)
    print("TEST 2: SandboxSession Logging")
    print("=" * 60)
    
    # Create a temporary directory
    test_dir = Path(tempfile.mkdtemp(prefix="clai_test_"))
    print(f"Test directory: {test_dir}")
    
    try:
        # Create a test file
        test_file = test_dir / "test.txt"
        test_file.write_text("Hello World")
        
        # Create session
        session = SandboxSession(work_dir=str(test_dir))
        session.start()
        
        print(f"Session original_dir: {session.original_dir}")
        print(f"Session logger log_dir: {session.logger.log_dir}")
        
        # Check logger is initialized
        assert hasattr(session, 'logger'), "Session should have logger"
        assert session.logger.log_dir == test_dir, f"Logger should use work_dir, got {session.logger.log_dir}"
        
        # Run a simple command
        plan = {
            "version": "1.0",
            "intent": "test",
            "command": ["cmd", "/c", "echo", "test"],
            "cwd": ".",
            "explain": "Test command"
        }
        
        result = session.run_plan(plan, user_query="test command")
        
        print(f"Command executed: exit_code={result.exit_code}")
        
        # Check log file exists
        log_path = session.logger.get_log_path()
        assert log_path.exists(), "Log file should exist after command"
        
        # Read log content
        log_content = log_path.read_text()
        print(f"\nLog file exists: {log_path}")
        print(f"Log file size: {len(log_content)} bytes")
        
        # Check log contains our command
        assert "test command" in log_content or "test" in log_content.lower(), "Log should contain user query"
        assert "echo" in log_content.lower(), "Log should contain command"
        
        print("✅ PASS: Session logs commands correctly")
        print(f"\nLog content preview:")
        print(log_content[:500])
        
        return True
    finally:
        # Cleanup
        if session and session.is_active():
            session.discard()
        shutil.rmtree(test_dir, ignore_errors=True)

def test_logger_default_location():
    """Test logger default location (current working directory)"""
    print("\n" + "=" * 60)
    print("TEST 3: Logger Default Location")
    print("=" * 60)
    
    # Save current directory
    original_cwd = Path.cwd()
    
    # Create a temporary directory and change to it
    test_dir = Path(tempfile.mkdtemp(prefix="clai_test_"))
    print(f"Test directory: {test_dir}")
    
    try:
        # Change to test directory
        os.chdir(test_dir)
        print(f"Changed to: {Path.cwd()}")
        
        # Create logger without specifying log_dir
        logger = CLAILogger()
        log_path = logger.get_log_path()
        
        print(f"Expected log path: {test_dir / 'CLAI_logs.txt'}")
        print(f"Actual log path: {log_path}")
        
        assert log_path.parent == test_dir, f"Log should be in current directory, got {log_path.parent}"
        assert log_path.name == "CLAI_logs.txt", f"Log file name should be CLAI_logs.txt"
        
        print("✅ PASS: Logger defaults to current working directory")
        
        return True
    finally:
        # Restore original directory
        os.chdir(original_cwd)
        shutil.rmtree(test_dir, ignore_errors=True)

def main():
    """Run all tests"""
    print("\n🧪 Testing CLAI Logging Functionality\n")
    
    tests = [
        test_logger_location,
        test_session_logging,
        test_logger_default_location,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ FAIL: {test.__name__}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

