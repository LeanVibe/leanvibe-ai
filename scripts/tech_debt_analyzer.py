#!/usr/bin/env python3
"""
LeanVibe Technical Debt Analyzer

Automated tool for detecting and tracking technical debt across the codebase.
Implements Gemini AI insights for pattern-based debt detection.
"""

import ast
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, NamedTuple
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse


@dataclass
class TechnicalDebtIssue:
    """Represents a single technical debt issue"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # critical, high, medium, low
    description: str
    suggested_fix: str
    estimated_effort: str  # hours


@dataclass
class FileMetrics:
    """Metrics for a single file"""
    path: str
    lines: int
    functions: int
    classes: int
    complexity_score: float
    import_count: int
    has_type_hints: bool
    has_docstrings: bool
    duplicate_blocks: int


class TechnicalDebtAnalyzer:
    """Main analyzer class implementing Gemini-inspired detection patterns"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues: List[TechnicalDebtIssue] = []
        self.file_metrics: List[FileMetrics] = []
        
        # Thresholds based on Gemini recommendations
        self.FILE_SIZE_THRESHOLD = 500
        self.FUNCTION_COMPLEXITY_THRESHOLD = 10
        self.DUPLICATE_THRESHOLD = 5
        
    def analyze_codebase(self) -> Dict:
        """Run comprehensive technical debt analysis"""
        print("🔍 Starting LeanVibe Technical Debt Analysis...")
        
        # Analyze Python files
        python_files = list(self.project_root.rglob("*.py"))
        print(f"Found {len(python_files)} Python files to analyze")
        
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
                
            try:
                self._analyze_file(file_path)
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        
        # Analyze project structure
        self._analyze_project_structure()
        
        # Generate report
        return self._generate_report()
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Skip certain files/directories"""
        skip_patterns = [
            "__pycache__", ".git", "venv", ".venv", 
            "node_modules", ".pytest_cache", "build", "dist"
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Calculate metrics
            metrics = self._calculate_file_metrics(file_path, content, tree)
            self.file_metrics.append(metrics)
            
            # Detect issues
            self._detect_file_size_issues(metrics)
            self._detect_complexity_issues(file_path, tree)
            self._detect_error_handling_issues(file_path, content)
            self._detect_import_issues(file_path, tree)
            self._detect_naming_issues(file_path, content)
            self._detect_duplicate_code(file_path, content)
            
        except SyntaxError as e:
            self.issues.append(TechnicalDebtIssue(
                file_path=str(file_path),
                line_number=e.lineno or 0,
                issue_type="syntax_error",
                severity="critical",
                description=f"Syntax error: {e.msg}",
                suggested_fix="Fix syntax error",
                estimated_effort="0.5"
            ))
    
    def _calculate_file_metrics(self, file_path: Path, content: str, tree: ast.AST) -> FileMetrics:
        """Calculate comprehensive file metrics"""
        lines = len(content.splitlines())
        
        # Count functions and classes
        functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
        classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        
        # Calculate complexity (simplified cyclomatic complexity)
        complexity_score = self._calculate_complexity(tree)
        
        # Count imports
        imports = len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))])
        
        # Check for type hints
        has_type_hints = self._has_type_hints(tree)
        
        # Check for docstrings
        has_docstrings = self._has_docstrings(tree)
        
        # Detect duplicate blocks (simplified)
        duplicate_blocks = self._count_duplicate_blocks(content)
        
        return FileMetrics(
            path=str(file_path.relative_to(self.project_root)),
            lines=lines,
            functions=functions,
            classes=classes,
            complexity_score=complexity_score,
            import_count=imports,
            has_type_hints=has_type_hints,
            has_docstrings=has_docstrings,
            duplicate_blocks=duplicate_blocks
        )
    
    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.ExceptHandler,)):
                complexity += 1
        
        return complexity / max(1, len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]))
    
    def _has_type_hints(self, tree: ast.AST) -> bool:
        """Check if file has type hints"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.returns or any(arg.annotation for arg in node.args.args):
                    return True
        return False
    
    def _has_docstrings(self, tree: ast.AST) -> bool:
        """Check if file has docstrings"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if (node.body and isinstance(node.body[0], ast.Expr) 
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                    return True
        return False
    
    def _count_duplicate_blocks(self, content: str) -> int:
        """Count potential duplicate code blocks"""
        lines = content.splitlines()
        duplicates = 0
        
        # Simple duplicate detection - look for repeated line patterns
        for i in range(len(lines) - 5):
            block = lines[i:i+5]
            block_str = '\n'.join(block).strip()
            if len(block_str) > 50:  # Only consider substantial blocks
                if content.count(block_str) > 1:
                    duplicates += 1
        
        return duplicates
    
    def _detect_file_size_issues(self, metrics: FileMetrics):
        """Detect files that are too large"""
        if metrics.lines > self.FILE_SIZE_THRESHOLD:
            severity = "critical" if metrics.lines > 1000 else "high"
            
            self.issues.append(TechnicalDebtIssue(
                file_path=metrics.path,
                line_number=0,
                issue_type="large_file",
                severity=severity,
                description=f"File has {metrics.lines} lines (threshold: {self.FILE_SIZE_THRESHOLD})",
                suggested_fix="Split into smaller, focused modules",
                estimated_effort=str(max(4, metrics.lines // 200))
            ))
    
    def _detect_complexity_issues(self, file_path: Path, tree: ast.AST):
        """Detect overly complex functions"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_function_complexity(node)
                if complexity > self.FUNCTION_COMPLEXITY_THRESHOLD:
                    self.issues.append(TechnicalDebtIssue(
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=node.lineno,
                        issue_type="high_complexity",
                        severity="medium",
                        description=f"Function '{node.name}' has complexity {complexity} (threshold: {self.FUNCTION_COMPLEXITY_THRESHOLD})",
                        suggested_fix="Break down into smaller functions",
                        estimated_effort="2"
                    ))
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate complexity for a single function"""
        complexity = 1
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
    
    def _detect_error_handling_issues(self, file_path: Path, content: str):
        """Detect poor error handling patterns"""
        lines = content.splitlines()
        
        for i, line in enumerate(lines, 1):
            # Detect bare except clauses
            if re.search(r'except\s*:', line.strip()):
                self.issues.append(TechnicalDebtIssue(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=i,
                    issue_type="bare_except",
                    severity="high",
                    description="Bare except clause catches all exceptions",
                    suggested_fix="Use specific exception types",
                    estimated_effort="0.5"
                ))
            
            # Detect pass in except blocks
            if "except" in line and i < len(lines) and "pass" in lines[i].strip():
                self.issues.append(TechnicalDebtIssue(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=i,
                    issue_type="silent_exception",
                    severity="medium",
                    description="Exception silently ignored",
                    suggested_fix="Add proper error handling or logging",
                    estimated_effort="1"
                ))
    
    def _detect_import_issues(self, file_path: Path, tree: ast.AST):
        """Detect import-related issues"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                # Detect wildcard imports
                if any(alias.name == '*' for alias in node.names):
                    self.issues.append(TechnicalDebtIssue(
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=node.lineno,
                        issue_type="wildcard_import",
                        severity="medium",
                        description=f"Wildcard import from {node.module}",
                        suggested_fix="Use explicit imports",
                        estimated_effort="0.5"
                    ))
    
    def _detect_naming_issues(self, file_path: Path, content: str):
        """Detect naming inconsistencies"""
        # Check for LeenVibe vs LeanVibe
        if "LeenVibe" in content:
            lines_with_issue = [i for i, line in enumerate(content.splitlines(), 1) if "LeenVibe" in line]
            for line_num in lines_with_issue:
                self.issues.append(TechnicalDebtIssue(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=line_num,
                    issue_type="naming_inconsistency",
                    severity="high",
                    description="Uses 'LeenVibe' instead of standardized 'LeanVibe'",
                    suggested_fix="Replace with 'LeanVibe'",
                    estimated_effort="0.1"
                ))
    
    def _detect_duplicate_code(self, file_path: Path, content: str):
        """Detect duplicate code blocks"""
        # This is a simplified implementation
        # In production, you'd use more sophisticated algorithms
        lines = content.splitlines()
        
        for i in range(len(lines) - 10):
            block = '\n'.join(lines[i:i+10]).strip()
            if len(block) > 100 and content.count(block) > 1:
                self.issues.append(TechnicalDebtIssue(
                    file_path=str(file_path.relative_to(self.project_root)),
                    line_number=i + 1,
                    issue_type="duplicate_code",
                    severity="medium",
                    description="Duplicate code block detected",
                    suggested_fix="Extract to shared function or module",
                    estimated_effort="2"
                ))
                break  # Only report one per file to avoid spam
    
    def _analyze_project_structure(self):
        """Analyze overall project structure"""
        # Count services
        backend_services = list(self.project_root.glob("leanvibe-backend/app/services/*.py"))
        if len(backend_services) > 20:
            self.issues.append(TechnicalDebtIssue(
                file_path="leanvibe-backend/app/services/",
                line_number=0,
                issue_type="service_proliferation",
                severity="high",
                description=f"Too many services ({len(backend_services)}), consider consolidation",
                suggested_fix="Group related services, use strategy pattern",
                estimated_effort="8"
            ))
        
        # Check for config duplication
        config_files = list(self.project_root.rglob("*config*.py"))
        if len(config_files) > 5:
            self.issues.append(TechnicalDebtIssue(
                file_path="project_root",
                line_number=0,
                issue_type="config_duplication",
                severity="high",
                description=f"Multiple configuration files ({len(config_files)}) may indicate duplication",
                suggested_fix="Unify configuration system",
                estimated_effort="6"
            ))
    
    def _generate_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        # Group issues by severity
        critical_issues = [i for i in self.issues if i.severity == "critical"]
        high_issues = [i for i in self.issues if i.severity == "high"]
        medium_issues = [i for i in self.issues if i.severity == "medium"]
        low_issues = [i for i in self.issues if i.severity == "low"]
        
        # Calculate metrics
        total_lines = sum(m.lines for m in self.file_metrics)
        avg_file_size = total_lines / len(self.file_metrics) if self.file_metrics else 0
        large_files = len([m for m in self.file_metrics if m.lines > self.FILE_SIZE_THRESHOLD])
        
        # Calculate technical debt score (0-10, higher is better)
        total_issues = len(self.issues)
        total_files = len(self.file_metrics)
        
        score = 10 - min(10, (total_issues / max(1, total_files)) * 2)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "summary": {
                "total_files_analyzed": len(self.file_metrics),
                "total_lines": total_lines,
                "average_file_size": round(avg_file_size, 1),
                "large_files_count": large_files,
                "technical_debt_score": round(score, 1),
                "total_issues": total_issues,
                "critical_issues": len(critical_issues),
                "high_issues": len(high_issues),
                "medium_issues": len(medium_issues),
                "low_issues": len(low_issues)
            },
            "issues": [asdict(issue) for issue in self.issues],
            "file_metrics": [asdict(metric) for metric in self.file_metrics],
            "recommendations": self._generate_recommendations(critical_issues, high_issues)
        }
        
        return report
    
    def _generate_recommendations(self, critical_issues: List, high_issues: List) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if critical_issues:
            recommendations.append("🚨 Address critical issues immediately - these are blocking development efficiency")
        
        if len(high_issues) > 10:
            recommendations.append("⚠️ High number of high-priority issues - consider dedicated refactoring sprint")
        
        large_files = [m for m in self.file_metrics if m.lines > 1000]
        if large_files:
            recommendations.append(f"📄 {len(large_files)} files exceed 1000 lines - prioritize for splitting")
        
        naming_issues = [i for i in self.issues if i.issue_type == "naming_inconsistency"]
        if naming_issues:
            recommendations.append("🏷️ Naming inconsistencies detected - run global find/replace")
        
        recommendations.append("🔄 Set up pre-commit hooks to prevent future debt accumulation")
        recommendations.append("📊 Run this analysis weekly to track improvement")
        
        return recommendations


