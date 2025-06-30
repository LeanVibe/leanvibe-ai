#!/usr/bin/env python3
"""
LeanVibe Pre-commit Quality Gate

Prevents technical debt accumulation by enforcing quality standards
before code is committed. Based on Gemini AI best practices for
maintaining code quality.
"""

import ast
import os
import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict, Set
import subprocess
import argparse


class QualityGateViolation:
    """Represents a quality gate violation"""
    def __init__(self, file_path: str, line: int, rule: str, message: str, severity: str = "error"):
        self.file_path = file_path
        self.line = line
        self.rule = rule
        self.message = message
        self.severity = severity
    
    def __str__(self):
        return f"{self.file_path}:{self.line} [{self.rule}] {self.message}"


class PreCommitQualityGate:
    """Enforces quality standards before commits"""
    
    def __init__(self):
        self.violations: List[QualityGateViolation] = []
        
        # Quality thresholds
        self.MAX_FILE_SIZE = 500  # lines
        self.MAX_FUNCTION_COMPLEXITY = 10
        self.MAX_FUNCTION_LENGTH = 50  # lines
        self.MIN_DOCSTRING_LENGTH = 10  # characters
        
        # Patterns to detect
        self.BAD_PATTERNS = [
            (r'except\s*:', "Use specific exception types instead of bare except"),
            (r'print\s*\(', "Use logging instead of print statements"),
            (r'TODO|FIXME|XXX', "Resolve TODO/FIXME comments before committing"),
            (r'LeenVibe', "Use 'LeanVibe' instead of 'LeenVibe'"),
            (r'import\s+\*', "Avoid wildcard imports"),
            (r'#\s*type:\s*ignore', "Avoid type ignore comments, fix type issues"),
        ]
    
    def check_staged_files(self) -> bool:
        """Check all staged files for quality issues"""
        staged_files = self._get_staged_files()
        if not staged_files:
            print("No staged files to check")
            return True
        
        print(f"🔍 Checking {len(staged_files)} staged files...")
        
        passed = True
        for file_path in staged_files:
            if file_path.suffix == '.py':
                if not self._check_python_file(file_path):
                    passed = False
            elif file_path.suffix in ['.md', '.txt', '.yml', '.yaml']:
                if not self._check_text_file(file_path):
                    passed = False
        
        return passed
    
    def _get_staged_files(self) -> List[Path]:
        """Get list of staged files"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True, text=True, check=True
            )
            return [Path(f) for f in result.stdout.strip().split('\n') if f]
        except subprocess.CalledProcessError:
            return []
    
    def _check_python_file(self, file_path: Path) -> bool:
        """Check a Python file for quality issues"""
        if not file_path.exists():
            return True  # File was deleted
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Check file size
            if len(lines) > self.MAX_FILE_SIZE:
                self.violations.append(QualityGateViolation(
                    str(file_path), 1, "file-size",
                    f"File has {len(lines)} lines (max: {self.MAX_FILE_SIZE})",
                    "error"
                ))
            
            # Check patterns
            self._check_patterns(file_path, content)
            
            # Parse AST for deeper analysis
            try:
                tree = ast.parse(content)
                self._check_ast(file_path, tree, lines)
            except SyntaxError as e:
                self.violations.append(QualityGateViolation(
                    str(file_path), e.lineno or 1, "syntax",
                    f"Syntax error: {e.msg}", "error"
                ))
            
            return len([v for v in self.violations if v.file_path == str(file_path) and v.severity == "error"]) == 0
            
        except Exception as e:
            print(f"Error checking {file_path}: {e}")
            return False
    
    def _check_text_file(self, file_path: Path) -> bool:
        """Check text files for basic quality issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self._check_patterns(file_path, content)
            
            return len([v for v in self.violations if v.file_path == str(file_path) and v.severity == "error"]) == 0
            
        except Exception as e:
            print(f"Error checking {file_path}: {e}")
            return False
    
    def _check_patterns(self, file_path: Path, content: str):
        """Check for problematic patterns"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern, message in self.BAD_PATTERNS:
                if re.search(pattern, line):
                    # Special handling for TODO/FIXME - make them warnings in some cases
                    severity = "warning" if "TODO" in pattern and "# TODO:" in line else "error"
                    
                    self.violations.append(QualityGateViolation(
                        str(file_path), i, "pattern",
                        f"{message}: '{line.strip()}'",
                        severity
                    ))
    
    def _check_ast(self, file_path: Path, tree: ast.AST, lines: List[str]):
        """Check AST for structural issues"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._check_function(file_path, node, lines)
            elif isinstance(node, ast.ClassDef):
                self._check_class(file_path, node, lines)
    
    def _check_function(self, file_path: Path, func_node: ast.FunctionDef, lines: List[str]):
        """Check function quality"""
        # Calculate function length
        func_lines = func_node.end_lineno - func_node.lineno + 1 if func_node.end_lineno else 1
        
        if func_lines > self.MAX_FUNCTION_LENGTH:
            self.violations.append(QualityGateViolation(
                str(file_path), func_node.lineno, "function-length",
                f"Function '{func_node.name}' has {func_lines} lines (max: {self.MAX_FUNCTION_LENGTH})",
                "warning"
            ))
        
        # Calculate complexity
        complexity = self._calculate_complexity(func_node)
        if complexity > self.MAX_FUNCTION_COMPLEXITY:
            self.violations.append(QualityGateViolation(
                str(file_path), func_node.lineno, "complexity",
                f"Function '{func_node.name}' has complexity {complexity} (max: {self.MAX_FUNCTION_COMPLEXITY})",
                "error"
            ))
        
        # Check for docstring
        if not self._has_docstring(func_node):
            if not func_node.name.startswith('_'):  # Don't require for private methods
                self.violations.append(QualityGateViolation(
                    str(file_path), func_node.lineno, "docstring",
                    f"Function '{func_node.name}' missing docstring",
                    "warning"
                ))
        
        # Check for type hints (for public functions)
        if not func_node.name.startswith('_'):
            if not self._has_type_hints(func_node):
                self.violations.append(QualityGateViolation(
                    str(file_path), func_node.lineno, "type-hints",
                    f"Function '{func_node.name}' missing type hints",
                    "warning"
                ))
    
    def _check_class(self, file_path: Path, class_node: ast.ClassDef, lines: List[str]):
        """Check class quality"""
        # Check for docstring
        if not self._has_docstring(class_node):
            self.violations.append(QualityGateViolation(
                str(file_path), class_node.lineno, "docstring",
                f"Class '{class_node.name}' missing docstring",
                "warning"
            ))
    
    def _calculate_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _has_docstring(self, node) -> bool:
        """Check if node has a docstring"""
        if (node.body and isinstance(node.body[0], ast.Expr) 
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)):
            docstring = node.body[0].value.value
            return len(docstring.strip()) >= self.MIN_DOCSTRING_LENGTH
        return False
    
    def _has_type_hints(self, func_node: ast.FunctionDef) -> bool:
        """Check if function has type hints"""
        # Check return type
        has_return_hint = func_node.returns is not None
        
        # Check argument types
        has_arg_hints = any(arg.annotation for arg in func_node.args.args)
        
        return has_return_hint or has_arg_hints
    
    def print_violations(self):
        """Print all violations"""
        if not self.violations:
            print("✅ All quality checks passed!")
            return
        
        errors = [v for v in self.violations if v.severity == "error"]
        warnings = [v for v in self.violations if v.severity == "warning"]
        
        if errors:
            print(f"\n❌ {len(errors)} error(s) found:")
            for violation in errors:
                print(f"  {violation}")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} warning(s) found:")
            for violation in warnings:
                print(f"  {violation}")
        
        if errors:
            print("\n🚫 Commit blocked due to quality gate violations.")
            print("Fix the errors above and try again.")
        elif warnings:
            print("\n⚠️  Warnings found but commit allowed.")
            print("Consider fixing these issues to improve code quality.")
    
    def should_block_commit(self) -> bool:
        """Determine if commit should be blocked"""
        return len([v for v in self.violations if v.severity == "error"]) > 0


