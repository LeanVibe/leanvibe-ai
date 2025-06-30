"""
Intelligent Change Classification Service

Automatically classifies code changes as breaking, non-breaking, or potentially
breaking using pattern analysis, AST comparison, and semantic analysis.
"""

import asyncio
import difflib
import hashlib
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..models.ast_models import (
    LanguageType,
    Symbol,
    SymbolType,
)
from ..models.monitoring_models import ChangeType, FileChange

logger = logging.getLogger(__name__)


class BreakingChangeType(str, Enum):
    """Types of breaking changes"""

    SIGNATURE_CHANGE = "signature_change"
    REMOVAL = "removal"
    VISIBILITY_REDUCTION = "visibility_reduction"
    RETURN_TYPE_CHANGE = "return_type_change"
    PARAMETER_REMOVAL = "parameter_removal"
    PARAMETER_TYPE_CHANGE = "parameter_type_change"
    INHERITANCE_CHANGE = "inheritance_change"
    INTERFACE_CHANGE = "interface_change"
    EXCEPTION_CHANGE = "exception_change"
    BEHAVIOR_CHANGE = "behavior_change"
    API_CONTRACT_CHANGE = "api_contract_change"


class ChangeCategory(str, Enum):
    """Categories of changes"""

    API_CHANGE = "api_change"
    IMPLEMENTATION_CHANGE = "implementation_change"
    STRUCTURAL_CHANGE = "structural_change"
    DOCUMENTATION_CHANGE = "documentation_change"
    TEST_CHANGE = "test_change"
    BUILD_CHANGE = "build_change"
    CONFIGURATION_CHANGE = "configuration_change"


class ChangeRisk(str, Enum):
    """Risk levels for changes"""

    SAFE = "safe"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    BREAKING = "breaking"


class CompatibilityLevel(str, Enum):
    """Compatibility levels"""

    BACKWARD_COMPATIBLE = "backward_compatible"
    FORWARD_COMPATIBLE = "forward_compatible"
    COMPATIBLE = "compatible"
    POTENTIALLY_BREAKING = "potentially_breaking"
    BREAKING = "breaking"
    UNKNOWN = "unknown"


@dataclass
class ChangePattern:
    """Pattern for detecting specific change types"""

    pattern_id: str
    name: str
    description: str
    language: Optional[LanguageType] = None
    file_patterns: List[str] = field(default_factory=list)
    ast_patterns: List[str] = field(default_factory=list)
    regex_patterns: List[str] = field(default_factory=list)
    breaking_indicators: List[str] = field(default_factory=list)
    safe_indicators: List[str] = field(default_factory=list)
    weight: float = 1.0
    confidence_threshold: float = 0.7


@dataclass
class ChangeSignature:
    """Signature of a specific change"""

    symbol_id: Optional[str] = None
    symbol_name: Optional[str] = None
    symbol_type: Optional[SymbolType] = None
    old_signature: Optional[str] = None
    new_signature: Optional[str] = None
    visibility_old: Optional[str] = None
    visibility_new: Optional[str] = None
    parameters_old: List[str] = field(default_factory=list)
    parameters_new: List[str] = field(default_factory=list)
    return_type_old: Optional[str] = None
    return_type_new: Optional[str] = None
    inheritance_old: List[str] = field(default_factory=list)
    inheritance_new: List[str] = field(default_factory=list)


@dataclass
class ChangeClassification:
    """Classification result for a change"""

    change_id: str
    file_path: str
    change_type: ChangeType
    category: ChangeCategory
    risk_level: ChangeRisk
    compatibility: CompatibilityLevel
    breaking_changes: List[BreakingChangeType] = field(default_factory=list)
    confidence_score: float = 0.0
    reasons: List[str] = field(default_factory=list)
    affected_symbols: List[str] = field(default_factory=list)
    migration_suggestions: List[str] = field(default_factory=list)
    analysis_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ClassificationRule:
    """Rule for classifying changes"""

    rule_id: str
    name: str
    description: str
    conditions: List[str]  # Condition expressions
    classification: ChangeRisk
    breaking_types: List[BreakingChangeType] = field(default_factory=list)
    confidence: float = 0.8
    priority: int = 1  # Higher number = higher priority


