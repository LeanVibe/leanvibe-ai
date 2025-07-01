#!/usr/bin/env python3
"""
Add test files to Xcode project test target.
"""

import os
import sys

try:
    from pbxproj import XcodeProject
except ImportError:
    print("pbxproj library not available")
    sys.exit(1)

def add_test_files():
    """Add test files to Xcode project test target."""
    
    # Load the project
    project_path = "LeanVibe.xcodeproj/project.pbxproj"
    print(f"Loading project: {project_path}")
    
    try:
        project = XcodeProject.load(project_path)
    except Exception as e:
        print(f"Failed to load project: {e}")
        return False
    
    # Test files to add
    test_files = [
        "LeanVibeTests/CodeCompletionServiceTests.swift"
    ]
    
    added_files = []
    skipped_files = []
    
    # Add test files to test target
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                # Add to test target
                project.add_file(file_path, target_name="LeanVibeTests")
                added_files.append(f"{file_path} -> LeanVibeTests target")
                print(f"✅ Added {file_path} to LeanVibeTests target")
            except Exception as e:
                print(f"❌ Failed to add {file_path}: {e}")
                skipped_files.append(file_path)
        else:
            print(f"⚠️  Test file not found: {file_path}")
            skipped_files.append(file_path)
    
    # Save the project
    if added_files:
        try:
            project.save()
            print(f"\n🎉 Successfully updated project with {len(added_files)} test files:")
            for file in added_files:
                print(f"  • {file}")
            
            return True
        except Exception as e:
            print(f"❌ Failed to save project: {e}")
            return False
    else:
        print("No test files were added to the project")
        return False

if __name__ == "__main__":
    print("🧪 Adding test files to Xcode project...")
    success = add_test_files()
    sys.exit(0 if success else 1)