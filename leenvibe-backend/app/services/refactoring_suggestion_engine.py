"""
Automated Refactoring Suggestion Engine

Analyzes code patterns and suggests intelligent refactoring opportunities
including code smells detection, design pattern recommendations, and automated fixes.
"""

import ast
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
from .project_indexer import project_indexer

logger = logging.getLogger(__name__)


class RefactoringType(str, Enum):
    """Types of refactoring suggestions"""

    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    MOVE_METHOD = "move_method"
    RENAME = "rename"
    INLINE = "inline"
    SIMPLIFY_CONDITIONAL = "simplify_conditional"
    REMOVE_DUPLICATION = "remove_duplication"
    OPTIMIZE_IMPORTS = "optimize_imports"
    REDUCE_COMPLEXITY = "reduce_complexity"
    IMPROVE_NAMING = "improve_naming"
    ADD_TYPE_HINTS = "add_type_hints"
    MODERNIZE_CODE = "modernize_code"


class CodeSmellType(str, Enum):
    """Types of code smells"""

    LONG_METHOD = "long_method"
    LONG_CLASS = "long_class"
    LARGE_PARAMETER_LIST = "large_parameter_list"
    DUPLICATE_CODE = "duplicate_code"
    DEAD_CODE = "dead_code"
    GOD_CLASS = "god_class"
    FEATURE_ENVY = "feature_envy"
    DATA_CLUMPS = "data_clumps"
    PRIMITIVE_OBSESSION = "primitive_obsession"
    SWITCH_STATEMENTS = "switch_statements"
    SPECULATIVE_GENERALITY = "speculative_generality"
    MESSAGE_CHAINS = "message_chains"


