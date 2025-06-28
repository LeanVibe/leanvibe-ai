#!/usr/bin/env python3
"""
Comprehensive test runner for Sprint 2.3 integration testing

Executes all test suites and validates quality gates:
- Unit tests for notification system
- Integration tests for CLI↔Backend↔iOS communication  
- Performance tests for quality requirements
"""

import sys
import subprocess
import time
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🧪 {description}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED ({duration:.2f}s)")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - FAILED ({duration:.2f}s)")
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            if result.stdout:
                print("STDOUT:")
                print(result.stdout)
            return False
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ {description} - ERROR ({duration:.2f}s)")
        print(f"Exception: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check pytest availability
    try:
        import pytest
        print(f"✅ pytest {pytest.__version__} available")
    except ImportError:
        print("❌ pytest not available. Install with: uv sync --extra dev")
        return False
    
    # Check required packages
    required_packages = [
        'asyncio',
        'unittest.mock',
        'psutil',
        'aiohttp'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} missing")
    
    if missing_packages:
        print(f"\nInstall missing packages with:")
        print(f"uv sync --extra dev")
        return False
    
    return True


def run_syntax_validation():
    """Run syntax validation on all Python files"""
    print("\n🔍 Running syntax validation...")
    
    python_files = [
        "leenvibe_cli/services/notification_service.py",
        "leenvibe_cli/services/desktop_notifications.py", 
        "leenvibe_cli/ui/notification_overlay.py",
        "leenvibe_cli/ui/live_dashboard.py",
        "leenvibe_cli/commands/monitor.py",
        "leenvibe_cli/commands/config.py",
        "leenvibe_cli/config/manager.py",
        "leenvibe_cli/config/schema.py"
    ]
    
    success = True
    for file_path in python_files:
        if Path(file_path).exists():
            result = run_command(
                f"python -m py_compile {file_path}",
                f"Syntax check: {Path(file_path).name}"
            )
            if not result:
                success = False
        else:
            print(f"⚠️  File not found: {file_path}")
    
    return success


def run_import_validation():
    """Test that all imports work correctly"""
    print("\n📦 Running import validation...")
    
    import_tests = [
        ("leenvibe_cli.config", "CLIConfig"),
        ("leenvibe_cli.services.notification_service", "NotificationService"),
        ("leenvibe_cli.services.desktop_notifications", "DesktopNotificationService"),
        ("leenvibe_cli.ui.notification_overlay", "NotificationOverlay"),
        ("leenvibe_cli.ui.live_dashboard", "LiveMetricsDashboard"),
        ("leenvibe_cli.commands.monitor", "enhanced_monitor_command"),
        ("leenvibe_cli.commands.config", "config")
    ]
    
    success = True
    for module, component in import_tests:
        try:
            module_obj = __import__(module, fromlist=[component])
            getattr(module_obj, component)
            print(f"✅ Import successful: {module}.{component}")
        except ImportError as e:
            print(f"❌ Import failed: {module}.{component} - {e}")
            success = False
        except AttributeError as e:
            print(f"❌ Component not found: {module}.{component} - {e}")
            success = False
    
    return success


def main():
    """Main test execution"""
    print("🧪 Sprint 2.3 Integration Testing Suite")
    print("=" * 60)
    print("Testing notification system, CLI integration, and performance")
    print()
    
    start_time = time.time()
    results = {}
    
    # 1. Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install required packages.")
        return False
    
    results["dependencies"] = True
    
    # 2. Syntax validation
    results["syntax"] = run_syntax_validation()
    
    # 3. Import validation  
    results["imports"] = run_import_validation()
    
    # 4. Unit tests for notification system
    results["unit_tests"] = run_command(
        "python -m pytest tests/test_notification_system.py -v",
        "Unit Tests - Notification System"
    )
    
    # 5. Integration tests
    results["integration_tests"] = run_command(
        "python -m pytest tests/test_integration.py -v",
        "Integration Tests - CLI↔Backend↔iOS"
    )
    
    # 6. Performance tests
    results["performance_tests"] = run_command(
        "python -m pytest tests/test_performance.py -v -s",
        "Performance Tests - Quality Gates"
    )
    
    # 7. All tests together with coverage
    results["full_test_suite"] = run_command(
        "python -m pytest tests/ -v --tb=short",
        "Complete Test Suite"
    )
    
    # 8. Test legacy test scripts for compatibility
    results["legacy_compatibility"] = True
    for legacy_test in ["test_notifications.py", "test_enhanced_monitor.py", "test_config_system.py"]:
        if Path(legacy_test).exists():
            result = run_command(
                f"python {legacy_test}",
                f"Legacy Test: {legacy_test}"
            )
            if not result:
                results["legacy_compatibility"] = False
    
    # Summary
    total_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = 0
    
    for test_name, passed_test in results.items():
        total += 1
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():.<40} {status}")
        if passed_test:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Duration: {total_time:.2f} seconds")
    
    # Quality Gates Validation
    print("\n" + "=" * 60)
    print("🎯 SPRINT 2.3 QUALITY GATES")
    print("=" * 60)
    
    quality_gates = [
        ("Syntax Validation", results["syntax"]),
        ("Import Structure", results["imports"]),
        ("Unit Test Coverage", results["unit_tests"]),
        ("Integration Testing", results["integration_tests"]),
        ("Performance Requirements", results["performance_tests"]),
        ("Legacy Compatibility", results["legacy_compatibility"])
    ]
    
    gates_passed = 0
    for gate_name, gate_result in quality_gates:
        status = "✅ PASS" if gate_result else "❌ FAIL"
        print(f"{gate_name:.<40} {status}")
        if gate_result:
            gates_passed += 1
    
    all_passed = gates_passed == len(quality_gates)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL QUALITY GATES PASSED!")
        print("\n✅ Sprint 2.3 notification system is ready for deployment")
        print("✅ Integration testing complete")
        print("✅ Performance requirements met")
        print("\nReady to proceed to next phase!")
    else:
        print("❌ QUALITY GATES FAILED")
        print(f"\n{gates_passed}/{len(quality_gates)} quality gates passed")
        print("Please fix failing tests before proceeding")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)