def main():
    parser = argparse.ArgumentParser(description="Analyze technical debt in LeanVibe codebase")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output", help="Output file for JSON report")
    parser.add_argument("--format", choices=["json", "summary"], default="summary", help="Output format")
    
    args = parser.parse_args()
    
    analyzer = TechnicalDebtAnalyzer(args.project_root)
    report = analyzer.analyze_codebase()
    
    if args.format == "json":
        output = json.dumps(report, indent=2)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Report saved to {args.output}")
        else:
            print(output)
    else:
        # Print summary
        summary = report["summary"]
        print("\n🎯 LeanVibe Technical Debt Analysis Summary")
        print("=" * 50)
        print(f"📊 Technical Debt Score: {summary['technical_debt_score']}/10")
        print(f"📁 Files Analyzed: {summary['total_files_analyzed']}")
        print(f"📏 Average File Size: {summary['average_file_size']} lines")
        print(f"🚨 Critical Issues: {summary['critical_issues']}")
        print(f"⚠️  High Priority: {summary['high_issues']}")
        print(f"📋 Medium Priority: {summary['medium_issues']}")
        print(f"📝 Low Priority: {summary['low_issues']}")
        
        if summary['large_files_count'] > 0:
            print(f"📄 Large Files (>{analyzer.FILE_SIZE_THRESHOLD} lines): {summary['large_files_count']}")
        
        print("\n🎯 Top Recommendations:")
        for i, rec in enumerate(report["recommendations"][:5], 1):
            print(f"{i}. {rec}")
        
        if summary['critical_issues'] > 0:
            print("\n🚨 Critical Issues Requiring Immediate Attention:")
            critical = [i for i in report["issues"] if i["severity"] == "critical"][:5]
            for issue in critical:
                print(f"   • {issue['file_path']}:{issue['line_number']} - {issue['description']}")


if __name__ == "__main__":
    main()