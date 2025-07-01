#!/usr/bin/env python3
"""
Script to add missing files to Xcode project target membership.
Uses python-pbxproj library to safely modify the project.pbxproj file.
"""

import os
import sys
import subprocess

def install_pbxproj():
    """Install pbxproj library if not present."""
    try:
        import pbxproj
        return True
    except ImportError:
        print("Installing pbxproj library...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pbxproj"])
            return True
        except subprocess.CalledProcessError:
            print("Failed to install pbxproj. Please install manually: pip install pbxproj")
            return False

def add_files_to_xcode_project():
    """Add missing files to Xcode project."""
    if not install_pbxproj():
        return False
    
    try:
        from pbxproj import XcodeProject
    except ImportError:
        print("Failed to import pbxproj after installation")
        return False
    
    # Load the project
    project_path = "LeanVibe.xcodeproj/project.pbxproj"
    print(f"Loading project: {project_path}")
    
    try:
        project = XcodeProject.load(project_path)
    except Exception as e:
        print(f"Failed to load project: {e}")
        return False
    
    # Critical files that need to be added to the project
    critical_files = [
        "LeanVibe/Configuration/AppConfiguration.swift",
        "LeanVibe/Services/GlobalErrorManager.swift", 
        "LeanVibe/Services/RetryManager.swift",
        "LeanVibe/Services/CodeCompletionService.swift",
        "LeanVibe/Models/KanbanTypes.swift",
        "LeanVibe/Extensions/EnvironmentValues+GlobalError.swift",
        "LeanVibe/Extensions/View+GlobalError.swift",
        "LeanVibe/Views/Error/GlobalErrorView.swift",
        "LeanVibe/Views/Error/RetryMonitorView.swift"
    ]
    
    # Test files to add to test target
    test_files = [
        "LeanVibeTests/IntegrationTestSuite.swift",
        "LeanVibeTests/ProjectManagerTests.swift",
        "LeanVibeTests/SpeechRecognitionServiceTests.swift", 
        "LeanVibeTests/TaskServiceTests.swift",
        "LeanVibeTests/UserFlowUITests.swift"
    ]
    
    added_files = []
    skipped_files = []
    
    # Add critical files to main target
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                # Add to main app target
                project.add_file(file_path, target_name="LeanVibe")
                added_files.append(f"{file_path} -> LeanVibe target")
                print(f"✅ Added {file_path} to LeanVibe target")
            except Exception as e:
                print(f"❌ Failed to add {file_path}: {e}")
                skipped_files.append(file_path)
        else:
            print(f"⚠️  File not found: {file_path}")
            skipped_files.append(file_path)
    
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
            print(f"\n🎉 Successfully updated project with {len(added_files)} files:")
            for file in added_files:
                print(f"  • {file}")
            
            if skipped_files:
                print(f"\n⚠️  Skipped {len(skipped_files)} files:")
                for file in skipped_files:
                    print(f"  • {file}")
            
            return True
        except Exception as e:
            print(f"❌ Failed to save project: {e}")
            return False
    else:
        print("No files were added to the project")
        return False

if __name__ == "__main__":
    print("🔧 Fixing Xcode target membership issues...")
    success = add_files_to_xcode_project()
    if success:
        print("\n✅ Target membership fixes completed!")
        print("🚀 Try building the project now: xcodebuild -project LeanVibe.xcodeproj -scheme LeanVibe build")
    else:
        print("\n❌ Failed to fix target membership issues")
    sys.exit(0 if success else 1)