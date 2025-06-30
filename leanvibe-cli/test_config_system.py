#!/usr/bin/env python3
"""
Test script for Task 2.3.4 configuration management system

Tests the configuration commands and functionality.
"""

import sys
import subprocess
from pathlib import Path

# Add the leanvibe_cli package to the path
sys.path.insert(0, '/Users/bogdan/work/leanvibe-ai/leanvibe-cli')


def test_syntax_validation():
    """Test Python syntax validation for all config files"""
    print("🧪 Testing Python syntax for configuration system...")
    
    files_to_check = [
        'leanvibe_cli/config/__init__.py',
        'leanvibe_cli/config/manager.py',
        'leanvibe_cli/config/schema.py',
        'leanvibe_cli/config/profiles.py',
        'leanvibe_cli/config/wizard.py',
        'leanvibe_cli/commands/config.py',
        'leanvibe_cli/utils/__init__.py',
        'leanvibe_cli/utils/yaml_helpers.py'
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


def test_imports():
    """Test that all imports work correctly"""
    print("\n🧪 Testing import structure...")
    
    try:
        # Test config package imports
        from leanvibe_cli.config import ConfigurationManager, ConfigSchema, ProfileManager
        print("✅ Config package imports successful")
        
        # Test schema imports
        from leanvibe_cli.config.schema import NotificationSettings, DesktopSettings, TerminalSettings
        print("✅ Schema imports successful")
        
        # Test wizard import
        from leanvibe_cli.config.wizard import ConfigurationWizard
        print("✅ Wizard import successful")
        
        # Test utils imports
        from leanvibe_cli.utils import safe_yaml_load, safe_yaml_dump, merge_dicts
        print("✅ Utils imports successful")
        
        # Test command import
        from leanvibe_cli.commands.config import config
        print("✅ Config command import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_help():
    """Test that config command help works"""
    print("\n🧪 Testing config command help...")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'leanvibe_cli.main', 'config', '--help'
        ], capture_output=True, text=True, cwd='/Users/bogdan/work/leanvibe-ai/leanvibe-cli')
        
        print(f"Exit code: {result.returncode}")
        
        if result.returncode == 0:
            # Check for expected subcommands
            expected_commands = [
                "show", "set", "get", "reset", "wizard",
                "profile", "export", "import"
            ]
            
            success = True
            for cmd in expected_commands:
                if cmd in result.stdout:
                    print(f"✅ Found command: {cmd}")
                else:
                    print(f"❌ Missing command: {cmd}")
                    success = False
            
            return success
        else:
            print("❌ Config help failed")
            if result.stderr:
                print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error testing config help: {e}")
        return False


def test_schema_validation():
    """Test configuration schema validation"""
    print("\n🧪 Testing configuration schema...")
    
    try:
        from leanvibe_cli.config.schema import ConfigSchema, ProfileConfig
        
        # Test creating default config
        config = ConfigSchema()
        print("✅ Default ConfigSchema created")
        
        # Test profile creation
        profile = ProfileConfig()
        print("✅ Default ProfileConfig created")
        
        # Test validation
        test_data = {
            "version": "1.0",
            "active_profile": "default",
            "profiles": {
                "default": {
                    "backend_url": "http://localhost:8000",
                    "notifications": {
                        "enabled": True,
                        "minimum_priority": "medium"
                    }
                }
            }
        }
        
        config = ConfigSchema.from_dict(test_data)
        print("✅ ConfigSchema from dict successful")
        
        # Test getting active config
        active = config.get_active_config()
        print(f"✅ Active profile retrieved: {config.active_profile}")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema validation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_yaml_helpers():
    """Test YAML helper functions"""
    print("\n🧪 Testing YAML helpers...")
    
    try:
        from leanvibe_cli.utils.yaml_helpers import merge_dicts
        
        # Test dict merging
        base = {"a": 1, "b": {"c": 2}}
        updates = {"b": {"d": 3}, "e": 4}
        result = merge_dicts(base, updates)
        
        assert result == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}
        print("✅ Dict merging works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ YAML helpers error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Task 2.3.4 Configuration Management Tests")
    print("=" * 50)
    
    all_success = True
    
    # Test syntax first
    if test_syntax_validation():
        print("✅ Syntax validation passed")
    else:
        print("❌ Syntax validation failed")
        all_success = False
    
    # Test imports
    if test_imports():
        print("✅ Import tests passed")
    else:
        print("❌ Import tests failed")
        all_success = False
    
    # Test schema
    if test_schema_validation():
        print("✅ Schema validation passed")
    else:
        print("❌ Schema validation failed")
        all_success = False
    
    # Test YAML helpers
    if test_yaml_helpers():
        print("✅ YAML helpers passed")
    else:
        print("❌ YAML helpers failed")
        all_success = False
    
    # Test command help
    if test_config_help():
        print("✅ Config command help passed")
    else:
        print("❌ Config command help failed")
        all_success = False
    
    print("\n" + "=" * 50)
    if all_success:
        print("✅ All tests passed! Configuration management system is ready.")
        print("\nUsage examples:")
        print("  leanvibe config show")
        print("  leanvibe config set notifications.enabled true")
        print("  leanvibe config wizard")
        print("  leanvibe config profile list")
        print("  leanvibe config profile create production")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return all_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)