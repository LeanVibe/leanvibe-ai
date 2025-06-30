#!/usr/bin/env python3
"""
LeanVibe Naming Inconsistency Fixer

Automated script to fix the LeenVibe vs LeanVibe naming inconsistency
across the entire codebase. This addresses one of the critical technical
debt issues identified in the analysis.
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
import argparse
import json
from datetime import datetime


class NamingInconsistencyFixer:
    """Fixes naming inconsistencies across the LeanVibe codebase"""
    
    def __init__(self, project_root: str, dry_run: bool = True):
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.changes_made: List[Dict] = []
        
        # Define the replacements to make
        self.text_replacements = {
            'LeenVibe': 'LeanVibe',
            'leenvibe': 'leanvibe',
            'LEENVIBE': 'LEANVIBE'
        }
        
        # File and directory renames
        self.path_replacements = {
            'leenvibe': 'leanvibe',
            'LeenVibe': 'LeanVibe'
        }
        
        # File extensions to process
        self.text_file_extensions = {
            '.py', '.md', '.txt', '.yml', '.yaml', '.toml', 
            '.json', '.sh', '.swift', '.ts', '.js'
        }
        
        # Directories to skip
        self.skip_directories = {
            '.git', '__pycache__', '.pytest_cache', 'node_modules',
            'venv', '.venv', 'build', 'dist', '.idea', '.vscode'
        }
    
    def fix_all_inconsistencies(self) -> Dict:
        """Run the complete naming inconsistency fix"""
        print(f"🔧 Starting naming inconsistency fix (dry_run={self.dry_run})")
        print(f"📁 Project root: {self.project_root}")
        
        # Phase 1: Fix file contents
        self._fix_file_contents()
        
        # Phase 2: Rename files and directories
        self._rename_paths()
        
        # Phase 3: Fix special cases
        self._fix_special_cases()
        
        # Generate report
        return self._generate_report()
    
    def _fix_file_contents(self):
        """Fix naming inconsistencies in file contents"""
        print("\n📝 Phase 1: Fixing file contents...")
        
        text_files = []
        for ext in self.text_file_extensions:
            text_files.extend(self.project_root.rglob(f"*{ext}"))
        
        processed = 0
        for file_path in text_files:
            if self._should_skip_path(file_path):
                continue
            
            try:
                if self._fix_file_content(file_path):
                    processed += 1
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
        
        print(f"✅ Processed {processed} files")
    
    def _fix_file_content(self, file_path: Path) -> bool:
        """Fix naming inconsistencies in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except UnicodeDecodeError:
            # Skip binary files
            return False
        
        modified_content = original_content
        changes_in_file = []
        
        # Apply text replacements
        for old_text, new_text in self.text_replacements.items():
            if old_text in modified_content:
                occurrences = modified_content.count(old_text)
                modified_content = modified_content.replace(old_text, new_text)
                changes_in_file.append({
                    'type': 'text_replacement',
                    'old': old_text,
                    'new': new_text,
                    'occurrences': occurrences
                })
        
        # If changes were made
        if modified_content != original_content:
            if not self.dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
            
            self.changes_made.append({
                'file': str(file_path.relative_to(self.project_root)),
                'type': 'content_fix',
                'changes': changes_in_file,
                'dry_run': self.dry_run
            })
            
            return True
        
        return False
    
    def _rename_paths(self):
        """Rename files and directories with naming inconsistencies"""
        print("\n📂 Phase 2: Renaming files and directories...")
        
        # Get all paths that need renaming
        paths_to_rename = []
        
        for path in self.project_root.rglob("*"):
            if self._should_skip_path(path.parent):
                continue
            
            name = path.name
            new_name = name
            
            for old_part, new_part in self.path_replacements.items():
                if old_part in name:
                    new_name = name.replace(old_part, new_part)
                    break
            
            if new_name != name:
                paths_to_rename.append((path, path.parent / new_name))
        
        # Sort by depth (deepest first) to avoid conflicts
        paths_to_rename.sort(key=lambda x: len(x[0].parts), reverse=True)
        
        renamed_count = 0
        for old_path, new_path in paths_to_rename:
            if self._rename_path(old_path, new_path):
                renamed_count += 1
        
        print(f"✅ Renamed {renamed_count} paths")
    
    def _rename_path(self, old_path: Path, new_path: Path) -> bool:
        """Rename a single path"""
        if new_path.exists():
            print(f"⚠️  Skipping {old_path} -> {new_path} (target exists)")
            return False
        
        try:
            if not self.dry_run:
                old_path.rename(new_path)
            
            self.changes_made.append({
                'type': 'path_rename',
                'old_path': str(old_path.relative_to(self.project_root)),
                'new_path': str(new_path.relative_to(self.project_root)),
                'dry_run': self.dry_run
            })
            
            print(f"📁 {old_path.name} -> {new_path.name}")
            return True
            
        except Exception as e:
            print(f"❌ Error renaming {old_path} -> {new_path}: {e}")
            return False
    
    def _fix_special_cases(self):
        """Fix special cases like cache directories and config files"""
        print("\n🔧 Phase 3: Fixing special cases...")
        
        special_cases = [
            # Cache directories
            ('.leenvibe_cache', '.leanvibe_cache'),
            ('.cache/leenvibe', '.cache/leanvibe'),
            
            # Common config directories
            ('config/leenvibe', 'config/leanvibe'),
            ('configs/leenvibe', 'configs/leanvibe'),
        ]
        
        fixed_count = 0
        for old_pattern, new_pattern in special_cases:
            old_paths = list(self.project_root.rglob(old_pattern))
            for old_path in old_paths:
                new_path = old_path.parent / new_pattern.split('/')[-1]
                if self._rename_path(old_path, new_path):
                    fixed_count += 1
        
        # Fix specific file patterns
        self._fix_pyproject_urls()
        
        print(f"✅ Fixed {fixed_count} special cases")
    
    def _fix_pyproject_urls(self):
        """Fix URLs in pyproject.toml files"""
        pyproject_files = list(self.project_root.rglob("pyproject.toml"))
        
        for file_path in pyproject_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Fix GitHub URLs
                url_fixes = {
                    'github.com/leanvibe-ai/leenvibe-': 'github.com/leanvibe-ai/leanvibe-',
                    'github.com/leenvibe-ai/': 'github.com/leanvibe-ai/',
                }
                
                modified = content
                changes = []
                
                for old_url, new_url in url_fixes.items():
                    if old_url in modified:
                        modified = modified.replace(old_url, new_url)
                        changes.append(f"{old_url} -> {new_url}")
                
                if changes:
                    if not self.dry_run:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(modified)
                    
                    self.changes_made.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'type': 'url_fix',
                        'changes': changes,
                        'dry_run': self.dry_run
                    })
                    
                    print(f"🔗 Fixed URLs in {file_path.name}")
                    
            except Exception as e:
                print(f"❌ Error fixing URLs in {file_path}: {e}")
    
    def _should_skip_path(self, path: Path) -> bool:
        """Check if a path should be skipped"""
        path_parts = path.parts
        return any(skip_dir in path_parts for skip_dir in self.skip_directories)
    
    def _generate_report(self) -> Dict:
        """Generate a report of all changes made"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'dry_run': self.dry_run,
            'summary': {
                'total_changes': len(self.changes_made),
                'content_fixes': len([c for c in self.changes_made if c['type'] == 'content_fix']),
                'path_renames': len([c for c in self.changes_made if c['type'] == 'path_rename']),
                'url_fixes': len([c for c in self.changes_made if c['type'] == 'url_fix']),
            },
            'changes': self.changes_made
        }
        
        return report


def main():
    parser = argparse.ArgumentParser(description="Fix LeenVibe vs LeanVibe naming inconsistencies")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--dry-run", action="store_true", default=True, 
                       help="Show what would be changed without making changes")
    parser.add_argument("--execute", action="store_true", 
                       help="Actually make the changes (overrides --dry-run)")
    parser.add_argument("--output", help="Save report to JSON file")
    
    args = parser.parse_args()
    
    # If --execute is specified, turn off dry-run
    dry_run = not args.execute if args.execute else args.dry_run
    
    fixer = NamingInconsistencyFixer(args.project_root, dry_run=dry_run)
    report = fixer.fix_all_inconsistencies()
    
    # Print summary
    summary = report['summary']
    print("\n" + "="*60)
    print("🎯 LeanVibe Naming Inconsistency Fix Summary")
    print("="*60)
    print(f"🏷️  Mode: {'DRY RUN' if dry_run else 'EXECUTION'}")
    print(f"📊 Total Changes: {summary['total_changes']}")
    print(f"📝 Content Fixes: {summary['content_fixes']}")
    print(f"📂 Path Renames: {summary['path_renames']}")
    print(f"🔗 URL Fixes: {summary['url_fixes']}")
    
    if dry_run:
        print("\n💡 To actually make these changes, run with --execute")
        print("   python scripts/fix_naming_inconsistency.py --execute")
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Report saved to {args.output}")
    
    # Show sample of changes
    if report['changes']:
        print("\n📋 Sample Changes:")
        for change in report['changes'][:5]:
            if change['type'] == 'content_fix':
                print(f"   📝 {change['file']}: {len(change['changes'])} text replacements")
            elif change['type'] == 'path_rename':
                print(f"   📂 {change['old_path']} -> {change['new_path']}")
            elif change['type'] == 'url_fix':
                print(f"   🔗 {change['file']}: URL fixes")
        
        if len(report['changes']) > 5:
            print(f"   ... and {len(report['changes']) - 5} more changes")


if __name__ == "__main__":
    main()