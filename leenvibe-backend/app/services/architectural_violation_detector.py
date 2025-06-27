"""
Real-time Architectural Violation Detection Service

Monitors code changes and detects violations of architectural patterns,
design principles, and coding standards in real-time.
"""

import asyncio
import hashlib
import logging
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..models.ast_models import (
    Dependency,
    FileAnalysis,
    LanguageType,
    ProjectIndex,
    Reference,
    Symbol,
    SymbolType,
)
from ..models.monitoring_models import ChangeType, FileChange
from .ast_service import ast_service
from .graph_service import graph_service
from .symbol_dependency_tracker import symbol_dependency_tracker

logger = logging.getLogger(__name__)


class ViolationType(str, Enum):
    """Types of architectural violations"""

    LAYER_VIOLATION = "layer_violation"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    DEPENDENCY_RULE_VIOLATION = "dependency_rule_violation"
    NAMING_CONVENTION_VIOLATION = "naming_convention_violation"
    SIZE_VIOLATION = "size_violation"
    COMPLEXITY_VIOLATION = "complexity_violation"
    COUPLING_VIOLATION = "coupling_violation"
    COHESION_VIOLATION = "cohesion_violation"
    ABSTRACTION_VIOLATION = "abstraction_violation"
    ENCAPSULATION_VIOLATION = "encapsulation_violation"
    PATTERN_VIOLATION = "pattern_violation"
    ANTI_PATTERN = "anti_pattern"


