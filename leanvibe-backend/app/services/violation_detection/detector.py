"""
Core Violation Detection Engine

Handles the actual detection of architectural violations using rules and patterns.
Extracted from architectural_violation_detector.py to improve modularity.
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from ...models.ast_models import FileAnalysis, SymbolType
from ..ast_service import ast_service
from .rule_manager import (
    ViolationType, 
    ViolationSeverity, 
    ArchitecturalLayer, 
    ArchitecturalRule, 
    rule_manager
)

logger = logging.getLogger(__name__)


@dataclass
class ViolationInstance:
    """Represents a detected architectural violation"""

    id: str
    rule_id: str
    file_path: str
    line_number: int
    column: int
    violation_type: ViolationType
    severity: ViolationSeverity
    message: str
    description: str
    suggestion: str
    context: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False


@dataclass
class ComponentMetrics:
    """Metrics for architectural components"""

    component_path: str
    lines_of_code: int = 0
    cyclomatic_complexity: int = 0
    coupling_score: float = 0.0
    cohesion_score: float = 0.0
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    last_analyzed: datetime = field(default_factory=datetime.now)
    violation_count: int = 0
    quality_score: float = 0.0


class ViolationDetector:
    """Core violation detection engine"""
    
    def __init__(self):
        self.violations: List[ViolationInstance] = []
        self.component_metrics: Dict[str, ComponentMetrics] = {}
        self.violation_cache: Dict[str, ViolationInstance] = {}
    
    async def detect_violations(self, file_path: str, file_analysis: FileAnalysis) -> List[ViolationInstance]:
        """Detect all violations in a file"""
        violations = []
        
        try:
            # Get enabled rules
            enabled_rules = rule_manager.get_enabled_rules()
            
            # Run different violation checks
            violations.extend(await self._check_size_violations(file_path, file_analysis))
            violations.extend(await self._check_complexity_violations(file_path, file_analysis))
            violations.extend(await self._check_coupling_violations(file_path, file_analysis))
            violations.extend(await self._check_naming_violations(file_path, file_analysis))
            violations.extend(await self._check_anti_patterns(file_path, file_analysis))
            violations.extend(await self._check_layer_violations(file_path, file_analysis))
            
            # Update component metrics
            await self._update_component_metrics(file_path, file_analysis, violations)
            
            # Cache violations
            for violation in violations:
                self.violation_cache[violation.id] = violation
            
            logger.info(f"Detected {len(violations)} violations in {file_path}")
            return violations
            
        except Exception as e:
            logger.error(f"Error detecting violations in {file_path}: {e}")
            return []
    
    def get_violations_for_file(self, file_path: str) -> List[ViolationInstance]:
        """Get all violations for a specific file"""
        return [v for v in self.violations if v.file_path == file_path and not v.resolved]
    
    def get_violations_by_type(self, violation_type: ViolationType) -> List[ViolationInstance]:
        """Get violations by type"""
        return [v for v in self.violations if v.violation_type == violation_type and not v.resolved]
    
    def get_violations_by_severity(self, min_severity: ViolationSeverity) -> List[ViolationInstance]:
        """Get violations by minimum severity level"""
        severity_order = {
            ViolationSeverity.INFO: 0,
            ViolationSeverity.LOW: 1,
            ViolationSeverity.MEDIUM: 2,
            ViolationSeverity.HIGH: 3,
            ViolationSeverity.CRITICAL: 4
        }
        min_level = severity_order.get(min_severity, 0)
        return [
            v for v in self.violations 
            if severity_order.get(v.severity, 0) >= min_level and not v.resolved
        ]
    
    async def _check_size_violations(self, file_path: str, file_analysis: FileAnalysis) -> List[ViolationInstance]:
        """Check for size-related violations"""
        violations = []
        
        # Get size rules
        size_rules = rule_manager.get_rules_by_type(ViolationType.SIZE_VIOLATION)
        
        # Check file size
        if file_analysis.lines_of_code:
            for rule in size_rules:
                if rule.max_lines and file_analysis.lines_of_code > rule.max_lines:
                    violation = ViolationInstance(
                        id=f"{rule.id}_{file_path}_{hash(file_path)}",
                        rule_id=rule.id,
                        file_path=file_path,
                        line_number=file_analysis.lines_of_code,
                        column=0,
                        violation_type=rule.violation_type,
                        severity=rule.severity,
                        message=f"File exceeds maximum size: {file_analysis.lines_of_code} > {rule.max_lines} lines",
                        description=rule.description,
                        suggestion=f"Consider breaking this file into smaller modules",
                        context={
                            "current_lines": file_analysis.lines_of_code,
                            "max_lines": rule.max_lines,
                            "excess_lines": file_analysis.lines_of_code - rule.max_lines
                        }
                    )
                    violations.append(violation)
        
        # Check function sizes
        if file_analysis.functions:
            for func in file_analysis.functions:
                func_lines = getattr(func, 'lines_of_code', 0) or 0
                for rule in size_rules:
                    if rule.id == "max_function_size" and rule.max_lines and func_lines > rule.max_lines:
                        violation = ViolationInstance(
                            id=f"{rule.id}_{file_path}_{func.name}",
                            rule_id=rule.id,
                            file_path=file_path,
                            line_number=func.line_number,
                            column=func.column,
                            violation_type=rule.violation_type,
                            severity=rule.severity,
                            message=f"Function '{func.name}' exceeds maximum size: {func_lines} > {rule.max_lines} lines",
                            description=rule.description,
                            suggestion=f"Consider breaking function '{func.name}' into smaller functions",
                            context={
                                "function_name": func.name,
                                "current_lines": func_lines,
                                "max_lines": rule.max_lines
                            }
                        )
                        violations.append(violation)
        
        return violations
    
    async def _check_complexity_violations(self, file_path: str, file_analysis: FileAnalysis) -> List[ViolationInstance]:
        """Check for complexity-related violations"""
        violations = []
        
        complexity_rules = rule_manager.get_rules_by_type(ViolationType.COMPLEXITY_VIOLATION)
        
        if file_analysis.functions:
            for func in file_analysis.functions:
                complexity = getattr(func, 'cyclomatic_complexity', 0) or 0
                for rule in complexity_rules:
                    if rule.max_complexity and complexity > rule.max_complexity:
                        violation = ViolationInstance(
                            id=f"{rule.id}_{file_path}_{func.name}",
                            rule_id=rule.id,
                            file_path=file_path,
                            line_number=func.line_number,
                            column=func.column,
                            violation_type=rule.violation_type,
                            severity=rule.severity,
                            message=f"Function '{func.name}' has high complexity: {complexity} > {rule.max_complexity}",
                            description=rule.description,
                            suggestion=f"Simplify function '{func.name}' by extracting logic or reducing branching",
                            context={
                                "function_name": func.name,
                                "complexity": complexity,
                                "max_complexity": rule.max_complexity
                            }
                        )
                        violations.append(violation)
        
        return violations
    
    async def _check_coupling_violations(self, file_path: str, file_analysis: FileAnalysis) -> List[ViolationInstance]:
        """Check for coupling-related violations"""
        violations = []
        
        coupling_rules = rule_manager.get_rules_by_type(ViolationType.COUPLING_VIOLATION)
        
        # Count imports as dependencies
        dependency_count = len(file_analysis.imports) if file_analysis.imports else 0
        
        for rule in coupling_rules:
            if rule.max_dependencies and dependency_count > rule.max_dependencies:
                violation = ViolationInstance(
                    id=f"{rule.id}_{file_path}",
                    rule_id=rule.id,
                    file_path=file_path,
                    line_number=1,
                    column=0,
                    violation_type=rule.violation_type,
                    severity=rule.severity,
                    message=f"File has too many dependencies: {dependency_count} > {rule.max_dependencies}",
                    description=rule.description,
                    suggestion="Consider using dependency injection or breaking the module into smaller parts",
                    context={
                        "dependency_count": dependency_count,
                        "max_dependencies": rule.max_dependencies,
                        "imports": [imp.module for imp in file_analysis.imports] if file_analysis.imports else []
                    }
                )
                violations.append(violation)
        
        return violations
    
    async def _check_naming_violations(self, file_path: str, file_analysis: FileAnalysis) -> List[ViolationInstance]:
        """Check for naming convention violations"""
        violations = []
        
        naming_rules = rule_manager.get_rules_by_type(ViolationType.NAMING_CONVENTION_VIOLATION)
        
        # Read file content for pattern matching
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for rule in naming_rules:
                if rule.pattern:
                    matches = re.finditer(rule.pattern, content, re.MULTILINE)
                    for match in matches:
                        # Calculate line number
                        line_number = content[:match.start()].count('\n') + 1
                        
                        violation = ViolationInstance(
                            id=f"{rule.id}_{file_path}_{line_number}",
                            rule_id=rule.id,
                            file_path=file_path,
                            line_number=line_number,
                            column=match.start() - content.rfind('\n', 0, match.start()),
                            violation_type=rule.violation_type,
                            severity=rule.severity,
                            message=f"Naming convention violation: {match.group()}",
                            description=rule.description,
                            suggestion="Follow the project's naming conventions",
                            context={
                                "matched_text": match.group(),
                                "rule_pattern": rule.pattern
                            }
                        )
                        violations.append(violation)
        
        except Exception as e:
            logger.error(f"Error checking naming violations in {file_path}: {e}")
        
        return violations
    
    async def _check_anti_patterns(self, file_path: str, file_analysis: FileAnalysis) -> List[ViolationInstance]:
        """Check for anti-patterns"""
        violations = []
        
        anti_pattern_rules = rule_manager.get_rules_by_type(ViolationType.ANTI_PATTERN)
        
        # Check for God Class pattern
        if file_analysis.classes:
            for cls in file_analysis.classes:
                class_lines = getattr(cls, 'lines_of_code', 0) or 0
                method_count = len(getattr(cls, 'methods', [])) if hasattr(cls, 'methods') else 0
                
                for rule in anti_pattern_rules:
                    if rule.id == "god_class" and rule.max_lines and class_lines > rule.max_lines:
                        violation = ViolationInstance(
                            id=f"{rule.id}_{file_path}_{cls.name}",
                            rule_id=rule.id,
                            file_path=file_path,
                            line_number=cls.line_number,
                            column=cls.column,
                            violation_type=rule.violation_type,
                            severity=rule.severity,
                            message=f"God Class detected: '{cls.name}' has {class_lines} lines and {method_count} methods",
                            description=rule.description,
                            suggestion=f"Break class '{cls.name}' into smaller, more focused classes",
                            context={
                                "class_name": cls.name,
                                "lines_of_code": class_lines,
                                "method_count": method_count,
                                "max_lines": rule.max_lines
                            }
                        )
                        violations.append(violation)
        
        # Check for long parameter lists
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for rule in anti_pattern_rules:
                if rule.id == "long_parameter_list" and rule.pattern:
                    matches = re.finditer(rule.pattern, content, re.MULTILINE)
                    for match in matches:
                        line_number = content[:match.start()].count('\n') + 1
                        
                        violation = ViolationInstance(
                            id=f"{rule.id}_{file_path}_{line_number}",
                            rule_id=rule.id,
                            file_path=file_path,
                            line_number=line_number,
                            column=match.start() - content.rfind('\n', 0, match.start()),
                            violation_type=rule.violation_type,
                            severity=rule.severity,
                            message="Long parameter list detected",
                            description=rule.description,
                            suggestion="Consider using a parameter object or reducing the number of parameters",
                            context={
                                "matched_function": match.group(),
                                "parameter_count": match.group().count(',') + 1
                            }
                        )
                        violations.append(violation)
        
        except Exception as e:
            logger.error(f"Error checking anti-patterns in {file_path}: {e}")
        
        return violations
    
    async def _check_layer_violations(self, file_path: str, file_analysis: FileAnalysis) -> List[ViolationInstance]:
        """Check for layer violation"""
        violations = []
        
        layer_rules = rule_manager.get_rules_by_type(ViolationType.LAYER_VIOLATION)
        current_layer = rule_manager.determine_layer(file_path)
        
        # Check imports against layer rules
        if file_analysis.imports:
            for imp in file_analysis.imports:
                import_layer = rule_manager.determine_layer(imp.module)
                
                for rule in layer_rules:
                    if (rule.forbidden_layers and 
                        current_layer in rule.forbidden_layers and 
                        import_layer in rule.forbidden_layers):
                        
                        violation = ViolationInstance(
                            id=f"{rule.id}_{file_path}_{imp.module}",
                            rule_id=rule.id,
                            file_path=file_path,
                            line_number=imp.line_number,
                            column=0,
                            violation_type=rule.violation_type,
                            severity=rule.severity,
                            message=f"Layer violation: {current_layer} importing from {import_layer}",
                            description=rule.description,
                            suggestion="Follow the architectural layer separation rules",
                            context={
                                "current_layer": current_layer,
                                "imported_layer": import_layer,
                                "imported_module": imp.module
                            }
                        )
                        violations.append(violation)
        
        return violations
    
    async def _update_component_metrics(self, file_path: str, file_analysis: FileAnalysis, violations: List[ViolationInstance]):
        """Update component metrics based on analysis"""
        try:
            metrics = self.component_metrics.get(file_path, ComponentMetrics(component_path=file_path))
            
            # Update basic metrics
            metrics.lines_of_code = file_analysis.lines_of_code or 0
            metrics.violation_count = len(violations)
            metrics.last_analyzed = datetime.now()
            
            # Calculate complexity
            total_complexity = 0
            if file_analysis.functions:
                for func in file_analysis.functions:
                    total_complexity += getattr(func, 'cyclomatic_complexity', 0) or 0
            metrics.cyclomatic_complexity = total_complexity
            
            # Calculate dependencies
            if file_analysis.imports:
                metrics.dependencies = {imp.module for imp in file_analysis.imports}
            
            # Calculate quality score (simplified)
            base_score = 100.0
            penalty_per_violation = {
                ViolationSeverity.CRITICAL: 20,
                ViolationSeverity.HIGH: 10,
                ViolationSeverity.MEDIUM: 5,
                ViolationSeverity.LOW: 2,
                ViolationSeverity.INFO: 1
            }
            
            for violation in violations:
                base_score -= penalty_per_violation.get(violation.severity, 1)
            
            metrics.quality_score = max(0.0, base_score)
            
            self.component_metrics[file_path] = metrics
            
        except Exception as e:
            logger.error(f"Error updating component metrics for {file_path}: {e}")


# Global violation detector instance
violation_detector = ViolationDetector()