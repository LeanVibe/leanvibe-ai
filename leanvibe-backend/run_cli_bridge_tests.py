#!/usr/bin/env python3
"""
CLI Bridge Test Runner

Comprehensive test runner for CLI bridge functionality with detailed reporting.
Tests CLI-to-iOS bridge endpoints, WebSocket communication, and device management.
"""

import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple

def run_command(cmd: List[str], cwd: str = None) -> Tuple[int, str, str]:
    """Run command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out after 120 seconds"
    except Exception as e:
        return 1, "", f"Error running command: {str(e)}"

def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_subsection(title: str):
    """Print formatted subsection header"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def run_pytest_with_coverage(test_pattern: str, coverage_source: str) -> Tuple[bool, Dict]:
    """Run pytest with coverage and return results"""
    cmd = [
        "python", "-m", "pytest",
        test_pattern,
        "-v",
        "--tb=short",
        f"--cov={coverage_source}",
        "--cov-report=term-missing",
        "--cov-report=json",
        "--json-report",
        "--json-report-file=test_results.json"
    ]
    
    exit_code, stdout, stderr = run_command(cmd, cwd=".")
    
    # Parse results
    results = {
        "success": exit_code == 0,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "coverage": None,
        "test_summary": None
    }
    
    # Try to read coverage data
    try:
        if Path("coverage.json").exists():
            with open("coverage.json") as f:
                coverage_data = json.load(f)
                results["coverage"] = coverage_data.get("totals", {})
    except Exception as e:
        print(f"Warning: Could not read coverage data: {e}")
    
    # Try to read test results
    try:
        if Path("test_results.json").exists():
            with open("test_results.json") as f:
                test_data = json.load(f)
                results["test_summary"] = test_data.get("summary", {})
    except Exception as e:
        print(f"Warning: Could not read test results: {e}")
    
    return results["success"], results

def check_dependencies():
    """Check if required test dependencies are available"""
    print_section("Checking Test Dependencies")
    
    dependencies = [
        ("pytest", "pytest --version"),
        ("pytest-cov", "python -c 'import pytest_cov'"),
        ("pytest-asyncio", "python -c 'import pytest_asyncio'"),
        ("fastapi", "python -c 'import fastapi'"),
        ("websockets", "python -c 'import websockets'")
    ]
    
    all_available = True
    for name, check_cmd in dependencies:
        exit_code, stdout, stderr = run_command(check_cmd.split())
        if exit_code == 0:
            print(f"✅ {name}: Available")
            if "version" in check_cmd:
                version = stdout.strip().split()[-1] if stdout.strip() else "unknown"
                print(f"   Version: {version}")
        else:
            print(f"❌ {name}: Not available")
            print(f"   Error: {stderr.strip()}")
            all_available = False
    
    return all_available

def run_cli_bridge_tests():
    """Run comprehensive CLI bridge tests"""
    print_section("CLI Bridge API Tests")
    
    success, results = run_pytest_with_coverage(
        "tests/test_cli_bridge_api.py",
        "app.api.endpoints.cli_bridge"
    )
    
    print(results["stdout"])
    if results["stderr"]:
        print("STDERR:")
        print(results["stderr"])
    
    return success, results

def run_connection_manager_tests():
    """Run enhanced connection manager tests"""
    print_section("Enhanced Connection Manager Tests")
    
    success, results = run_pytest_with_coverage(
        "tests/test_connection_manager_enhanced.py",
        "app.core.connection_manager"
    )
    
    print(results["stdout"])
    if results["stderr"]:
        print("STDERR:")
        print(results["stderr"])
    
    return success, results

def run_integration_tests():
    """Run integration tests for CLI bridge functionality"""
    print_section("CLI Bridge Integration Tests")
    
    success, results = run_pytest_with_coverage(
        "tests/test_cli_bridge_api.py::TestCLIBridgeIntegration",
        "app"
    )
    
    print(results["stdout"])
    if results["stderr"]:
        print("STDERR:")
        print(results["stderr"])
    
    return success, results

def run_performance_tests():
    """Run performance tests for CLI bridge"""
    print_section("CLI Bridge Performance Tests")
    
    # Run specific performance-related tests
    cmd = [
        "python", "-m", "pytest",
        "tests/test_connection_manager_enhanced.py::TestConnectionManagerIntegration::test_concurrent_ios_operations",
        "-v",
        "--tb=short"
    ]
    
    exit_code, stdout, stderr = run_command(cmd)
    success = exit_code == 0
    
    print(stdout)
    if stderr:
        print("STDERR:")
        print(stderr)
    
    return success, {"exit_code": exit_code, "stdout": stdout, "stderr": stderr}

def generate_test_report(test_results: List[Tuple[str, bool, Dict]]):
    """Generate comprehensive test report"""
    print_section("Test Report Summary")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, success, _ in test_results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Test Suites: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print_subsection("Test Suite Results")
    for test_name, success, results in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        
        if results.get("test_summary"):
            summary = results["test_summary"]
            if "total" in summary:
                print(f"     Tests: {summary.get('total', 0)} total, "
                      f"{summary.get('passed', 0)} passed, "
                      f"{summary.get('failed', 0)} failed")
        
        if results.get("coverage"):
            coverage = results["coverage"]
            if "percent_covered" in coverage:
                print(f"     Coverage: {coverage['percent_covered']:.1f}%")
    
    print_subsection("Coverage Summary")
    # Aggregate coverage data
    total_lines = 0
    covered_lines = 0
    
    for _, _, results in test_results:
        if results.get("coverage"):
            cov = results["coverage"]
            total_lines += cov.get("num_statements", 0)
            covered_lines += cov.get("covered_lines", 0)
    
    if total_lines > 0:
        overall_coverage = (covered_lines / total_lines) * 100
        print(f"Overall Coverage: {overall_coverage:.1f}% ({covered_lines}/{total_lines} lines)")
    else:
        print("Coverage data not available")
    
    return passed_tests == total_tests

def cleanup_test_artifacts():
    """Clean up test artifacts"""
    artifacts = [
        "test_results.json",
        "coverage.json",
        ".coverage",
        "__pycache__",
        ".pytest_cache"
    ]
    
    for artifact in artifacts:
        path = Path(artifact)
        if path.exists():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)

def main():
    """Main test runner function"""
    print("🚀 LeanVibe CLI Bridge Test Suite")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Missing required dependencies. Please install them first:")
        print("pip install pytest pytest-cov pytest-asyncio pytest-json-report")
        return 1
    
    # Clean up from previous runs
    cleanup_test_artifacts()
    
    # Run test suites
    test_results = []
    
    try:
        # CLI Bridge API Tests
        success, results = run_cli_bridge_tests()
        test_results.append(("CLI Bridge API", success, results))
        
        # Connection Manager Tests
        success, results = run_connection_manager_tests()
        test_results.append(("Connection Manager Enhanced", success, results))
        
        # Integration Tests
        success, results = run_integration_tests()
        test_results.append(("Integration Tests", success, results))
        
        # Performance Tests
        success, results = run_performance_tests()
        test_results.append(("Performance Tests", success, results))
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Test run interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Unexpected error during test run: {e}")
        return 1
    
    # Generate report
    all_passed = generate_test_report(test_results)
    
    # Final status
    if all_passed:
        print("\n🎉 All tests passed! CLI bridge is ready for deployment.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please review the results above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)