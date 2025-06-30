"""
Architectural Rule Management Service

Manages architectural rules, patterns, and layer definitions for violation detection.
Extracted from architectural_violation_detector.py to improve modularity.
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Set

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

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ArchitecturalLayer(str, Enum):
    """Architectural layers for organizing code"""

    PRESENTATION = "presentation"
    APPLICATION = "application"
    DOMAIN = "domain"
    INFRASTRUCTURE = "infrastructure"
    SHARED = "shared"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


@dataclass
class ArchitecturalRule:
    """Represents an architectural rule to be enforced"""

    id: str
    name: str
    description: str
    violation_type: ViolationType
    severity: ViolationSeverity
    pattern: str  # Regex or pattern to match
    allowed_layers: List[ArchitecturalLayer] = None
    forbidden_layers: List[ArchitecturalLayer] = None
    max_dependencies: int = None
    max_complexity: int = None
    max_lines: int = None
    enabled: bool = True


class ViolationRuleManager:
    """Manages architectural rules and layer patterns"""
    
    def __init__(self):
        self.rules: Dict[str, ArchitecturalRule] = {}
        self.layer_patterns: Dict[ArchitecturalLayer, List[str]] = {}
        self.component_layers: Dict[str, ArchitecturalLayer] = {}
        
        # Initialize built-in rules and patterns
        self._initialize_built_in_rules()
        self._initialize_layer_patterns()
    
    def add_rule(self, rule: ArchitecturalRule) -> bool:
        """Add a new architectural rule"""
        try:
            self.rules[rule.id] = rule
            logger.info(f"Added architectural rule: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add rule {rule.id}: {e}")
            return False
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove an architectural rule"""
        try:
            if rule_id in self.rules:
                removed_rule = self.rules.pop(rule_id)
                logger.info(f"Removed architectural rule: {removed_rule.name}")
                return True
            else:
                logger.warning(f"Rule {rule_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to remove rule {rule_id}: {e}")
            return False
    
    def get_rule(self, rule_id: str) -> ArchitecturalRule:
        """Get a specific rule by ID"""
        return self.rules.get(rule_id)
    
    def get_rules_by_type(self, violation_type: ViolationType) -> List[ArchitecturalRule]:
        """Get all rules for a specific violation type"""
        return [rule for rule in self.rules.values() if rule.violation_type == violation_type]
    
    def get_rules_by_severity(self, min_severity: ViolationSeverity) -> List[ArchitecturalRule]:
        """Get all rules with at least the specified severity"""
        severity_order = {
            ViolationSeverity.INFO: 0,
            ViolationSeverity.LOW: 1,
            ViolationSeverity.MEDIUM: 2,
            ViolationSeverity.HIGH: 3,
            ViolationSeverity.CRITICAL: 4
        }
        min_level = severity_order.get(min_severity, 0)
        return [
            rule for rule in self.rules.values() 
            if severity_order.get(rule.severity, 0) >= min_level
        ]
    
    def get_enabled_rules(self) -> List[ArchitecturalRule]:
        """Get all enabled rules"""
        return [rule for rule in self.rules.values() if rule.enabled]
    
    def determine_layer(self, file_path: str) -> ArchitecturalLayer:
        """Determine the architectural layer for a given file"""
        if file_path in self.component_layers:
            return self.component_layers[file_path]
        
        # Match against layer patterns
        for layer, patterns in self.layer_patterns.items():
            for pattern in patterns:
                if pattern in file_path.lower():
                    self.component_layers[file_path] = layer
                    return layer
        
        # Default to unknown
        self.component_layers[file_path] = ArchitecturalLayer.UNKNOWN
        return ArchitecturalLayer.UNKNOWN
    
    def _initialize_built_in_rules(self):
        """Initialize built-in architectural rules"""
        built_in_rules = [
            # Layer violation rules
            ArchitecturalRule(
                id="layer_separation",
                name="Layer Separation",
                description="Ensure proper separation between architectural layers",
                violation_type=ViolationType.LAYER_VIOLATION,
                severity=ViolationSeverity.HIGH,
                pattern=r"from\s+.*\.(presentation|infrastructure)\s+import",
                forbidden_layers=[ArchitecturalLayer.DOMAIN]
            ),
            
            # Dependency rules
            ArchitecturalRule(
                id="circular_import",
                name="Circular Import Detection",
                description="Detect circular imports between modules",
                violation_type=ViolationType.CIRCULAR_DEPENDENCY,
                severity=ViolationSeverity.CRITICAL,
                pattern=r"import\s+(\w+)",
            ),
            
            # Size violations
            ArchitecturalRule(
                id="max_file_size",
                name="Maximum File Size",
                description="Files should not exceed 500 lines",
                violation_type=ViolationType.SIZE_VIOLATION,
                severity=ViolationSeverity.MEDIUM,
                pattern="",
                max_lines=500
            ),
            
            ArchitecturalRule(
                id="max_function_size",
                name="Maximum Function Size",
                description="Functions should not exceed 50 lines",
                violation_type=ViolationType.SIZE_VIOLATION,
                severity=ViolationSeverity.MEDIUM,
                pattern="",
                max_lines=50
            ),
            
            # Complexity violations
            ArchitecturalRule(
                id="max_cyclomatic_complexity",
                name="Maximum Cyclomatic Complexity",
                description="Functions should have complexity <= 10",
                violation_type=ViolationType.COMPLEXITY_VIOLATION,
                severity=ViolationSeverity.MEDIUM,
                pattern="",
                max_complexity=10
            ),
            
            # Coupling violations
            ArchitecturalRule(
                id="max_dependencies",
                name="Maximum Dependencies",
                description="Modules should not have too many dependencies",
                violation_type=ViolationType.COUPLING_VIOLATION,
                severity=ViolationSeverity.MEDIUM,
                pattern="",
                max_dependencies=20
            ),
            
            # Naming conventions
            ArchitecturalRule(
                id="class_naming",
                name="Class Naming Convention",
                description="Classes should use PascalCase",
                violation_type=ViolationType.NAMING_CONVENTION_VIOLATION,
                severity=ViolationSeverity.LOW,
                pattern=r"class\s+([a-z]|.*_)"
            ),
            
            ArchitecturalRule(
                id="function_naming",
                name="Function Naming Convention",
                description="Functions should use snake_case",
                violation_type=ViolationType.NAMING_CONVENTION_VIOLATION,
                severity=ViolationSeverity.LOW,
                pattern=r"def\s+([A-Z]|.*[A-Z])"
            ),
            
            # Anti-patterns
            ArchitecturalRule(
                id="god_class",
                name="God Class Anti-pattern",
                description="Classes should not be overly large or complex",
                violation_type=ViolationType.ANTI_PATTERN,
                severity=ViolationSeverity.HIGH,
                pattern="",
                max_lines=300
            ),
            
            ArchitecturalRule(
                id="long_parameter_list",
                name="Long Parameter List",
                description="Functions should not have too many parameters",
                violation_type=ViolationType.ANTI_PATTERN,
                severity=ViolationSeverity.MEDIUM,
                pattern=r"def\s+\w+\([^)]*,[^)]*,[^)]*,[^)]*,[^)]*,"
            ),
        ]
        
        for rule in built_in_rules:
            self.rules[rule.id] = rule
            
        logger.info(f"Initialized {len(built_in_rules)} built-in architectural rules")
    
    def _initialize_layer_patterns(self):
        """Initialize layer pattern mappings"""
        self.layer_patterns = {
            ArchitecturalLayer.PRESENTATION: [
                "api/", "endpoints/", "controllers/", "views/", "handlers/",
                "routes/", "routers/", "web/", "ui/", "frontend/"
            ],
            ArchitecturalLayer.APPLICATION: [
                "services/", "usecases/", "use_cases/", "application/",
                "business/", "workflows/", "processes/"
            ],
            ArchitecturalLayer.DOMAIN: [
                "models/", "entities/", "domain/", "core/", "business_logic/",
                "aggregates/", "value_objects/"
            ],
            ArchitecturalLayer.INFRASTRUCTURE: [
                "repositories/", "persistence/", "database/", "db/", "storage/",
                "external/", "adapters/", "gateway/", "clients/"
            ],
            ArchitecturalLayer.SHARED: [
                "utils/", "helpers/", "common/", "shared/", "lib/", "libraries/"
            ],
            ArchitecturalLayer.EXTERNAL: [
                "third_party/", "vendor/", "external_libs/", "integrations/"
            ]
        }
        
        logger.info("Initialized architectural layer patterns")


# Global rule manager instance
rule_manager = ViolationRuleManager()