def run_additional_checks() -> bool:
    """Run additional quality checks using external tools"""
    checks_passed = True
    
    # Check if we have the tools available
    tools = {
        'black': 'python -m black --check --diff .',
        'isort': 'python -m isort --check-only --diff .',
        'mypy': 'python -m mypy --ignore-missing-imports .'
    }
    
    for tool, command in tools.items():
        try:
            result = subprocess.run(
                command.split(), 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"\n❌ {tool} check failed:")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                checks_passed = False
            else:
                print(f"✅ {tool} check passed")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {tool} check timed out")
            checks_passed = False
        except FileNotFoundError:
            print(f"⚠️  {tool} not found, skipping check")
    
    return checks_passed


def main():
    parser = argparse.ArgumentParser(description="Pre-commit quality gate for LeanVibe")
    parser.add_argument("--skip-external", action="store_true", 
                       help="Skip external tool checks (black, isort, mypy)")
    parser.add_argument("--warnings-as-errors", action="store_true",
                       help="Treat warnings as errors")
    
    args = parser.parse_args()
    
    print("🚦 LeanVibe Pre-commit Quality Gate")
    print("=" * 40)
    
    # Run main quality checks
    gate = PreCommitQualityGate()
    passed = gate.check_staged_files()
    
    # Adjust for warnings-as-errors
    if args.warnings_as_errors:
        warnings = [v for v in gate.violations if v.severity == "warning"]
        for warning in warnings:
            warning.severity = "error"
        passed = not gate.should_block_commit()
    
    gate.print_violations()
    
    # Run external tool checks if requested
    if not args.skip_external:
        print("\n🔧 Running external tool checks...")
        external_passed = run_additional_checks()
        passed = passed and external_passed
    
    # Final result
    if passed:
        print("\n🎉 Quality gate passed! Commit allowed.")
        sys.exit(0)
    else:
        print("\n🚫 Quality gate failed! Commit blocked.")
        print("\nTo bypass (not recommended): git commit --no-verify")
        sys.exit(1)


if __name__ == "__main__":
    main()