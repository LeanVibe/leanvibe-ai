#!/usr/bin/env python3
"""
Add missing Kanban views to Xcode project target.
"""

import os
import sys

try:
    from pbxproj import XcodeProject
except ImportError:
    print("pbxproj library not available")
    sys.exit(1)

def add_kanban_views():
    """Add missing Kanban view files to Xcode project."""
    
    # Load the project
    project_path = "LeanVibe.xcodeproj/project.pbxproj"
    print(f"Loading project: {project_path}")
    
    try:
        project = XcodeProject.load(project_path)
    except Exception as e:
        print(f"Failed to load project: {e}")
        return False
    
    # Files to check and add
    kanban_files = [
        "LeanVibe/Views/Kanban/KanbanColumnView.swift",
        "LeanVibe/Views/Kanban/TaskCardView.swift"
    ]
    
    added_files = []
    skipped_files = []
    
    for file_path in kanban_files:
        if os.path.exists(file_path):
            try:
                # Add to main app target
                project.add_file(file_path, target_name="LeanVibe")
                added_files.append(file_path)
                print(f"✅ Added {file_path} to LeanVibe target")
            except Exception as e:
                print(f"❌ Failed to add {file_path}: {e}")
                skipped_files.append(file_path)
        else:
            print(f"⚠️  File not found: {file_path}")
            skipped_files.append(file_path)
    
    # Save the project
    if added_files:
        try:
            project.save()
            print(f"\n🎉 Successfully added {len(added_files)} Kanban view files:")
            for file in added_files:
                print(f"  • {file}")
            return True
        except Exception as e:
            print(f"❌ Failed to save project: {e}")
            return False
    else:
        print("No Kanban view files were added to the project")
        return False

if __name__ == "__main__":
    print("🔧 Adding missing Kanban views to Xcode project...")
    success = add_kanban_views()
    sys.exit(0 if success else 1)