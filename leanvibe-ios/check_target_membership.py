#!/usr/bin/env python3
"""
Script to analyze Xcode target membership issues in the LeanVibe iOS project.
Identifies Swift files that exist in the filesystem but are not properly 
included in the Xcode project targets.
"""

import os
import re
import json
from pathlib import Path

def find_swift_files(directory):
    """Find all Swift files in the LeanVibe app and test directories."""
    swift_files = []
    
    # App files
    app_dir = Path(directory) / "LeanVibe"
    if app_dir.exists():
        for swift_file in app_dir.rglob("*.swift"):
            swift_files.append(str(swift_file.relative_to(directory)))
    
    # Test files
    test_dir = Path(directory) / "LeanVibeTests"
    if test_dir.exists():
        for swift_file in test_dir.rglob("*.swift"):
            swift_files.append(str(swift_file.relative_to(directory)))
    
    return sorted(swift_files)

def extract_files_from_pbxproj(pbxproj_path):
    """Extract file references and build file entries from project.pbxproj."""
    with open(pbxproj_path, 'r') as f:
        content = f.read()
    
    # Find all file references
    file_refs = {}
    file_ref_pattern = r'([A-F0-9]+) /\* (.+\.swift) \*/ = \{isa = PBXFileReference;.*?path = (.+\.swift);'
    for match in re.finditer(file_ref_pattern, content):
        file_id = match.group(1)
        file_name = match.group(2)
        file_path = match.group(3)
        file_refs[file_id] = {
            'name': file_name,
            'path': file_path
        }
    
    # Find all build file entries (files actually included in compilation)
    build_files = {}
    build_file_pattern = r'([A-F0-9]+) /\* (.+\.swift) in Sources \*/ = \{isa = PBXBuildFile; fileRef = ([A-F0-9]+) /\* (.+\.swift) \*/;'
    for match in re.finditer(build_file_pattern, content):
        build_id = match.group(1)
        file_name = match.group(2)
        file_ref_id = match.group(3)
        file_name2 = match.group(4)
        build_files[build_id] = {
            'file_ref_id': file_ref_id,
            'file_name': file_name
        }
    
    # Find which files are included in which targets
    target_files = {}
    
    # Main app target
    app_target_match = re.search(r'([A-F0-9]+) = \{[^}]*isa = PBXNativeTarget;[^}]*name = LeanVibe;.*?buildPhases = \((.*?)\);', content, re.DOTALL)
    if app_target_match:
        build_phases = app_target_match.group(2)
        sources_phase_match = re.search(r'([A-F0-9]+) /\* Sources \*/', build_phases)
        if sources_phase_match:
            sources_phase_id = sources_phase_match.group(1)
            sources_pattern = rf'{sources_phase_id} = \{{[^}}]*isa = PBXSourcesBuildPhase;[^}}]*files = \((.*?)\);'
            sources_match = re.search(sources_pattern, content, re.DOTALL)
            if sources_match:
                files_section = sources_match.group(1)
                app_files = re.findall(r'([A-F0-9]+) /\*', files_section)
                target_files['LeanVibe'] = app_files
    
    # Test target
    test_target_match = re.search(r'([A-F0-9]+) = \{[^}]*isa = PBXNativeTarget;[^}]*name = LeanVibeTests;.*?buildPhases = \((.*?)\);', content, re.DOTALL)
    if test_target_match:
        build_phases = test_target_match.group(2)
        sources_phase_match = re.search(r'([A-F0-9]+) /\* Sources \*/', build_phases)
        if sources_phase_match:
            sources_phase_id = sources_phase_match.group(1)
            sources_pattern = rf'{sources_phase_id} = \{{[^}}]*isa = PBXSourcesBuildPhase;[^}}]*files = \((.*?)\);'
            sources_match = re.search(sources_pattern, content, re.DOTALL)
            if sources_match:
                files_section = sources_match.group(1)
                test_files = re.findall(r'([A-F0-9]+) /\*', files_section)
                target_files['LeanVibeTests'] = test_files
    
    return file_refs, build_files, target_files

