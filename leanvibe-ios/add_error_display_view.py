#!/usr/bin/env python3
"""
Add ErrorDisplayView.swift to Xcode project target.
"""

import os
import sys

try:
    from pbxproj import XcodeProject
except ImportError:
    print("pbxproj library not available")
    sys.exit(1)

def add_error_display_view():
    """Add ErrorDisplayView.swift to Xcode project."""
    
    # Load the project
    project_path = "LeanVibe.xcodeproj/project.pbxproj"
    print(f"Loading project: {project_path}")
    
    try:
        project = XcodeProject.load(project_path)
    except Exception as e:
        print(f"Failed to load project: {e}")
        return False
    
    # File to add
    file_path = "LeanVibe/Views/Error/ErrorDisplayView.swift"
    
    if os.path.exists(file_path):
        try:
            # Add to main app target
            project.add_file(file_path, target_name="LeanVibe")
            print(f"✅ Added {file_path} to LeanVibe target")
            
            # Save the project
            project.save()
            print(f"\n🎉 Successfully added ErrorDisplayView.swift to project")
            return True
        except Exception as e:
            print(f"❌ Failed to add {file_path}: {e}")
            return False
    else:
        print(f"⚠️  File not found: {file_path}")
        return False

if __name__ == "__main__":
    print("🔧 Adding ErrorDisplayView.swift to Xcode project...")
    success = add_error_display_view()
    sys.exit(0 if success else 1)