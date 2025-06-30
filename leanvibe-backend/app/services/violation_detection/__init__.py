"""
Architectural Violation Detection Module

Modular architecture for detecting, managing, and reporting architectural violations.
Replaces the monolithic architectural_violation_detector.py with focused components.
"""

from .rule_manager import (
    ViolationType,
    ViolationSeverity, 
    ArchitecturalLayer,
    ArchitecturalRule,
    ViolationRuleManager,
    rule_manager
)

from .detector import (
    ViolationInstance,
    ComponentMetrics,
    ViolationDetector,
    violation_detector
)

from .reporter import (
    ArchitecturalReport,
    ViolationReporter,
    violation_reporter
)

from .orchestrator import (
    ArchitecturalViolationService,
    architectural_violation_service
)

__all__ = [
    # Types and enums
    "ViolationType",
    "ViolationSeverity",
    "ArchitecturalLayer",
    
    # Data classes
    "ArchitecturalRule",
    "ViolationInstance", 
    "ComponentMetrics",
    "ArchitecturalReport",
    
    # Service classes
    "ViolationRuleManager",
    "ViolationDetector",
    "ViolationReporter",
    "ArchitecturalViolationService",
    
    # Global instances
    "rule_manager",
    "violation_detector",
    "violation_reporter",
    "architectural_violation_service"
]