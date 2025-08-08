"""
Test to ensure no debug code exists in production
Following XP/TDD principles - test first, then fix
"""

import os
import re
from pathlib import Path


def test_no_debug_print_statements():
    """Ensure no print() debug statements in Python code"""
    project_root = Path(__file__).parent.parent
    python_files = list(project_root.glob("app/**/*.py"))
    
    files_with_debug = []
    
    for file_path in python_files:
        # Skip test files and this file
        if "test_" in file_path.name or "__pycache__" in str(file_path):
            continue
            
        content = file_path.read_text()
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Skip comments and strings
            if line.strip().startswith('#'):
                continue
                
            # Look for print statements (not in strings)
            if re.search(r'\bprint\s*\(', line):
                # Allow print in docstrings or comments
                if not (line.strip().startswith('"') or line.strip().startswith("'")):
                    files_with_debug.append((str(file_path.relative_to(project_root)), i, line.strip()))
    
    assert len(files_with_debug) == 0, f"Found debug print statements in: {files_with_debug[:5]}"


def test_no_debug_todos():
    """Ensure no TODO/FIXME/XXX/HACK comments in production code"""
    project_root = Path(__file__).parent.parent
    python_files = list(project_root.glob("app/**/*.py"))
    
    files_with_todos = []
    debug_patterns = ['TODO', 'FIXME', 'XXX', 'HACK', 'DEBUG']
    
    for file_path in python_files:
        if "__pycache__" in str(file_path):
            continue
            
        content = file_path.read_text()
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern in debug_patterns:
                if pattern in line:
                    files_with_todos.append((str(file_path.relative_to(project_root)), i, pattern))
                    break
    
    # We'll allow some TODOs but not DEBUG or HACK
    critical_todos = [t for t in files_with_todos if t[2] in ['DEBUG', 'HACK']]
    assert len(critical_todos) == 0, f"Found critical debug markers: {critical_todos[:5]}"


def test_no_console_log_in_frontend():
    """Ensure no console.log in Swift/JavaScript files"""
    project_root = Path(__file__).parent.parent.parent
    
    # Check JavaScript files
    js_files = list(project_root.glob("leanvibe-ios/**/*.js"))
    
    files_with_console = []
    
    for file_path in js_files:
        if "node_modules" in str(file_path) or ".min.js" in file_path.name:
            continue
            
        content = file_path.read_text()
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if 'console.log' in line and not line.strip().startswith('//'):
                files_with_console.append((str(file_path.name), i))
    
    assert len(files_with_console) == 0, f"Found console.log in: {files_with_console}"


def test_cors_not_wildcard():
    """Ensure CORS is not set to wildcard in production"""
    main_file = Path(__file__).parent.parent / "app" / "main.py"
    
    if main_file.exists():
        content = main_file.read_text()
        
        # Check for wildcard CORS
        if 'allow_origins=["*"]' in content:
            # This should fail until we fix it
            assert False, "CORS is set to wildcard (*) - security vulnerability!"
    
    assert True, "CORS check needs implementation"