class SuggestionPriority(str, Enum):
    """Priority levels for refactoring suggestions"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NICE_TO_HAVE = "nice_to_have"


class SuggestionCategory(str, Enum):
    """Categories of refactoring suggestions"""

    MAINTAINABILITY = "maintainability"
    PERFORMANCE = "performance"
    READABILITY = "readability"
    DESIGN = "design"
    SECURITY = "security"
    MODERNIZATION = "modernization"
    TESTING = "testing"


@dataclass
class CodePattern:
    """Represents a code pattern for analysis"""

    pattern_id: str
    name: str
    description: str
    language: LanguageType
    pattern_type: str  # AST pattern, regex, heuristic
    pattern_data: Any  # Pattern definition
    threshold_values: Dict[str, float] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class CodeSmell:
    """Represents a detected code smell"""

    smell_id: str
    smell_type: CodeSmellType
    symbol_id: str
    file_path: str
    line_start: int
    line_end: int
    severity: float  # 0.0 - 1.0
    description: str
    metrics: Dict[str, float] = field(default_factory=dict)
    related_symbols: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class RefactoringSuggestion:
    """Represents a refactoring suggestion"""

    suggestion_id: str
    refactoring_type: RefactoringType
    priority: SuggestionPriority
    category: SuggestionCategory
    title: str
    description: str
    rationale: str
    target_symbol_id: Optional[str] = None
    target_file_path: Optional[str] = None
    affected_symbols: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    estimated_effort_hours: float = 0.0
    expected_benefits: List[str] = field(default_factory=list)
    implementation_steps: List[str] = field(default_factory=list)
    automated_fix_available: bool = False
    automated_fix_data: Optional[Dict[str, Any]] = None
    code_examples: Dict[str, str] = field(default_factory=dict)  # before/after
    confidence_score: float = 0.0
    related_smells: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RefactoringMetrics:
    """Metrics for refactoring suggestions"""

    total_suggestions: int = 0
    suggestions_by_type: Dict[RefactoringType, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    suggestions_by_priority: Dict[SuggestionPriority, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    suggestions_by_category: Dict[SuggestionCategory, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    code_smells_detected: int = 0
    smells_by_type: Dict[CodeSmellType, int] = field(
        default_factory=lambda: defaultdict(int)
    )
    automated_fixes_available: int = 0
    total_estimated_effort_hours: float = 0.0
    average_confidence_score: float = 0.0


@dataclass
class RefactoringReport:
    """Comprehensive refactoring report"""

    report_id: str
    project_id: str
    analysis_timestamp: datetime
    suggestions: List[RefactoringSuggestion]
    code_smells: List[CodeSmell]
    metrics: RefactoringMetrics
    summary: str
    recommendations: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)


class RefactoringSuggestionEngine:
    """
    Automated Refactoring Suggestion Engine

    Analyzes code patterns, detects code smells, and generates
    intelligent refactoring suggestions with automated fix capabilities.
    """

    def __init__(self):
        # Pattern definitions for analysis
        self.code_patterns: Dict[str, CodePattern] = {}
        self.smell_detectors: Dict[CodeSmellType, Any] = {}

        # Analysis results storage
        self.detected_smells: List[CodeSmell] = []
        self.suggestions: List[RefactoringSuggestion] = []
        self.suggestion_cache: Dict[str, List[RefactoringSuggestion]] = {}

        # Configuration
        self.analysis_config = {
            "max_method_lines": 50,
            "max_class_lines": 500,
            "max_parameters": 5,
            "max_complexity": 10,
            "min_duplication_length": 6,
            "min_confidence_threshold": 0.6,
        }

        # Performance metrics
        self.metrics = RefactoringMetrics()

        # Background processing
        self.analysis_queue: asyncio.Queue = asyncio.Queue()
        self.analysis_task: Optional[asyncio.Task] = None

        # Initialize patterns and detectors
        self._initialize_code_patterns()
        self._initialize_smell_detectors()

    async def initialize(self) -> bool:
        """Initialize the refactoring suggestion engine"""
        try:
            logger.info("Initializing Refactoring Suggestion Engine...")

            # Start background analysis processor
            self.analysis_task = asyncio.create_task(
                self._background_analysis_processor()
            )

            logger.info("Refactoring suggestion engine initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing refactoring suggestion engine: {e}")
            return False

    async def shutdown(self):
        """Shutdown the refactoring suggestion engine"""
        try:
            logger.info("Shutting down refactoring suggestion engine...")

            # Cancel background task
            if self.analysis_task:
                self.analysis_task.cancel()
                try:
                    await self.analysis_task
                except asyncio.CancelledError:
                    pass

            logger.info("Refactoring suggestion engine shutdown complete")

        except Exception as e:
            logger.error(f"Error during refactoring suggestion engine shutdown: {e}")

    async def analyze_project(self, project_id: str) -> RefactoringReport:
        """Analyze entire project for refactoring opportunities"""
        try:
            start_time = time.time()
            logger.info(f"Starting refactoring analysis for project {project_id}")

            # Get project index
            project_index = await project_indexer.get_project_index(project_id)
            if not project_index:
                logger.warning(f"No project index found for {project_id}")
                return self._create_empty_report(project_id)

            # Clear previous results
            self.detected_smells.clear()
            self.suggestions.clear()

            # Analyze each file
            for file_path, file_analysis in project_index.files.items():
                if file_analysis.language in [
                    LanguageType.PYTHON,
                    LanguageType.JAVASCRIPT,
                    LanguageType.TYPESCRIPT,
                ]:
                    await self._analyze_file(file_path, file_analysis)

            # Generate cross-file suggestions
            await self._analyze_cross_file_patterns(project_index)

            # Create report
            report = RefactoringReport(
                report_id=self._generate_report_id(),
                project_id=project_id,
                analysis_timestamp=datetime.now(),
                suggestions=self.suggestions.copy(),
                code_smells=self.detected_smells.copy(),
                metrics=self._calculate_metrics(),
                summary=self._generate_summary(),
            )

            # Generate recommendations
            report.recommendations = self._generate_recommendations(report)
            report.next_steps = self._generate_next_steps(report)

            analysis_time = time.time() - start_time
            logger.info(
                f"Refactoring analysis completed in {analysis_time:.2f}s: "
                f"{len(self.suggestions)} suggestions, {len(self.detected_smells)} smells"
            )

            return report

        except Exception as e:
            logger.error(f"Error analyzing project {project_id}: {e}")
            return self._create_empty_report(project_id)

    async def analyze_file(self, file_path: str) -> List[RefactoringSuggestion]:
        """Analyze single file for refactoring opportunities"""
        try:
            # Get file analysis from AST service
            file_analysis = await ast_service.analyze_file(file_path)
            if not file_analysis:
                return []

            # Clear file-specific results
            file_suggestions = []

            # Analyze file
            suggestions = await self._analyze_file(file_path, file_analysis)
            file_suggestions.extend(suggestions)

            return file_suggestions

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return []

    async def get_suggestions_for_symbol(
        self, symbol_id: str
    ) -> List[RefactoringSuggestion]:
        """Get refactoring suggestions for specific symbol"""
        try:
            return [
                suggestion
                for suggestion in self.suggestions
                if suggestion.target_symbol_id == symbol_id
                or symbol_id in suggestion.affected_symbols
            ]
        except Exception as e:
            logger.error(f"Error getting suggestions for symbol {symbol_id}: {e}")
            return []

    async def generate_automated_fix(
        self, suggestion_id: str
    ) -> Optional[Dict[str, Any]]:
        """Generate automated fix for a suggestion"""
        try:
            suggestion = next(
                (s for s in self.suggestions if s.suggestion_id == suggestion_id), None
            )
            if not suggestion or not suggestion.automated_fix_available:
                return None

            # Generate fix based on refactoring type
            if suggestion.refactoring_type == RefactoringType.OPTIMIZE_IMPORTS:
                return await self._generate_import_optimization_fix(suggestion)
            elif suggestion.refactoring_type == RefactoringType.ADD_TYPE_HINTS:
                return await self._generate_type_hint_fix(suggestion)
            elif suggestion.refactoring_type == RefactoringType.SIMPLIFY_CONDITIONAL:
                return await self._generate_conditional_simplification_fix(suggestion)
            elif suggestion.refactoring_type == RefactoringType.REMOVE_DUPLICATION:
                return await self._generate_duplication_removal_fix(suggestion)

            return suggestion.automated_fix_data

        except Exception as e:
            logger.error(f"Error generating automated fix for {suggestion_id}: {e}")
            return None

    async def _analyze_file(
        self, file_path: str, file_analysis: FileAnalysis
    ) -> List[RefactoringSuggestion]:
        """Analyze a single file for refactoring opportunities"""
        try:
            suggestions = []

            # Detect code smells
            smells = await self._detect_code_smells(file_path, file_analysis)
            self.detected_smells.extend(smells)

            # Generate suggestions based on smells
            for smell in smells:
                smell_suggestions = await self._generate_suggestions_for_smell(
                    smell, file_analysis
                )
                suggestions.extend(smell_suggestions)

            # Analyze individual symbols
            for symbol in file_analysis.symbols:
                symbol_suggestions = await self._analyze_symbol(symbol, file_analysis)
                suggestions.extend(symbol_suggestions)

            # Add to global suggestions
            self.suggestions.extend(suggestions)

            return suggestions

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return []

    async def _detect_code_smells(
        self, file_path: str, file_analysis: FileAnalysis
    ) -> List[CodeSmell]:
        """Detect code smells in a file"""
        try:
            smells = []

            for symbol in file_analysis.symbols:
                # Long method detection
                if symbol.symbol_type == SymbolType.FUNCTION:
                    method_lines = symbol.line_end - symbol.line_start + 1
                    if method_lines > self.analysis_config["max_method_lines"]:
                        smell = CodeSmell(
                            smell_id=self._generate_smell_id(),
                            smell_type=CodeSmellType.LONG_METHOD,
                            symbol_id=symbol.id,
                            file_path=file_path,
                            line_start=symbol.line_start,
                            line_end=symbol.line_end,
                            severity=min(
                                1.0,
                                method_lines
                                / (self.analysis_config["max_method_lines"] * 2),
                            ),
                            description=f"Method has {method_lines} lines (threshold: {self.analysis_config['max_method_lines']})",
                            metrics={"lines": method_lines},
                        )
                        smells.append(smell)

                # Long class detection
                elif symbol.symbol_type == SymbolType.CLASS:
                    class_lines = symbol.line_end - symbol.line_start + 1
                    if class_lines > self.analysis_config["max_class_lines"]:
                        smell = CodeSmell(
                            smell_id=self._generate_smell_id(),
                            smell_type=CodeSmellType.LONG_CLASS,
                            symbol_id=symbol.id,
                            file_path=file_path,
                            line_start=symbol.line_start,
                            line_end=symbol.line_end,
                            severity=min(
                                1.0,
                                class_lines
                                / (self.analysis_config["max_class_lines"] * 2),
                            ),
                            description=f"Class has {class_lines} lines (threshold: {self.analysis_config['max_class_lines']})",
                            metrics={"lines": class_lines},
                        )
                        smells.append(smell)

                # Large parameter list detection
                if hasattr(symbol, "parameters") and symbol.parameters:
                    param_count = len(symbol.parameters)
                    if param_count > self.analysis_config["max_parameters"]:
                        smell = CodeSmell(
                            smell_id=self._generate_smell_id(),
                            smell_type=CodeSmellType.LARGE_PARAMETER_LIST,
                            symbol_id=symbol.id,
                            file_path=file_path,
                            line_start=symbol.line_start,
                            line_end=symbol.line_end,
                            severity=min(
                                1.0,
                                param_count
                                / (self.analysis_config["max_parameters"] * 2),
                            ),
                            description=f"Method has {param_count} parameters (threshold: {self.analysis_config['max_parameters']})",
                            metrics={"parameter_count": param_count},
                        )
                        smells.append(smell)

            return smells

        except Exception as e:
            logger.error(f"Error detecting code smells in {file_path}: {e}")
            return []

    async def _generate_suggestions_for_smell(
        self, smell: CodeSmell, file_analysis: FileAnalysis
    ) -> List[RefactoringSuggestion]:
        """Generate refactoring suggestions for a detected code smell"""
        try:
            suggestions = []

            if smell.smell_type == CodeSmellType.LONG_METHOD:
                suggestion = RefactoringSuggestion(
                    suggestion_id=self._generate_suggestion_id(),
                    refactoring_type=RefactoringType.EXTRACT_METHOD,
                    priority=(
                        SuggestionPriority.HIGH
                        if smell.severity > 0.7
                        else SuggestionPriority.MEDIUM
                    ),
                    category=SuggestionCategory.MAINTAINABILITY,
                    title="Extract method to reduce complexity",
                    description=f"Break down long method into smaller, focused methods",
                    rationale=f"Method has {smell.metrics.get('lines', 0)} lines, making it hard to understand and maintain",
                    target_symbol_id=smell.symbol_id,
                    target_file_path=smell.file_path,
                    estimated_effort_hours=2.0,
                    expected_benefits=[
                        "Improved readability",
                        "Better testability",
                        "Easier maintenance",
                        "Reduced complexity",
                    ],
                    implementation_steps=[
                        "Identify cohesive code blocks",
                        "Extract logical units into separate methods",
                        "Update method calls",
                        "Add appropriate documentation",
                    ],
                    confidence_score=0.8,
                    related_smells=[smell.smell_id],
                )
                suggestions.append(suggestion)

            elif smell.smell_type == CodeSmellType.LONG_CLASS:
                suggestion = RefactoringSuggestion(
                    suggestion_id=self._generate_suggestion_id(),
                    refactoring_type=RefactoringType.EXTRACT_CLASS,
                    priority=SuggestionPriority.HIGH,
                    category=SuggestionCategory.DESIGN,
                    title="Extract class to improve cohesion",
                    description=f"Split large class into smaller, focused classes",
                    rationale=f"Class has {smell.metrics.get('lines', 0)} lines, violating single responsibility principle",
                    target_symbol_id=smell.symbol_id,
                    target_file_path=smell.file_path,
                    estimated_effort_hours=4.0,
                    expected_benefits=[
                        "Better separation of concerns",
                        "Improved testability",
                        "Enhanced reusability",
                        "Clearer responsibilities",
                    ],
                    implementation_steps=[
                        "Identify related methods and data",
                        "Create new class for cohesive functionality",
                        "Move methods and attributes",
                        "Update dependencies and imports",
                    ],
                    confidence_score=0.75,
                    related_smells=[smell.smell_id],
                )
                suggestions.append(suggestion)

            elif smell.smell_type == CodeSmellType.LARGE_PARAMETER_LIST:
                suggestion = RefactoringSuggestion(
                    suggestion_id=self._generate_suggestion_id(),
                    refactoring_type=RefactoringType.EXTRACT_CLASS,
                    priority=SuggestionPriority.MEDIUM,
                    category=SuggestionCategory.DESIGN,
                    title="Introduce parameter object",
                    description=f"Group related parameters into a data class",
                    rationale=f"Method has {smell.metrics.get('parameter_count', 0)} parameters, making it hard to use",
                    target_symbol_id=smell.symbol_id,
                    target_file_path=smell.file_path,
                    estimated_effort_hours=1.5,
                    expected_benefits=[
                        "Simplified method signature",
                        "Better parameter grouping",
                        "Improved maintainability",
                        "Type safety",
                    ],
                    implementation_steps=[
                        "Create data class for related parameters",
                        "Update method signature",
                        "Modify all call sites",
                        "Add validation if needed",
                    ],
                    confidence_score=0.85,
                    related_smells=[smell.smell_id],
                    automated_fix_available=True,
                )
                suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error(
                f"Error generating suggestions for smell {smell.smell_id}: {e}"
            )
            return []

    async def _analyze_symbol(
        self, symbol: Symbol, file_analysis: FileAnalysis
    ) -> List[RefactoringSuggestion]:
        """Analyze individual symbol for refactoring opportunities"""
        try:
            suggestions = []

            # Type hint suggestions for Python
            if file_analysis.language == LanguageType.PYTHON:
                if symbol.symbol_type in [SymbolType.FUNCTION, SymbolType.METHOD]:
                    if not self._has_type_hints(symbol):
                        suggestion = RefactoringSuggestion(
                            suggestion_id=self._generate_suggestion_id(),
                            refactoring_type=RefactoringType.ADD_TYPE_HINTS,
                            priority=SuggestionPriority.MEDIUM,
                            category=SuggestionCategory.MODERNIZATION,
                            title="Add type hints for better code clarity",
                            description="Add type annotations to improve code documentation and IDE support",
                            rationale="Type hints improve code readability and enable better static analysis",
                            target_symbol_id=symbol.id,
                            target_file_path=file_analysis.file_path,
                            estimated_effort_hours=0.5,
                            expected_benefits=[
                                "Better IDE support",
                                "Improved documentation",
                                "Static type checking",
                                "Enhanced readability",
                            ],
                            implementation_steps=[
                                "Analyze parameter and return types",
                                "Add appropriate type annotations",
                                "Import necessary typing modules",
                                "Verify with type checker",
                            ],
                            confidence_score=0.9,
                            automated_fix_available=True,
                        )
                        suggestions.append(suggestion)

            # Naming convention suggestions
            if not self._follows_naming_conventions(symbol, file_analysis.language):
                suggestion = RefactoringSuggestion(
                    suggestion_id=self._generate_suggestion_id(),
                    refactoring_type=RefactoringType.IMPROVE_NAMING,
                    priority=SuggestionPriority.LOW,
                    category=SuggestionCategory.READABILITY,
                    title="Improve naming conventions",
                    description="Rename symbol to follow language conventions",
                    rationale="Consistent naming improves code readability and maintainability",
                    target_symbol_id=symbol.id,
                    target_file_path=file_analysis.file_path,
                    estimated_effort_hours=0.25,
                    expected_benefits=[
                        "Better readability",
                        "Consistent style",
                        "Team standards compliance",
                    ],
                    implementation_steps=[
                        "Choose appropriate name",
                        "Update all references",
                        "Update documentation",
                        "Run tests",
                    ],
                    confidence_score=0.7,
                )
                suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error(f"Error analyzing symbol {symbol.name}: {e}")
            return []

    async def _analyze_cross_file_patterns(self, project_index: ProjectIndex):
        """Analyze patterns across multiple files"""
        try:
            # Detect duplicate code across files
            await self._detect_cross_file_duplication(project_index)

            # Detect import optimization opportunities
            await self._detect_import_optimizations(project_index)

            # Detect architectural improvements
            await self._detect_architectural_improvements(project_index)

        except Exception as e:
            logger.error(f"Error analyzing cross-file patterns: {e}")

    async def _detect_cross_file_duplication(self, project_index: ProjectIndex):
        """Detect duplicate code across files"""
        try:
            # Simple duplicate detection based on similar method signatures
            methods_by_signature = defaultdict(list)

            for file_path, file_analysis in project_index.files.items():
                for symbol in file_analysis.symbols:
                    if symbol.symbol_type in [SymbolType.FUNCTION, SymbolType.METHOD]:
                        if hasattr(symbol, "signature") and symbol.signature:
                            signature_hash = hashlib.md5(
                                symbol.signature.encode()
                            ).hexdigest()
                            methods_by_signature[signature_hash].append(
                                (symbol, file_path)
                            )

            # Generate suggestions for duplicates
            for signature_hash, methods in methods_by_signature.items():
                if len(methods) > 1:
                    suggestion = RefactoringSuggestion(
                        suggestion_id=self._generate_suggestion_id(),
                        refactoring_type=RefactoringType.REMOVE_DUPLICATION,
                        priority=SuggestionPriority.HIGH,
                        category=SuggestionCategory.MAINTAINABILITY,
                        title=f"Remove duplicate methods ({len(methods)} instances)",
                        description="Extract common functionality to reduce code duplication",
                        rationale=f"Found {len(methods)} methods with identical signatures",
                        affected_symbols=[method[0].id for method in methods],
                        affected_files=list(set(method[1] for method in methods)),
                        estimated_effort_hours=2.0 * len(methods),
                        expected_benefits=[
                            "Reduced code duplication",
                            "Easier maintenance",
                            "Single source of truth",
                            "Reduced bugs",
                        ],
                        implementation_steps=[
                            "Identify common functionality",
                            "Create shared utility function",
                            "Replace duplicates with calls",
                            "Update tests",
                        ],
                        confidence_score=0.8,
                    )
                    self.suggestions.append(suggestion)

        except Exception as e:
            logger.error(f"Error detecting cross-file duplication: {e}")

    async def _detect_import_optimizations(self, project_index: ProjectIndex):
        """Detect import optimization opportunities"""
        try:
            for file_path, file_analysis in project_index.files.items():
                # Count import symbols
                import_symbols = [
                    s
                    for s in file_analysis.symbols
                    if s.symbol_type == SymbolType.IMPORT
                ]

                if len(import_symbols) > 10:  # Threshold for too many imports
                    suggestion = RefactoringSuggestion(
                        suggestion_id=self._generate_suggestion_id(),
                        refactoring_type=RefactoringType.OPTIMIZE_IMPORTS,
                        priority=SuggestionPriority.LOW,
                        category=SuggestionCategory.MAINTAINABILITY,
                        title="Optimize imports",
                        description="Remove unused imports and organize import statements",
                        rationale=f"File has {len(import_symbols)} import statements",
                        target_file_path=file_path,
                        estimated_effort_hours=0.25,
                        expected_benefits=[
                            "Cleaner code",
                            "Faster imports",
                            "Better organization",
                        ],
                        implementation_steps=[
                            "Remove unused imports",
                            "Sort import statements",
                            "Group by type",
                            "Run import checker",
                        ],
                        confidence_score=0.9,
                        automated_fix_available=True,
                    )
                    self.suggestions.append(suggestion)

        except Exception as e:
            logger.error(f"Error detecting import optimizations: {e}")

    async def _detect_architectural_improvements(self, project_index: ProjectIndex):
        """Detect architectural improvement opportunities"""
        try:
            # Analyze class relationships using graph service
            if hasattr(graph_service, "analyze_relationships"):
                relationships = await graph_service.analyze_relationships(project_index)

                # Look for tightly coupled classes
                for relationship in relationships.get("high_coupling", []):
                    suggestion = RefactoringSuggestion(
                        suggestion_id=self._generate_suggestion_id(),
                        refactoring_type=RefactoringType.EXTRACT_CLASS,
                        priority=SuggestionPriority.MEDIUM,
                        category=SuggestionCategory.DESIGN,
                        title="Reduce coupling between classes",
                        description="Introduce abstraction to reduce tight coupling",
                        rationale="High coupling makes code harder to maintain and test",
                        affected_symbols=relationship.get("symbols", []),
                        estimated_effort_hours=4.0,
                        expected_benefits=[
                            "Improved modularity",
                            "Better testability",
                            "Reduced dependencies",
                            "Enhanced flexibility",
                        ],
                        implementation_steps=[
                            "Identify interface boundaries",
                            "Create abstraction layer",
                            "Refactor dependencies",
                            "Update tests",
                        ],
                        confidence_score=0.7,
                    )
                    self.suggestions.append(suggestion)

        except Exception as e:
            logger.error(f"Error detecting architectural improvements: {e}")

    def _initialize_code_patterns(self):
        """Initialize code patterns for analysis"""
        try:
            # Long method pattern
            self.code_patterns["long_method"] = CodePattern(
                pattern_id="long_method",
                name="Long Method",
                description="Methods that are too long",
                language=LanguageType.PYTHON,
                pattern_type="heuristic",
                pattern_data={"metric": "line_count", "threshold": 50},
            )

            # Long class pattern
            self.code_patterns["long_class"] = CodePattern(
                pattern_id="long_class",
                name="Long Class",
                description="Classes that are too long",
                language=LanguageType.PYTHON,
                pattern_type="heuristic",
                pattern_data={"metric": "line_count", "threshold": 500},
            )

            logger.debug(f"Initialized {len(self.code_patterns)} code patterns")

        except Exception as e:
            logger.error(f"Error initializing code patterns: {e}")

    def _initialize_smell_detectors(self):
        """Initialize code smell detectors"""
        try:
            # Initialize smell detection functions
            self.smell_detectors[CodeSmellType.LONG_METHOD] = self._detect_long_method
            self.smell_detectors[CodeSmellType.LONG_CLASS] = self._detect_long_class
            self.smell_detectors[CodeSmellType.LARGE_PARAMETER_LIST] = (
                self._detect_large_parameter_list
            )

            logger.debug(f"Initialized {len(self.smell_detectors)} smell detectors")

        except Exception as e:
            logger.error(f"Error initializing smell detectors: {e}")

    def _has_type_hints(self, symbol: Symbol) -> bool:
        """Check if symbol has type hints"""
        # Simplified check - would need more sophisticated analysis
        if hasattr(symbol, "signature") and symbol.signature:
            return "->" in symbol.signature or ":" in symbol.signature
        return False

    def _follows_naming_conventions(
        self, symbol: Symbol, language: LanguageType
    ) -> bool:
        """Check if symbol follows naming conventions"""
        name = symbol.name

        if language == LanguageType.PYTHON:
            if symbol.symbol_type == SymbolType.CLASS:
                return name[0].isupper() and "_" not in name  # PascalCase
            elif symbol.symbol_type in [
                SymbolType.FUNCTION,
                SymbolType.METHOD,
                SymbolType.VARIABLE,
            ]:
                return name.islower() or "_" in name  # snake_case

        return True  # Default to true for unknown patterns

    def _calculate_metrics(self) -> RefactoringMetrics:
        """Calculate refactoring metrics"""
        try:
            metrics = RefactoringMetrics()

            metrics.total_suggestions = len(self.suggestions)
            metrics.code_smells_detected = len(self.detected_smells)
            metrics.automated_fixes_available = len(
                [s for s in self.suggestions if s.automated_fix_available]
            )
            metrics.total_estimated_effort_hours = sum(
                s.estimated_effort_hours for s in self.suggestions
            )

            if self.suggestions:
                metrics.average_confidence_score = sum(
                    s.confidence_score for s in self.suggestions
                ) / len(self.suggestions)

            # Count by type
            for suggestion in self.suggestions:
                metrics.suggestions_by_type[suggestion.refactoring_type] += 1
                metrics.suggestions_by_priority[suggestion.priority] += 1
                metrics.suggestions_by_category[suggestion.category] += 1

            # Count smells by type
            for smell in self.detected_smells:
                metrics.smells_by_type[smell.smell_type] += 1

            return metrics

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return RefactoringMetrics()

    def _generate_summary(self) -> str:
        """Generate analysis summary"""
        try:
            metrics = self._calculate_metrics()

            summary_parts = [
                f"Found {metrics.total_suggestions} refactoring opportunities",
                f"Detected {metrics.code_smells_detected} code smells",
                f"{metrics.automated_fixes_available} automated fixes available",
                f"Estimated total effort: {metrics.total_estimated_effort_hours:.1f} hours",
            ]

            return ". ".join(summary_parts) + "."

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Analysis summary unavailable"

    def _generate_recommendations(self, report: RefactoringReport) -> List[str]:
        """Generate high-level recommendations"""
        try:
            recommendations = []

            # Priority-based recommendations
            high_priority_count = len(
                [s for s in report.suggestions if s.priority == SuggestionPriority.HIGH]
            )
            if high_priority_count > 0:
                recommendations.append(
                    f"Address {high_priority_count} high-priority refactoring opportunities first"
                )

            # Automated fixes
            auto_fix_count = len(
                [s for s in report.suggestions if s.automated_fix_available]
            )
            if auto_fix_count > 0:
                recommendations.append(
                    f"Start with {auto_fix_count} suggestions that have automated fixes"
                )

            # Code smells
            smell_count = len(report.code_smells)
            if smell_count > 10:
                recommendations.append(
                    "Consider establishing coding standards to prevent future code smells"
                )

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    def _generate_next_steps(self, report: RefactoringReport) -> List[str]:
        """Generate next steps"""
        try:
            next_steps = [
                "Review high-priority suggestions with the team",
                "Create refactoring tasks in your project management system",
                "Start with automated fixes to gain quick wins",
                "Establish code review practices to prevent future issues",
                "Schedule regular refactoring sessions",
            ]

            return next_steps

        except Exception as e:
            logger.error(f"Error generating next steps: {e}")
            return []

    async def _generate_import_optimization_fix(
        self, suggestion: RefactoringSuggestion
    ) -> Dict[str, Any]:
        """Generate automated fix for import optimization"""
        return {
            "type": "import_optimization",
            "description": "Remove unused imports and sort remaining ones",
            "actions": [
                {"action": "remove_unused_imports"},
                {"action": "sort_imports", "style": "alphabetical"},
                {
                    "action": "group_imports",
                    "groups": ["stdlib", "third_party", "local"],
                },
            ],
        }

    async def _generate_type_hint_fix(
        self, suggestion: RefactoringSuggestion
    ) -> Dict[str, Any]:
        """Generate automated fix for type hints"""
        return {
            "type": "add_type_hints",
            "description": "Add type annotations based on usage patterns",
            "actions": [
                {"action": "analyze_usage"},
                {"action": "infer_types"},
                {"action": "add_annotations"},
                {"action": "add_imports", "modules": ["typing"]},
            ],
        }

    async def _generate_conditional_simplification_fix(
        self, suggestion: RefactoringSuggestion
    ) -> Dict[str, Any]:
        """Generate automated fix for conditional simplification"""
        return {
            "type": "simplify_conditional",
            "description": "Simplify complex conditional expressions",
            "actions": [
                {"action": "identify_patterns"},
                {"action": "apply_boolean_algebra"},
                {"action": "extract_conditions"},
                {"action": "verify_logic"},
            ],
        }

    async def _generate_duplication_removal_fix(
        self, suggestion: RefactoringSuggestion
    ) -> Dict[str, Any]:
        """Generate automated fix for duplication removal"""
        return {
            "type": "remove_duplication",
            "description": "Extract common code into shared functions",
            "actions": [
                {"action": "identify_common_code"},
                {"action": "create_shared_function"},
                {"action": "replace_duplicates"},
                {"action": "update_imports"},
            ],
        }

    def _create_empty_report(self, project_id: str) -> RefactoringReport:
        """Create empty report for error cases"""
        return RefactoringReport(
            report_id=self._generate_report_id(),
            project_id=project_id,
            analysis_timestamp=datetime.now(),
            suggestions=[],
            code_smells=[],
            metrics=RefactoringMetrics(),
            summary="No analysis performed",
        )

    async def _background_analysis_processor(self):
        """Background processor for queued analyses"""
        try:
            while True:
                # Get next analysis request
                request = await self.analysis_queue.get()

                try:
                    # Process analysis request
                    if request["type"] == "project":
                        await self.analyze_project(request["project_id"])
                    elif request["type"] == "file":
                        await self.analyze_file(request["file_path"])

                except Exception as e:
                    logger.error(f"Error processing analysis request: {e}")

                # Small delay between analyses
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info("Background analysis processor cancelled")
        except Exception as e:
            logger.error(f"Error in background analysis processor: {e}")

    def _generate_suggestion_id(self) -> str:
        """Generate unique suggestion ID"""
        timestamp = int(time.time() * 1000)
        return f"suggestion_{timestamp}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}"

    def _generate_smell_id(self) -> str:
        """Generate unique smell ID"""
        timestamp = int(time.time() * 1000)
        return (
            f"smell_{timestamp}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}"
        )

    def _generate_report_id(self) -> str:
        """Generate unique report ID"""
        timestamp = int(time.time() * 1000)
        return (
            f"report_{timestamp}_{hashlib.md5(str(timestamp).encode()).hexdigest()[:8]}"
        )

    def _detect_long_method(self, symbol: Symbol) -> Optional[CodeSmell]:
        """Detect long method smell"""
        # Implementation would go here
        pass

    def _detect_long_class(self, symbol: Symbol) -> Optional[CodeSmell]:
        """Detect long class smell"""
        # Implementation would go here
        pass

    def _detect_large_parameter_list(self, symbol: Symbol) -> Optional[CodeSmell]:
        """Detect large parameter list smell"""
        # Implementation would go here
        pass

    def get_metrics(self) -> Dict[str, Any]:
        """Get refactoring engine metrics"""
        metrics = self._calculate_metrics()
        return {
            "total_suggestions": metrics.total_suggestions,
            "code_smells_detected": metrics.code_smells_detected,
            "automated_fixes_available": metrics.automated_fixes_available,
            "total_estimated_effort_hours": metrics.total_estimated_effort_hours,
            "average_confidence_score": metrics.average_confidence_score,
            "suggestions_by_type": dict(metrics.suggestions_by_type),
            "suggestions_by_priority": dict(metrics.suggestions_by_priority),
            "suggestions_by_category": dict(metrics.suggestions_by_category),
            "smells_by_type": dict(metrics.smells_by_type),
        }


# Global instance
refactoring_suggestion_engine = RefactoringSuggestionEngine()
