#!/usr/bin/env python3
"""
Test script for enhanced monitor command

Tests the new monitor command options and integration.
"""

import subprocess
import sys
from pathlib import Path

# Add the leenvibe_cli package to the path
sys.path.insert(0, '/Users/bogdan/work/leanvibe-ai/leenvibe-cli')

def test_monitor_help():
    """Test that monitor command shows the new options"""
    print("🧪 Testing monitor command help...")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'leenvibe_cli.main', 'monitor', '--help'
        ], capture_output=True, text=True, cwd='/Users/bogdan/work/leanvibe-ai/leenvibe-cli')
        
        print(f"Exit code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        # Check for new options
        expected_options = [
            "--background",
            "--desktop-notifications", 
            "--live-dashboard",
            "--overlay"
        ]
        
        success = True
        for option in expected_options:
            if option in result.stdout:
                print(f"✅ Found option: {option}")
            else:
                print(f"❌ Missing option: {option}")
                success = False
        
        return success
        
    except Exception as e:
        print(f"❌ Error running monitor help: {e}")
        return False


def test_import_structure():
    """Test that all imports work correctly"""
    print("\n🧪 Testing import structure...")
    
    try:
        # Test UI imports
        from leenvibe_cli.ui import NotificationOverlay, NotificationHistory, LiveMetricsDashboard
        print("✅ UI imports successful")
        
        # Test services imports
        from leenvibe_cli.services import NotificationService, DesktopNotificationService, NotificationTriggers
        print("✅ Services imports successful")
        
        # Test monitor command imports
        from leenvibe_cli.commands.monitor import enhanced_monitor_command, show_enhanced_monitor_header
        print("✅ Monitor command imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_syntax_validation():
    """Test Python syntax validation"""
    print("\n🧪 Testing Python syntax...")
    
    files_to_check = [
        '/Users/bogdan/work/leanvibe-ai/leenvibe-cli/leenvibe_cli/commands/monitor.py',
        '/Users/bogdan/work/leanvibe-ai/leenvibe-cli/leenvibe_cli/ui/live_dashboard.py',
        '/Users/bogdan/work/leanvibe-ai/leenvibe-cli/leenvibe_cli/ui/notification_overlay.py',
        '/Users/bogdan/work/leanvibe-ai/leenvibe-cli/leenvibe_cli/services/notification_service.py'
    ]
    
    success = True
    for file_path in files_to_check:
        try:
            result = subprocess.run([
                sys.executable, '-m', 'py_compile', file_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {Path(file_path).name} - Syntax OK")
            else:
                print(f"❌ {Path(file_path).name} - Syntax Error:")
                print(result.stderr)
                success = False
                
        except Exception as e:
            print(f"❌ Error checking {file_path}: {e}")
            success = False
    
    return success


def main():
    """Run all tests"""
    print("🧪 Enhanced Monitor Command Tests")
    print("=" * 50)
    
    all_success = True
    
    # Test imports first
    if test_import_structure():
        print("✅ Import structure test passed")
    else:
        print("❌ Import structure test failed")
        all_success = False
    
    # Test syntax validation
    if test_syntax_validation():
        print("✅ Syntax validation test passed")
    else:
        print("❌ Syntax validation test failed")
        all_success = False
    
    # Test command help
    if test_monitor_help():
        print("✅ Monitor help test passed")
    else:
        print("❌ Monitor help test failed")
        all_success = False
    
    print("\n" + "=" * 50)
    if all_success:
        print("✅ All tests passed! Enhanced monitor command is ready.")
        print("\nUsage examples:")
        print("  leenvibe monitor --background --desktop-notifications")
        print("  leenvibe monitor --live-dashboard --overlay")
        print("  leenvibe monitor --background --live-dashboard --overlay --desktop-notifications")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return all_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)