#!/usr/bin/env python3
"""
Detailed analysis of Xcode target membership issues.
"""

import os
import re
from pathlib import Path

def analyze_xcode_project():
    project_dir = "/Users/bogdan/work/leanvibe-ai/leanvibe-ios"
    pbxproj_path = os.path.join(project_dir, "LeanVibe.xcodeproj", "project.pbxproj")
    
    with open(pbxproj_path, 'r') as f:
        content = f.read()
    
    print("🔍 DETAILED XCODE PROJECT ANALYSIS")
    print("=" * 50)
    
    # Extract all file references
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
    
    print(f"\n📋 Found {len(file_refs)} Swift file references in project.pbxproj")
    
    # Extract all PBXBuildFile entries
    build_files = {}
    build_file_pattern = r'([A-F0-9]+) /\* (.+\.swift) in Sources \*/ = \{isa = PBXBuildFile; fileRef = ([A-F0-9]+)'
    for match in re.finditer(build_file_pattern, content):
        build_id = match.group(1)
        file_name = match.group(2)
        file_ref_id = match.group(3)
        build_files[build_id] = {
            'file_ref_id': file_ref_id,
            'file_name': file_name
        }
    
    print(f"📋 Found {len(build_files)} build file entries")
    
    # Find main app target source files
    app_sources_match = re.search(r'isa = PBXSourcesBuildPhase;[^}]*files = \((.*?)\);', content, re.DOTALL)
    app_source_files = []
    if app_sources_match:
        files_section = app_sources_match.group(1)
        app_build_ids = re.findall(r'([A-F0-9]+) /\*', files_section)
        
        for build_id in app_build_ids:
            if build_id in build_files:
                app_source_files.append(build_files[build_id]['file_name'])
    
    print(f"🎯 Main app target includes {len(app_source_files)} source files")
    
    # Find test target source files  
    test_sources_matches = list(re.finditer(r'isa = PBXSourcesBuildPhase;[^}]*files = \((.*?)\);', content, re.DOTALL))
    test_source_files = []
    if len(test_sources_matches) > 1:
        # Second sources build phase is typically tests
        files_section = test_sources_matches[1].group(1)
        test_build_ids = re.findall(r'([A-F0-9]+) /\*', files_section)
        
        for build_id in test_build_ids:
            if build_id in build_files:
                test_source_files.append(build_files[build_id]['file_name'])
    
    print(f"🧪 Test target includes {len(test_source_files)} source files")
    
    # Get all filesystem files
    filesystem_files = []
    app_dir = Path(project_dir) / "LeanVibe"
    test_dir = Path(project_dir) / "LeanVibeTests"
    
    for swift_file in app_dir.rglob("*.swift"):
        filesystem_files.append(str(swift_file.name))
    
    for swift_file in test_dir.rglob("*.swift"):
        filesystem_files.append(str(swift_file.name))
    
    filesystem_files = list(set(filesystem_files))  # Remove duplicates
    print(f"📁 Found {len(filesystem_files)} unique Swift files in filesystem")
    
    # Find missing files
    all_included_files = set(app_source_files + test_source_files)
    referenced_files = set(ref['name'] for ref in file_refs.values())
    
    missing_from_project = []
    missing_from_targets = []
    
    for fs_file in filesystem_files:
        if fs_file not in referenced_files:
            missing_from_project.append(fs_file)
        elif fs_file not in all_included_files:
            missing_from_targets.append(fs_file)
    
    print(f"\n❌ FILES MISSING FROM PROJECT ({len(missing_from_project)}):")
    for f in sorted(missing_from_project):
        print(f"   • {f}")
    
    print(f"\n⚠️  FILES MISSING FROM TARGETS ({len(missing_from_targets)}):")
    for f in sorted(missing_from_targets):
        print(f"   • {f}")
    
    # Show what's actually included
    print(f"\n✅ FILES INCLUDED IN APP TARGET ({len(app_source_files)}):")
    for f in sorted(app_source_files)[:20]:  # Show first 20
        print(f"   • {f}")
    if len(app_source_files) > 20:
        print(f"   ... and {len(app_source_files) - 20} more")
    
    print(f"\n✅ FILES INCLUDED IN TEST TARGET ({len(test_source_files)}):")
    for f in sorted(test_source_files):
        print(f"   • {f}")
    
    # Critical files analysis
    critical_missing = []
    critical_files_to_check = [
        "AppConfiguration.swift",
        "GlobalErrorManager.swift", 
        "RetryManager.swift",
        "CodeCompletionService.swift",
        "KanbanTypes.swift"
    ]
    
    for critical_file in critical_files_to_check:
        if critical_file in missing_from_project:
            critical_missing.append(critical_file)
    
    if critical_missing:
        print(f"\n🚨 CRITICAL FILES MISSING FROM PROJECT:")
        for f in critical_missing:
            print(f"   • {f}")
    
    print(f"\n📊 SUMMARY:")
    print(f"   • Filesystem files: {len(filesystem_files)}")
    print(f"   • Referenced in project: {len(referenced_files)}")
    print(f"   • Included in app target: {len(app_source_files)}")
    print(f"   • Included in test target: {len(test_source_files)}")
    print(f"   • Missing from project: {len(missing_from_project)}")
    print(f"   • Missing from targets: {len(missing_from_targets)}")

if __name__ == "__main__":
    analyze_xcode_project()