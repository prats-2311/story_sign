#!/usr/bin/env python3
"""
Comprehensive test runner for StorySign ASL Platform
Runs both frontend and backend unit tests with coverage reporting
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_frontend_tests():
    """Run frontend Jest tests"""
    print("🧪 Running Frontend Tests (Jest/React Testing Library)")
    print("=" * 60)
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
        
    try:
        # Change to frontend directory and run tests
        result = subprocess.run(
            ["npm", "test", "--", "--coverage", "--watchAll=false"],
            cwd=frontend_dir,
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        if result.returncode == 0:
            print("✅ Frontend tests passed!")
            return True
        else:
            print("❌ Frontend tests failed!")
            return False
            
    except FileNotFoundError:
        print("❌ npm not found. Please install Node.js and npm")
        return False
    except Exception as e:
        print(f"❌ Error running frontend tests: {e}")
        return False


def run_backend_tests():
    """Run backend pytest tests"""
    print("\n🧪 Running Backend Tests (pytest)")
    print("=" * 60)
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
        
    try:
        # Run pytest with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            str(backend_dir),
            "-v",
            "--tb=short",
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:backend/htmlcov"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        if result.returncode == 0:
            print("✅ Backend tests passed!")
            return True
        else:
            print("❌ Backend tests failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error running backend tests: {e}")
        return False


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Run StorySign platform tests")
    parser.add_argument("--frontend-only", action="store_true", help="Run only frontend tests")
    parser.add_argument("--backend-only", action="store_true", help="Run only backend tests")
    
    args = parser.parse_args()
    
    print("🚀 StorySign ASL Platform Test Suite")
    print("=" * 60)
    
    frontend_success = True
    backend_success = True
    
    if not args.backend_only:
        frontend_success = run_frontend_tests()
        
    if not args.frontend_only:
        backend_success = run_backend_tests()
        
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    
    if not args.backend_only:
        status = "✅ PASSED" if frontend_success else "❌ FAILED"
        print(f"Frontend Tests: {status}")
        
    if not args.frontend_only:
        status = "✅ PASSED" if backend_success else "❌ FAILED"
        print(f"Backend Tests:  {status}")
        
    overall_success = frontend_success and backend_success
    overall_status = "✅ ALL TESTS PASSED" if overall_success else "❌ SOME TESTS FAILED"
    print(f"\nOverall Result: {overall_status}")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())