@dataclass
class ChangeMetrics:
    """Metrics about changes"""

    total_changes: int = 0
    breaking_changes: int = 0
    safe_changes: int = 0
    uncertain_changes: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0


class ChangeClassifier:
    """
    Intelligent Change Classification Service

    Automatically classifies code changes as breaking or non-breaking
    using pattern analysis, AST comparison, and semantic heuristics.
    """

    def __init__(self):
        # Pattern and rule storage
        self.patterns: Dict[str, ChangePattern] = {}
        self.rules: List[ClassificationRule] = []
        self.language_analyzers: Dict[LanguageType, Any] = {}

        # Classification cache and history
        self.classifications: List[ChangeClassification] = []
        self.classification_cache: Dict[str, ChangeClassification] = {}
        self.training_data: List[Tuple[FileChange, ChangeClassification]] = []

        # Performance metrics
        self.metrics = ChangeMetrics()

        # Configuration
        self.confidence_threshold = 0.7
        self.breaking_change_threshold = 0.8
        self.max_cache_size = 1000

        # Initialize patterns and rules
        self._initialize_built_in_patterns()
        self._initialize_classification_rules()

    async def initialize(self) -> bool:
        """Initialize the change classifier"""
        try:
            logger.info("Initializing Change Classifier...")

            # Load custom patterns and rules if they exist
            await self._load_custom_patterns()
            await self._load_classification_history()

            logger.info(
                f"Change classifier initialized with {len(self.patterns)} patterns and {len(self.rules)} rules"
            )
            return True

        except Exception as e:
            logger.error(f"Error initializing change classifier: {e}")
            return False

    async def classify_change(
        self,
        file_change: FileChange,
        old_content: Optional[str] = None,
        new_content: Optional[str] = None,
    ) -> ChangeClassification:
        """Classify a file change as breaking or non-breaking"""
        try:
            # Check cache
            cache_key = self._generate_cache_key(file_change)
            if cache_key in self.classification_cache:
                return self.classification_cache[cache_key]

            # Create base classification
            classification = ChangeClassification(
                change_id=file_change.id,
                file_path=file_change.file_path,
                change_type=file_change.change_type,
                category=self._determine_category(file_change),
                risk_level=ChangeRisk.MEDIUM_RISK,
                compatibility=CompatibilityLevel.UNKNOWN,
            )

            # Skip non-code files
            if not self._is_code_file(file_change.file_path):
                classification.category = self._get_non_code_category(
                    file_change.file_path
                )
                classification.risk_level = ChangeRisk.SAFE
                classification.compatibility = CompatibilityLevel.COMPATIBLE
                classification.confidence_score = 0.9
                classification.reasons.append("Non-code file")
                return classification

            # Analyze based on change type
            if file_change.change_type == ChangeType.DELETED:
                await self._analyze_deletion(classification, file_change)
            elif file_change.change_type == ChangeType.CREATED:
                await self._analyze_creation(classification, file_change, new_content)
            elif file_change.change_type == ChangeType.MODIFIED:
                await self._analyze_modification(
                    classification, file_change, old_content, new_content
                )
            elif file_change.change_type == ChangeType.MOVED:
                await self._analyze_move(classification, file_change)

            # Apply classification rules
            await self._apply_classification_rules(classification, file_change)

            # Calculate final confidence and compatibility
            self._finalize_classification(classification)

            # Cache result
            self.classification_cache[cache_key] = classification
            self.classifications.append(classification)

            # Update metrics
            self._update_metrics(classification)

            logger.debug(
                f"Classified change {file_change.file_path}: {classification.risk_level} "
                f"(confidence: {classification.confidence_score:.2f})"
            )

            return classification

        except Exception as e:
            logger.error(f"Error classifying change: {e}")
            return ChangeClassification(
                change_id=file_change.id,
                file_path=file_change.file_path,
                change_type=file_change.change_type,
                category=ChangeCategory.IMPLEMENTATION_CHANGE,
                risk_level=ChangeRisk.MEDIUM_RISK,
                compatibility=CompatibilityLevel.UNKNOWN,
                reasons=[f"Classification error: {str(e)}"],
            )

    async def classify_batch_changes(
        self, changes: List[FileChange], content_provider: Optional[Any] = None
    ) -> List[ChangeClassification]:
        """Classify multiple changes in batch"""
        try:
            classifications = []

            # Process changes in parallel for better performance
            semaphore = asyncio.Semaphore(10)  # Limit concurrent classifications

            async def classify_single(change):
                async with semaphore:
                    old_content = None
                    new_content = None

                    if content_provider:
                        old_content = await content_provider.get_old_content(
                            change.file_path
                        )
                        new_content = await content_provider.get_new_content(
                            change.file_path
                        )

                    return await self.classify_change(change, old_content, new_content)

            # Create tasks for all changes
            tasks = [classify_single(change) for change in changes]
            classifications = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions and log errors
            valid_classifications = []
            for i, result in enumerate(classifications):
                if isinstance(result, Exception):
                    logger.error(
                        f"Error classifying change {changes[i].file_path}: {result}"
                    )
                    # Create error classification
                    error_classification = ChangeClassification(
                        change_id=changes[i].id,
                        file_path=changes[i].file_path,
                        change_type=changes[i].change_type,
                        category=ChangeCategory.IMPLEMENTATION_CHANGE,
                        risk_level=ChangeRisk.MEDIUM_RISK,
                        compatibility=CompatibilityLevel.UNKNOWN,
                        reasons=[f"Classification error: {str(result)}"],
                    )
                    valid_classifications.append(error_classification)
                else:
                    valid_classifications.append(result)

            return valid_classifications

        except Exception as e:
            logger.error(f"Error in batch classification: {e}")
            return []

    async def analyze_breaking_changes(
        self, old_symbol: Symbol, new_symbol: Symbol
    ) -> List[BreakingChangeType]:
        """Analyze specific breaking changes between symbol versions"""
        try:
            breaking_changes = []

            # Check signature changes
            if old_symbol.signature != new_symbol.signature:
                breaking_changes.append(BreakingChangeType.SIGNATURE_CHANGE)

            # Check visibility changes
            old_visibility = getattr(old_symbol, "visibility", "public")
            new_visibility = getattr(new_symbol, "visibility", "public")
            if self._is_visibility_reduction(old_visibility, new_visibility):
                breaking_changes.append(BreakingChangeType.VISIBILITY_REDUCTION)

            # Check return type changes
            old_return = getattr(old_symbol, "return_type", None)
            new_return = getattr(new_symbol, "return_type", None)
            if old_return != new_return and old_return and new_return:
                breaking_changes.append(BreakingChangeType.RETURN_TYPE_CHANGE)

            # Check parameter changes
            old_params = getattr(old_symbol, "parameters", [])
            new_params = getattr(new_symbol, "parameters", [])

            if len(new_params) < len(old_params):
                breaking_changes.append(BreakingChangeType.PARAMETER_REMOVAL)
            elif old_params != new_params:
                # More detailed parameter analysis
                if self._has_parameter_type_changes(old_params, new_params):
                    breaking_changes.append(BreakingChangeType.PARAMETER_TYPE_CHANGE)

            return breaking_changes

        except Exception as e:
            logger.error(f"Error analyzing breaking changes: {e}")
            return []

    def get_classification_summary(
        self, classifications: List[ChangeClassification]
    ) -> Dict[str, Any]:
        """Get summary statistics for classifications"""
        try:
            if not classifications:
                return {
                    "total_changes": 0,
                    "breaking_changes": 0,
                    "safe_changes": 0,
                    "risk_distribution": {},
                    "category_distribution": {},
                    "average_confidence": 0.0,
                }

            # Count by risk level
            risk_counts = defaultdict(int)
            category_counts = defaultdict(int)
            confidence_scores = []

            for classification in classifications:
                risk_counts[classification.risk_level] += 1
                category_counts[classification.category] += 1
                confidence_scores.append(classification.confidence_score)

            # Calculate breaking vs safe
            breaking_count = (
                risk_counts[ChangeRisk.BREAKING] + risk_counts[ChangeRisk.HIGH_RISK]
            )
            safe_count = risk_counts[ChangeRisk.SAFE] + risk_counts[ChangeRisk.LOW_RISK]

            return {
                "total_changes": len(classifications),
                "breaking_changes": breaking_count,
                "safe_changes": safe_count,
                "uncertain_changes": risk_counts[ChangeRisk.MEDIUM_RISK],
                "risk_distribution": dict(risk_counts),
                "category_distribution": dict(category_counts),
                "average_confidence": (
                    sum(confidence_scores) / len(confidence_scores)
                    if confidence_scores
                    else 0.0
                ),
                "high_confidence_changes": len(
                    [c for c in classifications if c.confidence_score > 0.8]
                ),
                "low_confidence_changes": len(
                    [c for c in classifications if c.confidence_score < 0.5]
                ),
            }

        except Exception as e:
            logger.error(f"Error generating classification summary: {e}")
            return {}

    def _initialize_built_in_patterns(self):
        """Initialize built-in change patterns"""
        try:
            # API signature change patterns
            self.patterns["signature_change"] = ChangePattern(
                pattern_id="signature_change",
                name="Function/Method Signature Change",
                description="Changes to function or method signatures",
                regex_patterns=[
                    r"def\s+(\w+)\s*\([^)]*\).*?:",  # Python function
                    r"function\s+(\w+)\s*\([^)]*\)",  # JavaScript function
                    r"(\w+)\s*\([^)]*\)\s*{",  # C-style function
                ],
                breaking_indicators=["parameter removal", "return type change"],
                weight=2.0,
            )

            # Class definition changes
            self.patterns["class_change"] = ChangePattern(
                pattern_id="class_change",
                name="Class Definition Change",
                description="Changes to class definitions and inheritance",
                regex_patterns=[
                    r"class\s+(\w+)(?:\([^)]*\))?:",  # Python class
                    r"class\s+(\w+)(?:\s+extends\s+\w+)?",  # JavaScript/Java class
                ],
                breaking_indicators=["inheritance change", "interface change"],
                weight=1.8,
            )

            # Public API changes
            self.patterns["public_api"] = ChangePattern(
                pattern_id="public_api",
                name="Public API Change",
                description="Changes to public interfaces and APIs",
                regex_patterns=[
                    r"public\s+",
                    r"export\s+",
                    r"__all__\s*=",
                ],
                breaking_indicators=["visibility reduction", "removal"],
                weight=2.5,
            )

            # Import/export changes
            self.patterns["import_change"] = ChangePattern(
                pattern_id="import_change",
                name="Import/Export Change",
                description="Changes to imports and exports",
                regex_patterns=[
                    r"import\s+",
                    r"from\s+\w+\s+import",
                    r"export\s+",
                    r"module\.exports",
                ],
                safe_indicators=["new import", "additional export"],
                weight=1.2,
            )

            logger.debug(f"Initialized {len(self.patterns)} built-in patterns")

        except Exception as e:
            logger.error(f"Error initializing patterns: {e}")

    def _initialize_classification_rules(self):
        """Initialize classification rules"""
        try:
            # High-risk rules
            self.rules.extend(
                [
                    ClassificationRule(
                        rule_id="public_function_removal",
                        name="Public Function Removal",
                        description="Removal of public functions or methods",
                        conditions=[
                            "change_type == DELETED",
                            "symbol_type in [FUNCTION, METHOD]",
                            "visibility == public",
                        ],
                        classification=ChangeRisk.BREAKING,
                        breaking_types=[BreakingChangeType.REMOVAL],
                        confidence=0.95,
                        priority=10,
                    ),
                    ClassificationRule(
                        rule_id="signature_parameter_removal",
                        name="Parameter Removal",
                        description="Removal of required parameters",
                        conditions=[
                            "change_type == MODIFIED",
                            "parameter_count_decreased",
                            "no_default_values_added",
                        ],
                        classification=ChangeRisk.BREAKING,
                        breaking_types=[BreakingChangeType.PARAMETER_REMOVAL],
                        confidence=0.9,
                        priority=9,
                    ),
                    ClassificationRule(
                        rule_id="return_type_change",
                        name="Return Type Change",
                        description="Changes to function return types",
                        conditions=[
                            "change_type == MODIFIED",
                            "return_type_changed",
                            "not_compatible_types",
                        ],
                        classification=ChangeRisk.BREAKING,
                        breaking_types=[BreakingChangeType.RETURN_TYPE_CHANGE],
                        confidence=0.85,
                        priority=8,
                    ),
                ]
            )

            # Medium-risk rules
            self.rules.extend(
                [
                    ClassificationRule(
                        rule_id="parameter_type_change",
                        name="Parameter Type Change",
                        description="Changes to parameter types",
                        conditions=[
                            "change_type == MODIFIED",
                            "parameter_types_changed",
                        ],
                        classification=ChangeRisk.HIGH_RISK,
                        breaking_types=[BreakingChangeType.PARAMETER_TYPE_CHANGE],
                        confidence=0.75,
                        priority=7,
                    ),
                    ClassificationRule(
                        rule_id="visibility_reduction",
                        name="Visibility Reduction",
                        description="Reducing visibility of public members",
                        conditions=["change_type == MODIFIED", "visibility_reduced"],
                        classification=ChangeRisk.HIGH_RISK,
                        breaking_types=[BreakingChangeType.VISIBILITY_REDUCTION],
                        confidence=0.8,
                        priority=6,
                    ),
                ]
            )

            # Safe change rules
            self.rules.extend(
                [
                    ClassificationRule(
                        rule_id="implementation_only",
                        name="Implementation Only Change",
                        description="Changes that only affect implementation",
                        conditions=[
                            "change_type == MODIFIED",
                            "no_signature_changes",
                            "no_public_api_changes",
                        ],
                        classification=ChangeRisk.SAFE,
                        confidence=0.8,
                        priority=3,
                    ),
                    ClassificationRule(
                        rule_id="test_file_change",
                        name="Test File Change",
                        description="Changes to test files",
                        conditions=["file_path matches test patterns"],
                        classification=ChangeRisk.SAFE,
                        confidence=0.9,
                        priority=5,
                    ),
                    ClassificationRule(
                        rule_id="documentation_change",
                        name="Documentation Change",
                        description="Changes to documentation files",
                        conditions=["file_path matches doc patterns"],
                        classification=ChangeRisk.SAFE,
                        confidence=0.95,
                        priority=4,
                    ),
                ]
            )

            # Sort rules by priority (highest first)
            self.rules.sort(key=lambda r: r.priority, reverse=True)

            logger.debug(f"Initialized {len(self.rules)} classification rules")

        except Exception as e:
            logger.error(f"Error initializing rules: {e}")

    def _determine_category(self, file_change: FileChange) -> ChangeCategory:
        """Determine the category of change"""
        file_path = file_change.file_path.lower()

        # Documentation changes
        if any(
            pattern in file_path
            for pattern in [".md", ".rst", ".txt", "readme", "changelog", "docs/"]
        ):
            return ChangeCategory.DOCUMENTATION_CHANGE

        # Build/config changes (check before test patterns to avoid conflicts)
        if any(
            pattern in file_path
            for pattern in [
                "package.json",
                "pyproject.toml",
                "cargo.toml",
                "makefile",
                "dockerfile",
                ".yml",
                ".yaml",
                ".json",
                ".toml",
                ".ini",
                ".cfg",
                ".config",
            ]
        ):
            return ChangeCategory.BUILD_CHANGE

        # Test changes (after config checks)
        if any(
            pattern in file_path
            for pattern in ["test", "spec", "__test__", ".test.", ".spec."]
        ):
            return ChangeCategory.TEST_CHANGE

        # API changes (public interfaces)
        if any(pattern in file_path for pattern in ["api/", "interface/", "public/"]):
            return ChangeCategory.API_CHANGE

        # Default to implementation change
        return ChangeCategory.IMPLEMENTATION_CHANGE

    def _is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file"""
        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".swift",
            ".go",
            ".rs",
        }
        return Path(file_path).suffix.lower() in code_extensions

    def _get_non_code_category(self, file_path: str) -> ChangeCategory:
        """Get category for non-code files"""
        file_path_lower = file_path.lower()

        if any(ext in file_path_lower for ext in [".md", ".rst", ".txt"]):
            return ChangeCategory.DOCUMENTATION_CHANGE
        elif any(
            pattern in file_path_lower
            for pattern in [
                "package.json",
                "pyproject.toml",
                "cargo.toml",
                "makefile",
                "dockerfile",
                ".yml",
                ".yaml",
                ".json",
                ".toml",
                ".ini",
                ".cfg",
                ".config",
            ]
        ):
            return ChangeCategory.BUILD_CHANGE
        else:
            return ChangeCategory.CONFIGURATION_CHANGE

    async def _analyze_deletion(
        self, classification: ChangeClassification, file_change: FileChange
    ):
        """Analyze file deletion"""
        classification.risk_level = ChangeRisk.HIGH_RISK
        classification.compatibility = CompatibilityLevel.POTENTIALLY_BREAKING
        classification.reasons.append("File deletion")

        # Check if it's a public API file
        if (
            "api" in file_change.file_path.lower()
            or "public" in file_change.file_path.lower()
        ):
            classification.risk_level = ChangeRisk.BREAKING
            classification.compatibility = CompatibilityLevel.BREAKING
            classification.breaking_changes.append(BreakingChangeType.REMOVAL)
            classification.reasons.append("Public API file deletion")

    async def _analyze_creation(
        self,
        classification: ChangeClassification,
        file_change: FileChange,
        content: Optional[str],
    ):
        """Analyze file creation"""
        classification.risk_level = ChangeRisk.SAFE
        classification.compatibility = CompatibilityLevel.BACKWARD_COMPATIBLE
        classification.reasons.append("New file creation")
        classification.confidence_score = 0.9

    async def _analyze_modification(
        self,
        classification: ChangeClassification,
        file_change: FileChange,
        old_content: Optional[str],
        new_content: Optional[str],
    ):
        """Analyze file modification"""
        # Default to medium risk for modifications
        classification.risk_level = ChangeRisk.MEDIUM_RISK
        classification.compatibility = CompatibilityLevel.POTENTIALLY_BREAKING

        if old_content and new_content:
            # Analyze content changes
            await self._analyze_content_changes(
                classification, old_content, new_content
            )

        # Check file type specific patterns
        await self._apply_pattern_analysis(classification, file_change)

    async def _analyze_move(
        self, classification: ChangeClassification, file_change: FileChange
    ):
        """Analyze file move/rename"""
        classification.risk_level = ChangeRisk.MEDIUM_RISK
        classification.compatibility = CompatibilityLevel.POTENTIALLY_BREAKING
        classification.reasons.append("File moved/renamed")

        # Moving public API files is more risky
        if "api" in file_change.file_path.lower():
            classification.risk_level = ChangeRisk.HIGH_RISK
            classification.breaking_changes.append(
                BreakingChangeType.API_CONTRACT_CHANGE
            )

    async def _analyze_content_changes(
        self, classification: ChangeClassification, old_content: str, new_content: str
    ):
        """Analyze changes in file content"""
        try:
            # Calculate diff
            diff_lines = list(
                difflib.unified_diff(
                    old_content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    lineterm="",
                )
            )

            removed_lines = [
                line[1:]
                for line in diff_lines
                if line.startswith("-") and not line.startswith("---")
            ]
            added_lines = [
                line[1:]
                for line in diff_lines
                if line.startswith("+") and not line.startswith("+++")
            ]

            # Analyze removed content for breaking changes
            for line in removed_lines:
                if self._is_public_api_line(line):
                    classification.risk_level = ChangeRisk.HIGH_RISK
                    classification.breaking_changes.append(
                        BreakingChangeType.API_CONTRACT_CHANGE
                    )
                    classification.reasons.append("Public API removal detected")

                if self._is_function_signature_line(line):
                    classification.risk_level = ChangeRisk.HIGH_RISK
                    classification.breaking_changes.append(
                        BreakingChangeType.SIGNATURE_CHANGE
                    )
                    classification.reasons.append("Function signature removal")

            # Calculate change magnitude
            total_lines = len(old_content.splitlines())
            changed_lines = len(removed_lines) + len(added_lines)

            if total_lines > 0:
                change_ratio = changed_lines / total_lines
                if change_ratio > 0.5:
                    classification.reasons.append("Large-scale changes detected")
                    if classification.risk_level == ChangeRisk.MEDIUM_RISK:
                        classification.risk_level = ChangeRisk.HIGH_RISK

        except Exception as e:
            logger.error(f"Error analyzing content changes: {e}")

    async def _apply_pattern_analysis(
        self, classification: ChangeClassification, file_change: FileChange
    ):
        """Apply pattern-based analysis"""
        for pattern in self.patterns.values():
            if self._pattern_matches_file(pattern, file_change.file_path):
                # Pattern matching logic would go here
                # This is a simplified implementation
                if pattern.breaking_indicators:
                    classification.reasons.append(f"Pattern match: {pattern.name}")

    async def _apply_classification_rules(
        self, classification: ChangeClassification, file_change: FileChange
    ):
        """Apply classification rules"""
        try:
            for rule in self.rules:
                if self._rule_applies(rule, classification, file_change):
                    # Apply rule
                    if rule.classification == ChangeRisk.BREAKING:
                        classification.risk_level = ChangeRisk.BREAKING
                        classification.compatibility = CompatibilityLevel.BREAKING
                    elif (
                        rule.classification == ChangeRisk.HIGH_RISK
                        and classification.risk_level != ChangeRisk.BREAKING
                    ):
                        classification.risk_level = ChangeRisk.HIGH_RISK
                    elif (
                        rule.classification == ChangeRisk.SAFE
                        and classification.risk_level == ChangeRisk.MEDIUM_RISK
                    ):
                        classification.risk_level = ChangeRisk.SAFE
                        classification.compatibility = CompatibilityLevel.COMPATIBLE

                    classification.breaking_changes.extend(rule.breaking_types)
                    classification.reasons.append(f"Rule applied: {rule.name}")
                    classification.confidence_score = max(
                        classification.confidence_score, rule.confidence
                    )

                    # High priority rules can stop further processing
                    if rule.priority >= 9:
                        break

        except Exception as e:
            logger.error(f"Error applying classification rules: {e}")

    def _rule_applies(
        self,
        rule: ClassificationRule,
        classification: ChangeClassification,
        file_change: FileChange,
    ) -> bool:
        """Check if a rule applies to the given change"""
        try:
            # Simple condition evaluation
            for condition in rule.conditions:
                if not self._evaluate_condition(condition, classification, file_change):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
            return False

    def _evaluate_condition(
        self,
        condition: str,
        classification: ChangeClassification,
        file_change: FileChange,
    ) -> bool:
        """Evaluate a single condition"""
        # Simplified condition evaluation
        if "change_type == DELETED" in condition:
            return file_change.change_type == ChangeType.DELETED
        elif "change_type == MODIFIED" in condition:
            return file_change.change_type == ChangeType.MODIFIED
        elif "test patterns" in condition:
            return "test" in file_change.file_path.lower()
        elif "doc patterns" in condition:
            return any(
                ext in file_change.file_path.lower() for ext in [".md", ".rst", "doc"]
            )

        return False

    def _finalize_classification(self, classification: ChangeClassification):
        """Finalize classification with confidence and compatibility"""
        # Set default confidence if not set
        if classification.confidence_score == 0.0:
            if classification.risk_level in [ChangeRisk.SAFE, ChangeRisk.BREAKING]:
                classification.confidence_score = 0.8
            else:
                classification.confidence_score = 0.6

        # Set compatibility based on risk level
        if classification.compatibility == CompatibilityLevel.UNKNOWN:
            if classification.risk_level == ChangeRisk.BREAKING:
                classification.compatibility = CompatibilityLevel.BREAKING
            elif classification.risk_level == ChangeRisk.SAFE:
                classification.compatibility = CompatibilityLevel.COMPATIBLE
            else:
                classification.compatibility = CompatibilityLevel.POTENTIALLY_BREAKING

        # Generate migration suggestions
        if classification.breaking_changes:
            classification.migration_suggestions = self._generate_migration_suggestions(
                classification
            )

    def _generate_migration_suggestions(
        self, classification: ChangeClassification
    ) -> List[str]:
        """Generate migration suggestions for breaking changes"""
        suggestions = []

        for breaking_type in classification.breaking_changes:
            if breaking_type == BreakingChangeType.SIGNATURE_CHANGE:
                suggestions.append("Update function calls to match new signature")
                suggestions.append("Add parameter validation for new parameters")
            elif breaking_type == BreakingChangeType.REMOVAL:
                suggestions.append("Find alternative implementations")
                suggestions.append("Update imports and references")
            elif breaking_type == BreakingChangeType.VISIBILITY_REDUCTION:
                suggestions.append("Use public alternatives if available")
                suggestions.append("Consider refactoring to use public APIs")

        return suggestions

    def _is_public_api_line(self, line: str) -> bool:
        """Check if line contains public API elements"""
        line = line.strip()
        return any(
            keyword in line for keyword in ["def ", "class ", "export ", "public "]
        )

    def _is_function_signature_line(self, line: str) -> bool:
        """Check if line is a function signature"""
        line = line.strip()
        return bool(
            re.match(r"def\s+\w+\s*\(|function\s+\w+\s*\(|\w+\s*\([^)]*\)\s*{", line)
        )

    def _pattern_matches_file(self, pattern: ChangePattern, file_path: str) -> bool:
        """Check if pattern matches file"""
        if pattern.file_patterns:
            for file_pattern in pattern.file_patterns:
                if re.search(file_pattern, file_path):
                    return True
        return True  # Default to match if no file patterns

    def _is_visibility_reduction(
        self, old_visibility: str, new_visibility: str
    ) -> bool:
        """Check if visibility is being reduced"""
        visibility_levels = {"public": 3, "protected": 2, "private": 1}
        old_level = visibility_levels.get(old_visibility, 3)
        new_level = visibility_levels.get(new_visibility, 3)
        return new_level < old_level

    def _has_parameter_type_changes(
        self, old_params: List[str], new_params: List[str]
    ) -> bool:
        """Check if parameter types have changed"""
        # Simplified check - would need more sophisticated analysis
        return old_params != new_params and len(old_params) == len(new_params)

    def _generate_cache_key(self, file_change: FileChange) -> str:
        """Generate cache key for file change"""
        key_data = f"{file_change.file_path}:{file_change.change_type}:{file_change.id}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _update_metrics(self, classification: ChangeClassification):
        """Update performance metrics"""
        self.metrics.total_changes += 1

        if classification.risk_level == ChangeRisk.BREAKING:
            self.metrics.breaking_changes += 1
        elif classification.risk_level == ChangeRisk.SAFE:
            self.metrics.safe_changes += 1
        else:
            self.metrics.uncertain_changes += 1

    async def _load_custom_patterns(self):
        """Load custom patterns from configuration"""
        # Placeholder for loading custom patterns
        pass

    async def _load_classification_history(self):
        """Load previous classification history"""
        # Placeholder for loading classification history
        pass

    def get_metrics(self) -> Dict[str, Any]:
        """Get classifier metrics"""
        return {
            "total_changes": self.metrics.total_changes,
            "breaking_changes": self.metrics.breaking_changes,
            "safe_changes": self.metrics.safe_changes,
            "uncertain_changes": self.metrics.uncertain_changes,
            "accuracy": self.metrics.accuracy,
            "patterns_loaded": len(self.patterns),
            "rules_loaded": len(self.rules),
            "cache_size": len(self.classification_cache),
            "confidence_threshold": self.confidence_threshold,
        }


# Global instance
change_classifier = ChangeClassifier()