def analyze_target_membership(project_dir):
    """Analyze target membership issues."""
    print("🔍 LeanVibe iOS Target Membership Analysis")
    print("=" * 50)
    
    # Find all Swift files in the filesystem
    filesystem_files = find_swift_files(project_dir)
    print(f"\n📁 Found {len(filesystem_files)} Swift files in filesystem:")
    for f in filesystem_files[:10]:  # Show first 10
        print(f"   • {f}")
    if len(filesystem_files) > 10:
        print(f"   ... and {len(filesystem_files) - 10} more")
    
    # Parse project.pbxproj
    pbxproj_path = os.path.join(project_dir, "LeanVibe.xcodeproj", "project.pbxproj")
    if not os.path.exists(pbxproj_path):
        print("❌ project.pbxproj not found!")
        return
    
    file_refs, build_files, target_files = extract_files_from_pbxproj(pbxproj_path)
    
    print(f"\n📋 Found {len(file_refs)} file references in project.pbxproj")
    print(f"📋 Found {len(build_files)} build file entries in project.pbxproj")
    
    # Get files referenced in the project
    referenced_files = set()
    for file_ref in file_refs.values():
        referenced_files.add(file_ref['path'])
    
    # Get files actually included in targets
    included_files = set()
    for target_name, build_ids in target_files.items():
        print(f"\n🎯 Target '{target_name}' includes {len(build_ids)} files")
        for build_id in build_ids:
            if build_id in build_files:
                file_ref_id = build_files[build_id]['file_ref_id']
                if file_ref_id in file_refs:
                    included_files.add(file_refs[file_ref_id]['path'])
    
    # Find missing files
    missing_from_project = []
    missing_from_targets = []
    
    for fs_file in filesystem_files:
        file_name = os.path.basename(fs_file)
        
        # Check if file is referenced in project at all
        found_in_refs = False
        for ref_path in referenced_files:
            if ref_path == file_name or ref_path.endswith(f"/{file_name}"):
                found_in_refs = True
                break
        
        if not found_in_refs:
            missing_from_project.append(fs_file)
        else:
            # Check if file is actually included in a target
            found_in_targets = False
            for inc_path in included_files:
                if inc_path == file_name or inc_path.endswith(f"/{file_name}"):
                    found_in_targets = True
                    break
            
            if not found_in_targets:
                missing_from_targets.append(fs_file)
    
    # Report findings
    print(f"\n❌ FILES MISSING FROM PROJECT ({len(missing_from_project)}):")
    print("   (Files that exist in filesystem but are not referenced in project.pbxproj)")
    for f in missing_from_project:
        print(f"   • {f}")
    
    print(f"\n⚠️  FILES MISSING FROM TARGETS ({len(missing_from_targets)}):")
    print("   (Files referenced in project.pbxproj but not included in any target)")
    for f in missing_from_targets:
        print(f"   • {f}")
    
    # Categorize missing files
    if missing_from_project:
        print(f"\n📊 CATEGORIZATION OF MISSING FILES:")
        categories = {
            'Configuration': [f for f in missing_from_project if 'Configuration' in f],
            'Services': [f for f in missing_from_project if 'Services' in f],
            'Views': [f for f in missing_from_project if 'Views' in f],
            'Models': [f for f in missing_from_project if 'Models' in f],
            'Extensions': [f for f in missing_from_project if 'Extensions' in f],
            'Tests': [f for f in missing_from_project if 'Tests' in f],
            'Error Handling': [f for f in missing_from_project if any(x in f for x in ['Error', 'Retry'])],
            'Other': []
        }
        
        # Categorize uncategorized files
        categorized = set()
        for cat_files in categories.values():
            categorized.update(cat_files)
        
        categories['Other'] = [f for f in missing_from_project if f not in categorized]
        
        for category, files in categories.items():
            if files:
                print(f"\n   📂 {category} ({len(files)} files):")
                for f in files:
                    print(f"      • {f}")
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   • Total Swift files in filesystem: {len(filesystem_files)}")
    print(f"   • Files referenced in project: {len(referenced_files)}")
    print(f"   • Files included in targets: {len(included_files)}")
    print(f"   • Missing from project: {len(missing_from_project)}")
    print(f"   • Missing from targets: {len(missing_from_targets)}")
    
    if missing_from_project or missing_from_targets:
        print(f"\n⚠️  ACTION REQUIRED:")
        print(f"   These files need to be added to the Xcode project targets to resolve build issues.")
        print(f"   Use Xcode to add them to the appropriate target (LeanVibe or LeanVibeTests).")
    else:
        print(f"\n✅ All files appear to be properly included in the project!")

if __name__ == "__main__":
    project_dir = "/Users/bogdan/work/leanvibe-ai/leanvibe-ios"
    analyze_target_membership(project_dir)