class ViolationSeverity(str, Enum):
    """Severity levels for violations"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ArchitecturalLayer(str, Enum):
    """Common architectural layers"""

    PRESENTATION = "presentation"
    BUSINESS = "business"
    DATA = "data"
    INFRASTRUCTURE = "infrastructure"
    UTILITY = "utility"
    TEST = "test"
    UNKNOWN = "unknown"


@dataclass
class ArchitecturalRule:
    """Represents an architectural rule to be enforced"""

    rule_id: str
    name: str
    description: str
    violation_type: ViolationType
    severity: ViolationSeverity
    enabled: bool = True
    pattern: Optional[str] = None  # Regex pattern for detection
    conditions: List[str] = field(default_factory=list)  # Rule conditions
    exceptions: List[str] = field(default_factory=list)  # Exception patterns
    layers_from: Set[ArchitecturalLayer] = field(default_factory=set)
    layers_to: Set[ArchitecturalLayer] = field(default_factory=set)
    confidence_threshold: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ViolationInstance:
    """Represents a detected violation"""

    violation_id: str
    rule_id: str
    violation_type: ViolationType
    severity: ViolationSeverity
    file_path: str
    symbol_id: Optional[str] = None
    symbol_name: Optional[str] = None
    line_start: int = 0
    line_end: int = 0
    description: str = ""
    details: str = ""
    suggestion: str = ""
    confidence_score: float = 0.0
    related_violations: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentMetrics:
    """Metrics for architectural components"""

    component_id: str
    component_type: str
    file_path: str
    size_metrics: Dict[str, int] = field(default_factory=dict)  # lines, symbols, etc.
    complexity_metrics: Dict[str, float] = field(
        default_factory=dict
    )  # cyclomatic, cognitive
    coupling_metrics: Dict[str, int] = field(default_factory=dict)  # afferent, efferent
    cohesion_score: float = 0.0
    dependencies_in: int = 0
    dependencies_out: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ArchitecturalReport:
    """Report of architectural violations"""

    report_id: str
    project_id: str
    analysis_timestamp: datetime
    violations: List[ViolationInstance]
    component_metrics: List[ComponentMetrics]
    summary: Dict[str, Any]
    trends: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    quality_score: float = 0.0


class ArchitecturalViolationDetector:
    """
    Real-time Architectural Violation Detection Service

    Monitors code for architectural violations, design pattern violations,
    and adherence to coding standards and best practices.
    """

    def __init__(self):
        # Rule and violation storage
        self.rules: Dict[str, ArchitecturalRule] = {}
        self.violations: List[ViolationInstance] = []
        self.component_metrics: Dict[str, ComponentMetrics] = {}
        self.violation_cache: Dict[str, ViolationInstance] = {}

        # Architecture mapping
        self.layer_patterns: Dict[ArchitecturalLayer, List[str]] = {}
        self.component_layers: Dict[str, ArchitecturalLayer] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)

        # Real-time monitoring
        self.active_monitors: Set[str] = set()  # File paths being monitored
        self.violation_subscribers: Dict[str, Set[str]] = defaultdict(
            set
        )  # client subscriptions
        self.pending_analysis: deque[str] = deque()

        # Configuration
        self.max_file_size = 10000  # lines
        self.max_function_size = 100  # lines
        self.max_class_size = 500  # lines
        self.max_complexity = 15
        self.max_dependencies = 20
        self.real_time_enabled = True

        # Performance metrics
        self.metrics = {
            "total_violations": 0,
            "violations_by_type": defaultdict(int),
            "violations_by_severity": defaultdict(int),
            "rules_checked": 0,
            "analysis_time_ms": 0.0,
            "false_positives": 0,
            "components_analyzed": 0,
        }

        # Background tasks
        self.analysis_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None

        # Initialize built-in rules
        self._initialize_built_in_rules()
        self._initialize_layer_patterns()

    async def initialize(self) -> bool:
        """Initialize the architectural violation detector"""
        try:
            logger.info("Initializing Architectural Violation Detector...")

            # Start background tasks
            self.analysis_task = asyncio.create_task(
                self._background_analysis_processor()
            )
            self.monitoring_task = asyncio.create_task(self._continuous_monitoring())

            logger.info(
                f"Architectural violation detector initialized with {len(self.rules)} rules"
            )
            return True

        except Exception as e:
            logger.error(f"Error initializing architectural violation detector: {e}")
            return False

    async def shutdown(self):
        """Shutdown the violation detector"""
        try:
            logger.info("Shutting down architectural violation detector...")

            # Cancel background tasks
            if self.analysis_task:
                self.analysis_task.cancel()
                try:
                    await self.analysis_task
                except asyncio.CancelledError:
                    pass

            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass

            logger.info("Architectural violation detector shutdown complete")

        except Exception as e:
            logger.error(f"Error during violation detector shutdown: {e}")

    async def analyze_file(
        self, file_path: str, content: Optional[str] = None
    ) -> List[ViolationInstance]:
        """Analyze a file for architectural violations"""
        try:
            start_time = time.time()
            violations = []

            # Get file analysis
            file_analysis = await ast_service.analyze_file(file_path, content)
            if not file_analysis:
                return violations

            # Determine architectural layer
            layer = self._determine_layer(file_path)
            self.component_layers[file_path] = layer

            # Calculate component metrics
            component_metrics = await self._calculate_component_metrics(
                file_path, file_analysis
            )
            self.component_metrics[file_path] = component_metrics

            # Apply architectural rules
            for rule in self.rules.values():
                if rule.enabled:
                    rule_violations = await self._apply_rule(
                        rule, file_path, file_analysis, component_metrics
                    )
                    violations.extend(rule_violations)

            # Check for circular dependencies
            circular_violations = await self._detect_circular_dependencies(
                file_path, file_analysis
            )
            violations.extend(circular_violations)

            # Store violations
            for violation in violations:
                self.violations.append(violation)
                self.violation_cache[violation.violation_id] = violation

            # Update metrics
            analysis_time = (time.time() - start_time) * 1000
            self._update_metrics(violations, analysis_time)

            logger.debug(f"Analyzed {file_path}: found {len(violations)} violations")
            return violations

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return []

    async def analyze_project(self, project_id: str) -> ArchitecturalReport:
        """Analyze entire project for architectural violations"""
        try:
            start_time = time.time()

            # Get project index
            project_index = await graph_service.get_project_index(project_id)
            if not project_index:
                return self._create_empty_report(project_id)

            all_violations = []
            all_component_metrics = []

            # Analyze each file
            for file_path, file_analysis in project_index.files.items():
                violations = await self.analyze_file(file_path)
                all_violations.extend(violations)

                if file_path in self.component_metrics:
                    all_component_metrics.append(self.component_metrics[file_path])

            # Generate summary
            summary = self._generate_summary(all_violations, all_component_metrics)

            # Calculate quality score
            quality_score = self._calculate_quality_score(
                all_violations, len(project_index.files)
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(all_violations, summary)

            report = ArchitecturalReport(
                report_id=self._generate_report_id(),
                project_id=project_id,
                analysis_timestamp=datetime.now(),
                violations=all_violations,
                component_metrics=all_component_metrics,
                summary=summary,
                recommendations=recommendations,
                quality_score=quality_score,
            )

            analysis_time = (time.time() - start_time) * 1000
            logger.info(
                f"Project analysis completed in {analysis_time:.2f}ms: "
                f"{len(all_violations)} violations found"
            )

            return report

        except Exception as e:
            logger.error(f"Error analyzing project {project_id}: {e}")
            return self._create_empty_report(project_id)

    async def process_file_change(
        self, file_change: FileChange
    ) -> List[ViolationInstance]:
        """Process a file change and detect new violations"""
        try:
            if not file_change.is_code_file():
                return []

            file_path = file_change.file_path

            if file_change.change_type == ChangeType.DELETED:
                # Remove violations for deleted file
                self._remove_violations_for_file(file_path)
                return []

            elif file_change.change_type in [ChangeType.MODIFIED, ChangeType.CREATED]:
                # Re-analyze the file
                violations = await self.analyze_file(file_path)

                # Notify subscribers
                if self.real_time_enabled:
                    await self._notify_violation_subscribers(file_path, violations)

                return violations

            return []

        except Exception as e:
            logger.error(
                f"Error processing file change for {file_change.file_path}: {e}"
            )
            return []

    def add_rule(self, rule: ArchitecturalRule) -> bool:
        """Add a new architectural rule"""
        try:
            self.rules[rule.rule_id] = rule
            logger.debug(f"Added architectural rule: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"Error adding rule {rule.rule_id}: {e}")
            return False

    def remove_rule(self, rule_id: str) -> bool:
        """Remove an architectural rule"""
        try:
            if rule_id in self.rules:
                del self.rules[rule_id]
                logger.debug(f"Removed architectural rule: {rule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing rule {rule_id}: {e}")
            return False

    def get_violations_for_file(self, file_path: str) -> List[ViolationInstance]:
        """Get all violations for a specific file"""
        return [v for v in self.violations if v.file_path == file_path]

    def get_violations_by_type(
        self, violation_type: ViolationType
    ) -> List[ViolationInstance]:
        """Get all violations of a specific type"""
        return [v for v in self.violations if v.violation_type == violation_type]

    def get_violations_by_severity(
        self, severity: ViolationSeverity
    ) -> List[ViolationInstance]:
        """Get all violations of a specific severity"""
        return [v for v in self.violations if v.severity == severity]

    def subscribe_to_violations(self, file_path: str, client_id: str):
        """Subscribe to violation notifications for a file"""
        self.violation_subscribers[file_path].add(client_id)
        logger.debug(f"Client {client_id} subscribed to violations for {file_path}")

    def unsubscribe_from_violations(self, file_path: str, client_id: str):
        """Unsubscribe from violation notifications"""
        self.violation_subscribers[file_path].discard(client_id)
        if not self.violation_subscribers[file_path]:
            del self.violation_subscribers[file_path]
        logger.debug(f"Client {client_id} unsubscribed from violations for {file_path}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get violation detection metrics"""
        return {
            **self.metrics,
            "active_rules": len([r for r in self.rules.values() if r.enabled]),
            "total_rules": len(self.rules),
            "active_monitors": len(self.active_monitors),
            "violation_subscribers": len(self.violation_subscribers),
            "pending_analysis": len(self.pending_analysis),
            "component_metrics_count": len(self.component_metrics),
        }

    def _initialize_built_in_rules(self):
        """Initialize built-in architectural rules"""
        try:
            # Layer violation rules
            self.rules["layer_presentation_to_data"] = ArchitecturalRule(
                rule_id="layer_presentation_to_data",
                name="Presentation Layer to Data Layer Violation",
                description="Presentation layer should not directly access data layer",
                violation_type=ViolationType.LAYER_VIOLATION,
                severity=ViolationSeverity.ERROR,
                layers_from={ArchitecturalLayer.PRESENTATION},
                layers_to={ArchitecturalLayer.DATA},
                confidence_threshold=0.8,
            )

            # Size violation rules
            self.rules["file_size_violation"] = ArchitecturalRule(
                rule_id="file_size_violation",
                name="File Size Violation",
                description=f"Files should not exceed {self.max_file_size} lines",
                violation_type=ViolationType.SIZE_VIOLATION,
                severity=ViolationSeverity.WARNING,
                confidence_threshold=0.9,
            )

            self.rules["function_size_violation"] = ArchitecturalRule(
                rule_id="function_size_violation",
                name="Function Size Violation",
                description=f"Functions should not exceed {self.max_function_size} lines",
                violation_type=ViolationType.SIZE_VIOLATION,
                severity=ViolationSeverity.WARNING,
                confidence_threshold=0.9,
            )

            self.rules["class_size_violation"] = ArchitecturalRule(
                rule_id="class_size_violation",
                name="Class Size Violation",
                description=f"Classes should not exceed {self.max_class_size} lines",
                violation_type=ViolationType.SIZE_VIOLATION,
                severity=ViolationSeverity.WARNING,
                confidence_threshold=0.9,
            )

            # Complexity violation rules
            self.rules["complexity_violation"] = ArchitecturalRule(
                rule_id="complexity_violation",
                name="Complexity Violation",
                description=f"Functions should not exceed complexity of {self.max_complexity}",
                violation_type=ViolationType.COMPLEXITY_VIOLATION,
                severity=ViolationSeverity.WARNING,
                confidence_threshold=0.8,
            )

            # Coupling violation rules
            self.rules["high_coupling_violation"] = ArchitecturalRule(
                rule_id="high_coupling_violation",
                name="High Coupling Violation",
                description=f"Components should not have more than {self.max_dependencies} dependencies",
                violation_type=ViolationType.COUPLING_VIOLATION,
                severity=ViolationSeverity.WARNING,
                confidence_threshold=0.7,
            )

            # Naming convention rules
            self.rules["python_naming_convention"] = ArchitecturalRule(
                rule_id="python_naming_convention",
                name="Python Naming Convention",
                description="Python code should follow PEP 8 naming conventions",
                violation_type=ViolationType.NAMING_CONVENTION_VIOLATION,
                severity=ViolationSeverity.INFO,
                pattern=r"[A-Z][a-z]+[A-Z]",  # CamelCase in Python (should be snake_case)
                confidence_threshold=0.6,
            )

            # Anti-pattern detection
            self.rules["god_class_antipattern"] = ArchitecturalRule(
                rule_id="god_class_antipattern",
                name="God Class Anti-pattern",
                description="Classes should not be overly large and handle too many responsibilities",
                violation_type=ViolationType.ANTI_PATTERN,
                severity=ViolationSeverity.ERROR,
                confidence_threshold=0.7,
            )

            logger.debug(f"Initialized {len(self.rules)} built-in architectural rules")

        except Exception as e:
            logger.error(f"Error initializing built-in rules: {e}")

    def _initialize_layer_patterns(self):
        """Initialize patterns for architectural layer detection"""
        self.layer_patterns = {
            ArchitecturalLayer.PRESENTATION: [
                r".*/(ui|views|components|controllers|handlers)/.*",
                r".*/presentation/.*",
                r".*/(templates|static)/.*",
            ],
            ArchitecturalLayer.BUSINESS: [
                r".*/(services|business|domain|logic)/.*",
                r".*/(models|entities)/.*",
                r".*/core/.*",
            ],
            ArchitecturalLayer.DATA: [
                r".*/(data|repository|dao|models)/.*",
                r".*/(database|db|storage)/.*",
                r".*/(migrations|schemas)/.*",
            ],
            ArchitecturalLayer.INFRASTRUCTURE: [
                r".*/(infrastructure|config|utils|common)/.*",
                r".*/(external|adapters|clients)/.*",
            ],
            ArchitecturalLayer.TEST: [r".*/test.*/.*", r".*_test\..*", r".*/tests/.*"],
        }

    def _determine_layer(self, file_path: str) -> ArchitecturalLayer:
        """Determine the architectural layer of a file"""
        file_path_lower = file_path.lower()

        for layer, patterns in self.layer_patterns.items():
            for pattern in patterns:
                if re.match(pattern, file_path_lower):
                    return layer

        return ArchitecturalLayer.UNKNOWN

    async def _calculate_component_metrics(
        self, file_path: str, file_analysis: FileAnalysis
    ) -> ComponentMetrics:
        """Calculate metrics for a component"""
        try:
            # Size metrics
            total_lines = (
                len(file_analysis.content.splitlines())
                if hasattr(file_analysis, "content")
                else 0
            )
            symbol_count = len(file_analysis.symbols)

            # Complexity metrics (simplified)
            complexity_sum = 0
            for symbol in file_analysis.symbols:
                if hasattr(symbol, "complexity") and symbol.complexity is not None:
                    complexity_sum += symbol.complexity
                else:
                    complexity_sum += 1
            avg_complexity = complexity_sum / symbol_count if symbol_count > 0 else 0

            # Coupling metrics
            dependencies_out = len(file_analysis.dependencies)
            dependencies_in = await self._count_incoming_dependencies(file_path)

            # Cohesion score (simplified - based on symbol types diversity)
            symbol_types = set(symbol.symbol_type for symbol in file_analysis.symbols)
            cohesion_score = 1.0 / len(symbol_types) if symbol_types else 0.0

            return ComponentMetrics(
                component_id=file_path,
                component_type="file",
                file_path=file_path,
                size_metrics={
                    "lines": total_lines,
                    "symbols": symbol_count,
                    "functions": len(
                        [
                            s
                            for s in file_analysis.symbols
                            if s.symbol_type == SymbolType.FUNCTION
                        ]
                    ),
                    "classes": len(
                        [
                            s
                            for s in file_analysis.symbols
                            if s.symbol_type == SymbolType.CLASS
                        ]
                    ),
                },
                complexity_metrics={
                    "average_complexity": avg_complexity,
                    "max_complexity": max(
                        (
                            getattr(s, "complexity", 1) or 1
                            for s in file_analysis.symbols
                        ),
                        default=0,
                    ),
                },
                coupling_metrics={
                    "afferent_coupling": dependencies_in,
                    "efferent_coupling": dependencies_out,
                },
                cohesion_score=cohesion_score,
                dependencies_in=dependencies_in,
                dependencies_out=dependencies_out,
            )

        except Exception as e:
            logger.error(f"Error calculating component metrics for {file_path}: {e}")
            return ComponentMetrics(
                component_id=file_path, component_type="file", file_path=file_path
            )

    async def _apply_rule(
        self,
        rule: ArchitecturalRule,
        file_path: str,
        file_analysis: FileAnalysis,
        component_metrics: ComponentMetrics,
    ) -> List[ViolationInstance]:
        """Apply an architectural rule to a file"""
        violations = []

        try:
            if rule.violation_type == ViolationType.SIZE_VIOLATION:
                violations.extend(
                    self._check_size_violations(
                        rule, file_path, file_analysis, component_metrics
                    )
                )

            elif rule.violation_type == ViolationType.COMPLEXITY_VIOLATION:
                violations.extend(
                    self._check_complexity_violations(rule, file_path, file_analysis)
                )

            elif rule.violation_type == ViolationType.COUPLING_VIOLATION:
                violations.extend(
                    self._check_coupling_violations(rule, file_path, component_metrics)
                )

            elif rule.violation_type == ViolationType.LAYER_VIOLATION:
                violations.extend(
                    await self._check_layer_violations(rule, file_path, file_analysis)
                )

            elif rule.violation_type == ViolationType.NAMING_CONVENTION_VIOLATION:
                violations.extend(
                    self._check_naming_violations(rule, file_path, file_analysis)
                )

            elif rule.violation_type == ViolationType.ANTI_PATTERN:
                violations.extend(
                    self._check_anti_patterns(
                        rule, file_path, file_analysis, component_metrics
                    )
                )

            self.metrics["rules_checked"] += 1

        except Exception as e:
            logger.error(f"Error applying rule {rule.rule_id} to {file_path}: {e}")

        return violations

    def _check_size_violations(
        self,
        rule: ArchitecturalRule,
        file_path: str,
        file_analysis: FileAnalysis,
        component_metrics: ComponentMetrics,
    ) -> List[ViolationInstance]:
        """Check for size violations"""
        violations = []

        # Check file size
        if rule.rule_id == "file_size_violation":
            file_lines = component_metrics.size_metrics.get("lines", 0)
            if file_lines > self.max_file_size:
                violations.append(
                    ViolationInstance(
                        violation_id=self._generate_violation_id(),
                        rule_id=rule.rule_id,
                        violation_type=rule.violation_type,
                        severity=rule.severity,
                        file_path=file_path,
                        description=f"File has {file_lines} lines, exceeds limit of {self.max_file_size}",
                        suggestion=f"Consider splitting this file into smaller, more focused modules",
                        confidence_score=0.9,
                    )
                )

        # Check function sizes
        elif rule.rule_id == "function_size_violation":
            for symbol in file_analysis.symbols:
                if symbol.symbol_type == SymbolType.FUNCTION:
                    function_lines = symbol.line_end - symbol.line_start + 1
                    if function_lines > self.max_function_size:
                        violations.append(
                            ViolationInstance(
                                violation_id=self._generate_violation_id(),
                                rule_id=rule.rule_id,
                                violation_type=rule.violation_type,
                                severity=rule.severity,
                                file_path=file_path,
                                symbol_id=symbol.id,
                                symbol_name=symbol.name,
                                line_start=symbol.line_start,
                                line_end=symbol.line_end,
                                description=f"Function '{symbol.name}' has {function_lines} lines, exceeds limit of {self.max_function_size}",
                                suggestion="Consider breaking this function into smaller, more focused functions",
                                confidence_score=0.9,
                            )
                        )

        # Check class sizes
        elif rule.rule_id == "class_size_violation":
            for symbol in file_analysis.symbols:
                if symbol.symbol_type == SymbolType.CLASS:
                    class_lines = symbol.line_end - symbol.line_start + 1
                    if class_lines > self.max_class_size:
                        violations.append(
                            ViolationInstance(
                                violation_id=self._generate_violation_id(),
                                rule_id=rule.rule_id,
                                violation_type=rule.violation_type,
                                severity=rule.severity,
                                file_path=file_path,
                                symbol_id=symbol.id,
                                symbol_name=symbol.name,
                                line_start=symbol.line_start,
                                line_end=symbol.line_end,
                                description=f"Class '{symbol.name}' has {class_lines} lines, exceeds limit of {self.max_class_size}",
                                suggestion="Consider splitting this class or using composition to reduce size",
                                confidence_score=0.9,
                            )
                        )

        return violations

    def _check_complexity_violations(
        self, rule: ArchitecturalRule, file_path: str, file_analysis: FileAnalysis
    ) -> List[ViolationInstance]:
        """Check for complexity violations"""
        violations = []

        for symbol in file_analysis.symbols:
            if symbol.symbol_type in [SymbolType.FUNCTION, SymbolType.METHOD]:
                complexity = getattr(symbol, "complexity", 1) or 1
                if complexity > self.max_complexity:
                    violations.append(
                        ViolationInstance(
                            violation_id=self._generate_violation_id(),
                            rule_id=rule.rule_id,
                            violation_type=rule.violation_type,
                            severity=rule.severity,
                            file_path=file_path,
                            symbol_id=symbol.id,
                            symbol_name=symbol.name,
                            line_start=symbol.line_start,
                            line_end=symbol.line_end,
                            description=f"Function '{symbol.name}' has complexity {complexity}, exceeds limit of {self.max_complexity}",
                            suggestion="Simplify control flow, extract methods, or use early returns",
                            confidence_score=0.8,
                        )
                    )

        return violations

    def _check_coupling_violations(
        self,
        rule: ArchitecturalRule,
        file_path: str,
        component_metrics: ComponentMetrics,
    ) -> List[ViolationInstance]:
        """Check for coupling violations"""
        violations = []

        total_coupling = (
            component_metrics.dependencies_in + component_metrics.dependencies_out
        )
        if total_coupling > self.max_dependencies:
            violations.append(
                ViolationInstance(
                    violation_id=self._generate_violation_id(),
                    rule_id=rule.rule_id,
                    violation_type=rule.violation_type,
                    severity=rule.severity,
                    file_path=file_path,
                    description=f"Component has {total_coupling} dependencies, exceeds limit of {self.max_dependencies}",
                    suggestion="Reduce dependencies through dependency injection, interfaces, or refactoring",
                    confidence_score=0.7,
                )
            )

        return violations

    async def _check_layer_violations(
        self, rule: ArchitecturalRule, file_path: str, file_analysis: FileAnalysis
    ) -> List[ViolationInstance]:
        """Check for architectural layer violations"""
        violations = []

        current_layer = self._determine_layer(file_path)

        # Check dependencies for layer violations
        for dependency in file_analysis.dependencies:
            target_file = dependency.target_file
            target_layer = self._determine_layer(target_file)

            # Check if this violates layer rules
            if current_layer in rule.layers_from and target_layer in rule.layers_to:
                violations.append(
                    ViolationInstance(
                        violation_id=self._generate_violation_id(),
                        rule_id=rule.rule_id,
                        violation_type=rule.violation_type,
                        severity=rule.severity,
                        file_path=file_path,
                        description=f"Layer violation: {current_layer} accessing {target_layer}",
                        details=f"File in {current_layer} layer should not directly access {target_layer} layer",
                        suggestion="Use dependency inversion or introduce an interface/service layer",
                        confidence_score=rule.confidence_threshold,
                        context={
                            "target_file": target_file,
                            "dependency_type": dependency.dependency_type,
                        },
                    )
                )

        return violations

    def _check_naming_violations(
        self, rule: ArchitecturalRule, file_path: str, file_analysis: FileAnalysis
    ) -> List[ViolationInstance]:
        """Check for naming convention violations"""
        violations = []

        if not rule.pattern:
            return violations

        pattern = re.compile(rule.pattern)

        for symbol in file_analysis.symbols:
            if pattern.search(symbol.name):
                violations.append(
                    ViolationInstance(
                        violation_id=self._generate_violation_id(),
                        rule_id=rule.rule_id,
                        violation_type=rule.violation_type,
                        severity=rule.severity,
                        file_path=file_path,
                        symbol_id=symbol.id,
                        symbol_name=symbol.name,
                        line_start=symbol.line_start,
                        line_end=symbol.line_end,
                        description=f"Naming convention violation: '{symbol.name}' does not follow conventions",
                        suggestion="Follow language-specific naming conventions",
                        confidence_score=rule.confidence_threshold,
                    )
                )

        return violations

    def _check_anti_patterns(
        self,
        rule: ArchitecturalRule,
        file_path: str,
        file_analysis: FileAnalysis,
        component_metrics: ComponentMetrics,
    ) -> List[ViolationInstance]:
        """Check for anti-patterns"""
        violations = []

        if rule.rule_id == "god_class_antipattern":
            for symbol in file_analysis.symbols:
                if symbol.symbol_type == SymbolType.CLASS:
                    class_lines = symbol.line_end - symbol.line_start + 1
                    class_methods = len(
                        [
                            s
                            for s in file_analysis.symbols
                            if s.symbol_type == SymbolType.METHOD
                            and s.line_start >= symbol.line_start
                            and s.line_end <= symbol.line_end
                        ]
                    )

                    # Heuristic for god class: large size + many methods
                    if class_lines > 200 and class_methods > 10:
                        violations.append(
                            ViolationInstance(
                                violation_id=self._generate_violation_id(),
                                rule_id=rule.rule_id,
                                violation_type=rule.violation_type,
                                severity=rule.severity,
                                file_path=file_path,
                                symbol_id=symbol.id,
                                symbol_name=symbol.name,
                                line_start=symbol.line_start,
                                line_end=symbol.line_end,
                                description=f"God class detected: '{symbol.name}' ({class_lines} lines, {class_methods} methods)",
                                suggestion="Split into smaller, single-responsibility classes",
                                confidence_score=0.7,
                                context={
                                    "lines": class_lines,
                                    "methods": class_methods,
                                },
                            )
                        )

        return violations

    async def _detect_circular_dependencies(
        self, file_path: str, file_analysis: FileAnalysis
    ) -> List[ViolationInstance]:
        """Detect circular dependencies"""
        violations = []

        try:
            # Use symbol dependency tracker to detect cycles
            for dependency in file_analysis.dependencies:
                target_file = dependency.target_file

                # Check if target file depends back on this file
                reverse_path = await symbol_dependency_tracker.find_dependency_path(
                    target_file, file_path
                )
                if reverse_path and reverse_path.is_cyclic:
                    violations.append(
                        ViolationInstance(
                            violation_id=self._generate_violation_id(),
                            rule_id="circular_dependency",
                            violation_type=ViolationType.CIRCULAR_DEPENDENCY,
                            severity=ViolationSeverity.ERROR,
                            file_path=file_path,
                            description=f"Circular dependency detected between {file_path} and {target_file}",
                            suggestion="Break the cycle using dependency inversion or interfaces",
                            confidence_score=0.9,
                            context={"cycle_path": reverse_path.path},
                        )
                    )

        except Exception as e:
            logger.error(f"Error detecting circular dependencies: {e}")

        return violations

    async def _count_incoming_dependencies(self, file_path: str) -> int:
        """Count how many files depend on this file"""
        try:
            # This would typically query the graph service
            # For now, return a placeholder
            return 0
        except Exception as e:
            logger.error(f"Error counting incoming dependencies for {file_path}: {e}")
            return 0

    def _generate_summary(
        self,
        violations: List[ViolationInstance],
        component_metrics: List[ComponentMetrics],
    ) -> Dict[str, Any]:
        """Generate summary statistics"""
        summary = {
            "total_violations": len(violations),
            "violations_by_type": defaultdict(int),
            "violations_by_severity": defaultdict(int),
            "components_analyzed": len(component_metrics),
            "most_violated_files": [],
            "quality_indicators": {},
        }

        # Count by type and severity
        for violation in violations:
            summary["violations_by_type"][violation.violation_type] += 1
            summary["violations_by_severity"][violation.severity] += 1

        # Find most violated files
        file_violation_counts = defaultdict(int)
        for violation in violations:
            file_violation_counts[violation.file_path] += 1

        summary["most_violated_files"] = sorted(
            file_violation_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Quality indicators
        if component_metrics:
            avg_complexity = sum(
                m.complexity_metrics.get("average_complexity", 0)
                for m in component_metrics
            ) / len(component_metrics)
            avg_coupling = sum(
                m.dependencies_in + m.dependencies_out for m in component_metrics
            ) / len(component_metrics)
            avg_cohesion = sum(m.cohesion_score for m in component_metrics) / len(
                component_metrics
            )

            summary["quality_indicators"] = {
                "average_complexity": avg_complexity,
                "average_coupling": avg_coupling,
                "average_cohesion": avg_cohesion,
            }

        return summary

    def _calculate_quality_score(
        self, violations: List[ViolationInstance], total_files: int
    ) -> float:
        """Calculate overall quality score"""
        if total_files == 0:
            return 1.0

        # Weight violations by severity
        severity_weights = {
            ViolationSeverity.CRITICAL: 4.0,
            ViolationSeverity.ERROR: 2.0,
            ViolationSeverity.WARNING: 1.0,
            ViolationSeverity.INFO: 0.5,
        }

        weighted_violations = sum(
            severity_weights.get(v.severity, 1.0) for v in violations
        )

        # Calculate score (higher is better)
        violations_per_file = weighted_violations / total_files
        quality_score = max(0.0, 1.0 - (violations_per_file / 10.0))  # Scale to 0-1

        return quality_score

    def _generate_recommendations(
        self, violations: List[ViolationInstance], summary: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on violations"""
        recommendations = []

        # High-level recommendations based on violation patterns
        if summary["violations_by_type"].get(ViolationType.SIZE_VIOLATION, 0) > 5:
            recommendations.append(
                "Consider refactoring large classes and functions into smaller components"
            )

        if summary["violations_by_type"].get(ViolationType.COMPLEXITY_VIOLATION, 0) > 3:
            recommendations.append(
                "Reduce code complexity using early returns, guard clauses, and method extraction"
            )

        if summary["violations_by_type"].get(ViolationType.COUPLING_VIOLATION, 0) > 2:
            recommendations.append(
                "Implement dependency injection and use interfaces to reduce coupling"
            )

        if summary["violations_by_type"].get(ViolationType.LAYER_VIOLATION, 0) > 1:
            recommendations.append(
                "Enforce architectural boundaries with clear layer separation"
            )

        if summary["violations_by_severity"].get(ViolationSeverity.CRITICAL, 0) > 0:
            recommendations.append(
                "Address critical violations immediately as they may impact system stability"
            )

        return recommendations

    def _create_empty_report(self, project_id: str) -> ArchitecturalReport:
        """Create an empty report for error cases"""
        return ArchitecturalReport(
            report_id=self._generate_report_id(),
            project_id=project_id,
            analysis_timestamp=datetime.now(),
            violations=[],
            component_metrics=[],
            summary={"total_violations": 0},
            quality_score=1.0,
        )

    def _remove_violations_for_file(self, file_path: str):
        """Remove all violations for a specific file"""
        self.violations = [v for v in self.violations if v.file_path != file_path]

        # Remove from cache
        to_remove = [
            vid for vid, v in self.violation_cache.items() if v.file_path == file_path
        ]
        for vid in to_remove:
            del self.violation_cache[vid]

    async def _notify_violation_subscribers(
        self, file_path: str, violations: List[ViolationInstance]
    ):
        """Notify subscribers about new violations"""
        try:
            subscribers = self.violation_subscribers.get(file_path, set())
            if subscribers:
                # Here you would send real-time notifications
                logger.debug(
                    f"Notified {len(subscribers)} subscribers about {len(violations)} violations in {file_path}"
                )
        except Exception as e:
            logger.error(f"Error notifying violation subscribers: {e}")

    async def _background_analysis_processor(self):
        """Background task to process pending analysis"""
        try:
            while True:
                if self.pending_analysis:
                    file_path = self.pending_analysis.popleft()
                    await self.analyze_file(file_path)

                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            logger.info("Background analysis processor cancelled")
        except Exception as e:
            logger.error(f"Error in background analysis processor: {e}")

    async def _continuous_monitoring(self):
        """Continuous monitoring task"""
        try:
            while True:
                # Periodic cleanup and maintenance
                await asyncio.sleep(300)  # 5 minutes

                # Clean up old violations
                cutoff_time = datetime.now() - timedelta(days=1)
                self.violations = [
                    v for v in self.violations if v.detected_at > cutoff_time
                ]

                logger.debug("Completed periodic cleanup of architectural violations")

        except asyncio.CancelledError:
            logger.info("Continuous monitoring cancelled")
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")

    def _update_metrics(
        self, violations: List[ViolationInstance], analysis_time_ms: float
    ):
        """Update performance metrics"""
        self.metrics["total_violations"] += len(violations)
        self.metrics["components_analyzed"] += 1

        for violation in violations:
            self.metrics["violations_by_type"][violation.violation_type] += 1
            self.metrics["violations_by_severity"][violation.severity] += 1

        # Update average analysis time
        if self.metrics["analysis_time_ms"] == 0:
            self.metrics["analysis_time_ms"] = analysis_time_ms
        else:
            self.metrics["analysis_time_ms"] = (
                self.metrics["analysis_time_ms"] + analysis_time_ms
            ) / 2

    def _generate_violation_id(self) -> str:
        """Generate unique violation ID"""
        timestamp = int(time.time() * 1000)
        return f"violation_{timestamp}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}"

    def _generate_report_id(self) -> str:
        """Generate unique report ID"""
        timestamp = int(time.time() * 1000)
        return (
            f"report_{timestamp}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}"
        )


# Global instance
architectural_violation_detector = ArchitecturalViolationDetector()
