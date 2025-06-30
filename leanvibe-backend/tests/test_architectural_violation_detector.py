"""
Test Architectural Violation Detector

Tests for real-time architectural violation detection service including
rule enforcement, layer violation detection, and quality analysis.
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_architectural_violation_detector_imports():
    """Test that architectural violation detector imports correctly"""
    try:
        from app.services.architectural_violation_detector import (
            ArchitecturalLayer,
            ArchitecturalViolationDetector,
            ViolationSeverity,
            ViolationType,
            architectural_violation_detector,
        )

        # Test service exists
        assert architectural_violation_detector is not None
        assert isinstance(
            architectural_violation_detector, ArchitecturalViolationDetector
        )

        # Test enums
        assert hasattr(ViolationType, "LAYER_VIOLATION")
        assert hasattr(ViolationType, "CIRCULAR_DEPENDENCY")
        assert hasattr(ViolationType, "SIZE_VIOLATION")
        assert hasattr(ViolationType, "COMPLEXITY_VIOLATION")
        assert hasattr(ViolationType, "COUPLING_VIOLATION")
        assert hasattr(ViolationType, "ANTI_PATTERN")

        assert hasattr(ViolationSeverity, "INFO")
        assert hasattr(ViolationSeverity, "WARNING")
        assert hasattr(ViolationSeverity, "ERROR")
        assert hasattr(ViolationSeverity, "CRITICAL")

        assert hasattr(ArchitecturalLayer, "PRESENTATION")
        assert hasattr(ArchitecturalLayer, "BUSINESS")
        assert hasattr(ArchitecturalLayer, "DATA")
        assert hasattr(ArchitecturalLayer, "INFRASTRUCTURE")

        print("✅ Architectural violation detector imports test passed")
        return True

    except Exception as e:
        print(f"❌ Architectural violation detector imports test failed: {e}")
        return False


def test_violation_type_enums():
    """Test ViolationType enum values"""
    try:
        from app.services.architectural_violation_detector import ViolationType

        # Test enum values
        assert ViolationType.LAYER_VIOLATION == "layer_violation"
        assert ViolationType.CIRCULAR_DEPENDENCY == "circular_dependency"
        assert ViolationType.DEPENDENCY_RULE_VIOLATION == "dependency_rule_violation"
        assert (
            ViolationType.NAMING_CONVENTION_VIOLATION == "naming_convention_violation"
        )
        assert ViolationType.SIZE_VIOLATION == "size_violation"
        assert ViolationType.COMPLEXITY_VIOLATION == "complexity_violation"
        assert ViolationType.COUPLING_VIOLATION == "coupling_violation"
        assert ViolationType.COHESION_VIOLATION == "cohesion_violation"
        assert ViolationType.ABSTRACTION_VIOLATION == "abstraction_violation"
        assert ViolationType.ENCAPSULATION_VIOLATION == "encapsulation_violation"
        assert ViolationType.PATTERN_VIOLATION == "pattern_violation"
        assert ViolationType.ANTI_PATTERN == "anti_pattern"

        # Test enum iteration
        violation_types = list(ViolationType)
        assert len(violation_types) == 12

        print("✅ Violation type enums test passed")
        return True

    except Exception as e:
        print(f"❌ Violation type enums test failed: {e}")
        return False


def test_violation_severity_enums():
    """Test ViolationSeverity enum values"""
    try:
        from app.services.architectural_violation_detector import ViolationSeverity

        # Test enum values
        assert ViolationSeverity.INFO == "info"
        assert ViolationSeverity.WARNING == "warning"
        assert ViolationSeverity.ERROR == "error"
        assert ViolationSeverity.CRITICAL == "critical"

        print("✅ Violation severity enums test passed")
        return True

    except Exception as e:
        print(f"❌ Violation severity enums test failed: {e}")
        return False


def test_architectural_layer_enums():
    """Test ArchitecturalLayer enum values"""
    try:
        from app.services.architectural_violation_detector import ArchitecturalLayer

        # Test enum values
        assert ArchitecturalLayer.PRESENTATION == "presentation"
        assert ArchitecturalLayer.BUSINESS == "business"
        assert ArchitecturalLayer.DATA == "data"
        assert ArchitecturalLayer.INFRASTRUCTURE == "infrastructure"
        assert ArchitecturalLayer.UTILITY == "utility"
        assert ArchitecturalLayer.TEST == "test"
        assert ArchitecturalLayer.UNKNOWN == "unknown"

        print("✅ Architectural layer enums test passed")
        return True

    except Exception as e:
        print(f"❌ Architectural layer enums test failed: {e}")
        return False


def test_architectural_rule_creation():
    """Test ArchitecturalRule creation and properties"""
    try:
        from app.services.architectural_violation_detector import (
            ArchitecturalLayer,
            ArchitecturalRule,
            ViolationSeverity,
            ViolationType,
        )

        # Test rule creation
        rule = ArchitecturalRule(
            rule_id="test_rule",
            name="Test Rule",
            description="A test rule for validation",
            violation_type=ViolationType.LAYER_VIOLATION,
            severity=ViolationSeverity.ERROR,
            enabled=True,
            pattern=r".*\.test\..*",
            conditions=["layer == presentation", "target_layer == data"],
            exceptions=["test_files"],
            layers_from={ArchitecturalLayer.PRESENTATION},
            layers_to={ArchitecturalLayer.DATA},
            confidence_threshold=0.8,
            metadata={"category": "architecture", "priority": "high"},
        )

        assert rule.rule_id == "test_rule"
        assert rule.name == "Test Rule"
        assert rule.description == "A test rule for validation"
        assert rule.violation_type == ViolationType.LAYER_VIOLATION
        assert rule.severity == ViolationSeverity.ERROR
        assert rule.enabled is True
        assert rule.pattern == r".*\.test\..*"
        assert len(rule.conditions) == 2
        assert len(rule.exceptions) == 1
        assert ArchitecturalLayer.PRESENTATION in rule.layers_from
        assert ArchitecturalLayer.DATA in rule.layers_to
        assert rule.confidence_threshold == 0.8
        assert rule.metadata["category"] == "architecture"

        print("✅ Architectural rule creation test passed")
        return True

    except Exception as e:
        print(f"❌ Architectural rule creation test failed: {e}")
        return False


def test_violation_instance_creation():
    """Test ViolationInstance creation"""
    try:
        from app.services.architectural_violation_detector import (
            ViolationInstance,
            ViolationSeverity,
            ViolationType,
        )

        # Test violation creation
        violation = ViolationInstance(
            violation_id="violation_123",
            rule_id="rule_456",
            violation_type=ViolationType.SIZE_VIOLATION,
            severity=ViolationSeverity.WARNING,
            file_path="/test/large_file.py",
            symbol_id="symbol_789",
            symbol_name="huge_function",
            line_start=100,
            line_end=250,
            description="Function exceeds size limit",
            details="Function has 150 lines, exceeds limit of 100",
            suggestion="Break function into smaller methods",
            confidence_score=0.9,
            related_violations=["violation_124", "violation_125"],
            affected_components=["component_1", "component_2"],
            context={"lines": 150, "complexity": 25},
        )

        assert violation.violation_id == "violation_123"
        assert violation.rule_id == "rule_456"
        assert violation.violation_type == ViolationType.SIZE_VIOLATION
        assert violation.severity == ViolationSeverity.WARNING
        assert violation.file_path == "/test/large_file.py"
        assert violation.symbol_id == "symbol_789"
        assert violation.symbol_name == "huge_function"
        assert violation.line_start == 100
        assert violation.line_end == 250
        assert violation.description == "Function exceeds size limit"
        assert violation.details == "Function has 150 lines, exceeds limit of 100"
        assert violation.suggestion == "Break function into smaller methods"
        assert violation.confidence_score == 0.9
        assert len(violation.related_violations) == 2
        assert len(violation.affected_components) == 2
        assert isinstance(violation.detected_at, datetime)
        assert violation.context["lines"] == 150

        print("✅ Violation instance creation test passed")
        return True

    except Exception as e:
        print(f"❌ Violation instance creation test failed: {e}")
        return False


def test_component_metrics_creation():
    """Test ComponentMetrics creation"""
    try:
        from app.services.architectural_violation_detector import ComponentMetrics

        # Test metrics creation
        metrics = ComponentMetrics(
            component_id="component_123",
            component_type="file",
            file_path="/test/component.py",
            size_metrics={"lines": 500, "symbols": 25, "functions": 10, "classes": 3},
            complexity_metrics={"average_complexity": 8.5, "max_complexity": 15},
            coupling_metrics={"afferent_coupling": 5, "efferent_coupling": 8},
            cohesion_score=0.75,
            dependencies_in=5,
            dependencies_out=8,
        )

        assert metrics.component_id == "component_123"
        assert metrics.component_type == "file"
        assert metrics.file_path == "/test/component.py"
        assert metrics.size_metrics["lines"] == 500
        assert metrics.size_metrics["symbols"] == 25
        assert metrics.size_metrics["functions"] == 10
        assert metrics.size_metrics["classes"] == 3
        assert metrics.complexity_metrics["average_complexity"] == 8.5
        assert metrics.complexity_metrics["max_complexity"] == 15
        assert metrics.coupling_metrics["afferent_coupling"] == 5
        assert metrics.coupling_metrics["efferent_coupling"] == 8
        assert metrics.cohesion_score == 0.75
        assert metrics.dependencies_in == 5
        assert metrics.dependencies_out == 8
        assert isinstance(metrics.last_updated, datetime)

        print("✅ Component metrics creation test passed")
        return True

    except Exception as e:
        print(f"❌ Component metrics creation test failed: {e}")
        return False


def test_architectural_report_creation():
    """Test ArchitecturalReport creation"""
    try:
        from app.services.architectural_violation_detector import (
            ArchitecturalReport,
            ComponentMetrics,
            ViolationInstance,
            ViolationSeverity,
            ViolationType,
        )

        # Create test data
        violation = ViolationInstance(
            violation_id="violation_1",
            rule_id="rule_1",
            violation_type=ViolationType.SIZE_VIOLATION,
            severity=ViolationSeverity.WARNING,
            file_path="/test/file.py",
            description="Test violation",
        )

        metrics = ComponentMetrics(
            component_id="component_1", component_type="file", file_path="/test/file.py"
        )

        # Test report creation
        report = ArchitecturalReport(
            report_id="report_123",
            project_id="project_456",
            analysis_timestamp=datetime.now(),
            violations=[violation],
            component_metrics=[metrics],
            summary={"total_violations": 1, "quality_score": 0.85},
            trends={"improvement": 15, "regression": 3},
            recommendations=["Fix size violations", "Improve coupling"],
            quality_score=0.85,
        )

        assert report.report_id == "report_123"
        assert report.project_id == "project_456"
        assert isinstance(report.analysis_timestamp, datetime)
        assert len(report.violations) == 1
        assert len(report.component_metrics) == 1
        assert report.summary["total_violations"] == 1
        assert report.summary["quality_score"] == 0.85
        assert report.trends["improvement"] == 15
        assert len(report.recommendations) == 2
        assert report.quality_score == 0.85

        print("✅ Architectural report creation test passed")
        return True

    except Exception as e:
        print(f"❌ Architectural report creation test failed: {e}")
        return False


async def test_detector_initialization():
    """Test architectural violation detector initialization"""
    try:
        from app.services.architectural_violation_detector import (
            ArchitecturalViolationDetector,
        )

        detector = ArchitecturalViolationDetector()

        # Test initial state
        assert len(detector.rules) > 0  # Should have built-in rules
        assert len(detector.violations) == 0
        assert len(detector.component_metrics) == 0
        assert len(detector.violation_cache) == 0

        # Test layer patterns
        assert len(detector.layer_patterns) > 0

        # Test configuration
        assert detector.max_file_size == 10000
        assert detector.max_function_size == 100
        assert detector.max_class_size == 500
        assert detector.max_complexity == 15
        assert detector.max_dependencies == 20
        assert detector.real_time_enabled is True

        # Test metrics
        assert detector.metrics["total_violations"] == 0
        assert detector.metrics["components_analyzed"] == 0

        # Test initialization
        success = await detector.initialize()
        assert success is True

        # Cleanup
        await detector.shutdown()

        print("✅ Detector initialization test passed")
        return True

    except Exception as e:
        print(f"❌ Detector initialization test failed: {e}")
        return False


async def test_layer_determination():
    """Test architectural layer determination"""
    try:
        from app.services.architectural_violation_detector import (
            ArchitecturalLayer,
            ArchitecturalViolationDetector,
        )

        detector = ArchitecturalViolationDetector()

        # Test presentation layer detection
        assert (
            detector._determine_layer("/app/ui/components/button.py")
            == ArchitecturalLayer.PRESENTATION
        )
        assert (
            detector._determine_layer("/src/views/user_view.py")
            == ArchitecturalLayer.PRESENTATION
        )
        assert (
            detector._determine_layer("/frontend/controllers/auth.py")
            == ArchitecturalLayer.PRESENTATION
        )

        # Test business layer detection
        assert (
            detector._determine_layer("/app/services/user_service.py")
            == ArchitecturalLayer.BUSINESS
        )
        assert (
            detector._determine_layer("/src/business/logic.py")
            == ArchitecturalLayer.BUSINESS
        )
        assert (
            detector._determine_layer("/core/domain/entities.py")
            == ArchitecturalLayer.BUSINESS
        )

        # Test data layer detection
        assert (
            detector._determine_layer("/app/data/repository.py")
            == ArchitecturalLayer.DATA
        )
        assert (
            detector._determine_layer("/src/database/models.py")
            == ArchitecturalLayer.DATA
        )
        assert (
            detector._determine_layer("/storage/migrations/001.py")
            == ArchitecturalLayer.DATA
        )

        # Test infrastructure layer detection
        assert (
            detector._determine_layer("/app/infrastructure/config.py")
            == ArchitecturalLayer.INFRASTRUCTURE
        )
        assert (
            detector._determine_layer("/src/utils/helpers.py")
            == ArchitecturalLayer.INFRASTRUCTURE
        )
        assert (
            detector._determine_layer("/external/clients/api.py")
            == ArchitecturalLayer.INFRASTRUCTURE
        )

        # Test test layer detection
        assert (
            detector._determine_layer("/tests/unit/test_user.py")
            == ArchitecturalLayer.TEST
        )
        assert detector._determine_layer("/src/user_test.py") == ArchitecturalLayer.TEST

        # Test unknown layer
        assert (
            detector._determine_layer("/random/path/file.py")
            == ArchitecturalLayer.UNKNOWN
        )

        print("✅ Layer determination test passed")
        return True

    except Exception as e:
        print(f"❌ Layer determination test failed: {e}")
        return False


async def test_analyze_file():
    """Test file analysis functionality"""
    try:
        from app.models.ast_models import (
            FileAnalysis,
            LanguageType,
            Symbol,
            SymbolType,
        )
        from app.services.architectural_violation_detector import (
            ArchitecturalViolationDetector,
        )

        detector = ArchitecturalViolationDetector()
        await detector.initialize()

        # Create mock file analysis with large function (should trigger size violation)
        large_function = Symbol(
            id="large_function",
            name="huge_method",
            symbol_type=SymbolType.FUNCTION,
            file_path="/test/file.py",
            line_start=1,
            line_end=150,  # 150 lines - exceeds limit of 100
            column_start=0,
            column_end=10,
        )

        file_analysis = FileAnalysis(
            file_path="/test/file.py",
            language=LanguageType.PYTHON,
            symbols=[large_function],
            dependencies=[],
            imports=[],
            exports=[],
            complexity_metrics={},
        )

        # Mock ast_service
        with patch(
            "app.services.architectural_violation_detector.ast_service"
        ) as mock_ast:
            mock_ast.analyze_file = AsyncMock(return_value=file_analysis)

            violations = await detector.analyze_file("/test/file.py")

            # Should find size violation
            assert len(violations) >= 1
            size_violations = [v for v in violations if "size" in v.violation_type]
            assert len(size_violations) > 0

        await detector.shutdown()

        print("✅ Analyze file test passed")
        return True

    except Exception as e:
        print(f"❌ Analyze file test failed: {e}")
        return False


async def test_size_violation_detection():
    """Test size violation detection"""
    try:
        from app.models.ast_models import FileAnalysis, LanguageType, Symbol, SymbolType
        from app.services.architectural_violation_detector import (
            ArchitecturalViolationDetector,
            ViolationType,
        )

        detector = ArchitecturalViolationDetector()

        # Create symbols with size violations
        large_function = Symbol(
            id="large_function",
            name="huge_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="/test/file.py",
            line_start=1,
            line_end=120,  # 120 lines - exceeds limit of 100
            column_start=0,
            column_end=10,
        )

        large_class = Symbol(
            id="large_class",
            name="GodClass",
            symbol_type=SymbolType.CLASS,
            file_path="/test/file.py",
            line_start=150,
            line_end=800,  # 651 lines - exceeds limit of 500
            column_start=0,
            column_end=10,
        )

        file_analysis = FileAnalysis(
            file_path="/test/file.py",
            language=LanguageType.PYTHON,
            symbols=[large_function, large_class],
            dependencies=[],
            imports=[],
            exports=[],
            complexity_metrics={},
        )

        # Mock component metrics calculation
        component_metrics = await detector._calculate_component_metrics(
            "/test/file.py", file_analysis
        )

        # Apply size violation rules
        function_rule = detector.rules["function_size_violation"]
        class_rule = detector.rules["class_size_violation"]

        function_violations = detector._check_size_violations(
            function_rule, "/test/file.py", file_analysis, component_metrics
        )
        class_violations = detector._check_size_violations(
            class_rule, "/test/file.py", file_analysis, component_metrics
        )

        # Should detect violations
        assert len(function_violations) == 1
        assert function_violations[0].violation_type == ViolationType.SIZE_VIOLATION
        assert function_violations[0].symbol_name == "huge_function"

        assert len(class_violations) == 1
        assert class_violations[0].violation_type == ViolationType.SIZE_VIOLATION
        assert class_violations[0].symbol_name == "GodClass"

        print("✅ Size violation detection test passed")
        return True

    except Exception as e:
        print(f"❌ Size violation detection test failed: {e}")
        return False


async def test_complexity_violation_detection():
    """Test complexity violation detection"""
    try:
        from app.models.ast_models import FileAnalysis, LanguageType, Symbol, SymbolType
        from app.services.architectural_violation_detector import (
            ArchitecturalViolationDetector,
            ViolationType,
        )

        detector = ArchitecturalViolationDetector()

        # Create function with high complexity
        complex_function = Symbol(
            id="complex_function",
            name="complex_method",
            symbol_type=SymbolType.FUNCTION,
            file_path="/test/file.py",
            line_start=1,
            line_end=50,
            column_start=0,
            column_end=10,
        )
        # Simulate high complexity
        complex_function.complexity = 20  # Exceeds limit of 15

        file_analysis = FileAnalysis(
            file_path="/test/file.py",
            language=LanguageType.PYTHON,
            symbols=[complex_function],
            dependencies=[],
            imports=[],
            exports=[],
            complexity_metrics={},
        )

        # Apply complexity violation rule
        rule = detector.rules["complexity_violation"]
        violations = detector._check_complexity_violations(
            rule, "/test/file.py", file_analysis
        )

        # Should detect violation
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.COMPLEXITY_VIOLATION
        assert violations[0].symbol_name == "complex_method"
        assert "complexity 20" in violations[0].description

        print("✅ Complexity violation detection test passed")
        return True

    except Exception as e:
        print(f"❌ Complexity violation detection test failed: {e}")
        return False


async def test_coupling_violation_detection():
    """Test coupling violation detection"""
    try:
        from app.services.architectural_violation_detector import (
            ArchitecturalViolationDetector,
            ComponentMetrics,
            ViolationType,
        )

        detector = ArchitecturalViolationDetector()

        # Create component with high coupling
        high_coupling_metrics = ComponentMetrics(
            component_id="/test/file.py",
            component_type="file",
            file_path="/test/file.py",
            dependencies_in=15,  # High coupling
            dependencies_out=10,  # Total: 25, exceeds limit of 20
        )

        # Apply coupling violation rule
        rule = detector.rules["high_coupling_violation"]
        violations = detector._check_coupling_violations(
            rule, "/test/file.py", high_coupling_metrics
        )

        # Should detect violation
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.COUPLING_VIOLATION
        assert "25 dependencies" in violations[0].description

        print("✅ Coupling violation detection test passed")
        return True

    except Exception as e:
        print(f"❌ Coupling violation detection test failed: {e}")
        return False


async def test_layer_violation_detection():
    """Test layer violation detection"""
    try:
        from app.models.ast_models import Dependency, FileAnalysis, LanguageType
        from app.services.architectural_violation_detector import (
            ArchitecturalViolationDetector,
            ViolationType,
        )

        detector = ArchitecturalViolationDetector()

        # Create dependency from presentation to data layer (violation)
        dependency = Dependency(
            source_file="/app/ui/component.py",  # Presentation layer
            target_file="/app/data/models.py",  # Data layer
            target_symbol="database_model",
            dependency_type="import",
            line_number=10,
            is_external=False,
        )

        file_analysis = FileAnalysis(
            file_path="/app/ui/component.py",
            language=LanguageType.PYTHON,
            symbols=[],
            dependencies=[dependency],
            imports=[],
            exports=[],
            complexity_metrics={},
        )

        # Apply layer violation rule
        rule = detector.rules["layer_presentation_to_data"]
        violations = await detector._check_layer_violations(
            rule, "/app/ui/component.py", file_analysis
        )

        # Should detect violation
        assert len(violations) >= 1
        layer_violations = [
            v for v in violations if v.violation_type == ViolationType.LAYER_VIOLATION
        ]
        assert len(layer_violations) >= 1
        assert "layer violation" in layer_violations[0].description.lower()

        print("✅ Layer violation detection test passed")
        return True

    except Exception as e:
        print(f"❌ Layer violation detection test failed: {e}")
        return False


async def test_anti_pattern_detection():
    """Test anti-pattern detection"""
    try:
        from app.models.ast_models import FileAnalysis, LanguageType, Symbol, SymbolType
        from app.services.architectural_violation_detector import (
            ArchitecturalViolationDetector,
            ComponentMetrics,
            ViolationType,
        )

        detector = ArchitecturalViolationDetector()

        # Create god class (large class with many methods)
        god_class = Symbol(
            id="god_class",
            name="GodClass",
            symbol_type=SymbolType.CLASS,
            file_path="/test/file.py",
            line_start=1,
            line_end=300,  # 300 lines
            column_start=0,
            column_end=10,
        )

        # Create many methods for the class
        methods = []
        for i in range(15):  # 15 methods
            method = Symbol(
                id=f"method_{i}",
                name=f"method_{i}",
                symbol_type=SymbolType.METHOD,
                file_path="/test/file.py",
                line_start=10 + i * 10,
                line_end=15 + i * 10,
                column_start=4,
                column_end=20,
            )
            methods.append(method)

        file_analysis = FileAnalysis(
            file_path="/test/file.py",
            language=LanguageType.PYTHON,
            symbols=[god_class] + methods,
            dependencies=[],
            imports=[],
            exports=[],
            complexity_metrics={},
        )

        component_metrics = ComponentMetrics(
            component_id="/test/file.py",
            component_type="file",
            file_path="/test/file.py",
        )

        # Apply anti-pattern rule
        rule = detector.rules["god_class_antipattern"]
        violations = detector._check_anti_patterns(
            rule, "/test/file.py", file_analysis, component_metrics
        )

        # Should detect god class
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.ANTI_PATTERN
        assert violations[0].symbol_name == "GodClass"
        assert "God class detected" in violations[0].description

        print("✅ Anti-pattern detection test passed")
        return True

    except Exception as e:
        print(f"❌ Anti-pattern detection test failed: {e}")
        return False


async def test_project_analysis():
    """Test full project analysis"""
    try:
        from app.models.ast_models import (
            FileAnalysis,
            LanguageType,
            ProjectIndex,
            Symbol,
            SymbolType,
        )
        from app.services.architectural_violation_detector import (
            ArchitecturalViolationDetector,
        )

        detector = ArchitecturalViolationDetector()
        await detector.initialize()

        # Create mock project with violations
        symbol = Symbol(
            id="test_symbol",
            name="test_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="/test/file.py",
            line_start=1,
            line_end=30,
            column_start=0,
            column_end=10,
        )

        file_analysis = FileAnalysis(
            file_path="/test/file.py",
            language=LanguageType.PYTHON,
            symbols=[symbol],
            dependencies=[],
            imports=[],
            exports=[],
            complexity_metrics={},
        )

        project_index = ProjectIndex(
            workspace_path="/test",
            files={"/test/file.py": file_analysis},
            symbols={"test_symbol": symbol},
            dependencies=[],
            supported_files=1,
            total_files=1,
        )

        # Mock graph service
        with patch(
            "app.services.architectural_violation_detector.graph_service"
        ) as mock_graph:
            mock_graph.get_project_index = AsyncMock(return_value=project_index)

            # Mock ast_service
            with patch(
                "app.services.architectural_violation_detector.ast_service"
            ) as mock_ast:
                mock_ast.analyze_file = AsyncMock(return_value=file_analysis)

                report = await detector.analyze_project("test_project")

                assert report.project_id == "test_project"
                assert isinstance(report.analysis_timestamp, datetime)
                assert report.violations is not None
                assert report.component_metrics is not None
                assert "total_violations" in report.summary
                assert report.quality_score >= 0.0

        await detector.shutdown()

        print("✅ Project analysis test passed")
        return True

    except Exception as e:
        print(f"❌ Project analysis test failed: {e}")
        return False


def test_rule_management():
    """Test adding and removing rules"""
    try:
        from app.services.architectural_violation_detector import (
            ArchitecturalRule,
            ArchitecturalViolationDetector,
            ViolationSeverity,
            ViolationType,
        )

        detector = ArchitecturalViolationDetector()
        initial_rule_count = len(detector.rules)

        # Test adding rule
        new_rule = ArchitecturalRule(
            rule_id="test_custom_rule",
            name="Test Custom Rule",
            description="A custom test rule",
            violation_type=ViolationType.NAMING_CONVENTION_VIOLATION,
            severity=ViolationSeverity.INFO,
        )

        success = detector.add_rule(new_rule)
        assert success is True
        assert len(detector.rules) == initial_rule_count + 1
        assert "test_custom_rule" in detector.rules

        # Test removing rule
        success = detector.remove_rule("test_custom_rule")
        assert success is True
        assert len(detector.rules) == initial_rule_count
        assert "test_custom_rule" not in detector.rules

        # Test removing non-existent rule
        success = detector.remove_rule("non_existent_rule")
        assert success is False

        print("✅ Rule management test passed")
        return True

    except Exception as e:
        print(f"❌ Rule management test failed: {e}")
        return False


def test_violation_filtering():
    """Test violation filtering methods"""
    try:
        from app.services.architectural_violation_detector import (
            ArchitecturalViolationDetector,
            ViolationInstance,
            ViolationSeverity,
            ViolationType,
        )

        detector = ArchitecturalViolationDetector()

        # Create test violations
        violations = [
            ViolationInstance(
                violation_id="v1",
                rule_id="r1",
                violation_type=ViolationType.SIZE_VIOLATION,
                severity=ViolationSeverity.WARNING,
                file_path="/test/file1.py",
                description="Size violation 1",
            ),
            ViolationInstance(
                violation_id="v2",
                rule_id="r2",
                violation_type=ViolationType.COMPLEXITY_VIOLATION,
                severity=ViolationSeverity.ERROR,
                file_path="/test/file2.py",
                description="Complexity violation 1",
            ),
            ViolationInstance(
                violation_id="v3",
                rule_id="r3",
                violation_type=ViolationType.SIZE_VIOLATION,
                severity=ViolationSeverity.ERROR,
                file_path="/test/file1.py",
                description="Size violation 2",
            ),
        ]

        detector.violations = violations

        # Test filtering by file
        file1_violations = detector.get_violations_for_file("/test/file1.py")
        assert len(file1_violations) == 2
        assert all(v.file_path == "/test/file1.py" for v in file1_violations)

        # Test filtering by type
        size_violations = detector.get_violations_by_type(ViolationType.SIZE_VIOLATION)
        assert len(size_violations) == 2
        assert all(
            v.violation_type == ViolationType.SIZE_VIOLATION for v in size_violations
        )

        # Test filtering by severity
        error_violations = detector.get_violations_by_severity(ViolationSeverity.ERROR)
        assert len(error_violations) == 2
        assert all(v.severity == ViolationSeverity.ERROR for v in error_violations)

        print("✅ Violation filtering test passed")
        return True

    except Exception as e:
        print(f"❌ Violation filtering test failed: {e}")
        return False


def test_subscription_management():
    """Test violation subscription management"""
    try:
        from app.services.architectural_violation_detector import (
            ArchitecturalViolationDetector,
        )

        detector = ArchitecturalViolationDetector()

        # Test subscribing
        detector.subscribe_to_violations("/test/file.py", "client_1")
        detector.subscribe_to_violations("/test/file.py", "client_2")
        detector.subscribe_to_violations("/test/other.py", "client_1")

        assert len(detector.violation_subscribers["/test/file.py"]) == 2
        assert len(detector.violation_subscribers["/test/other.py"]) == 1
        assert "client_1" in detector.violation_subscribers["/test/file.py"]
        assert "client_2" in detector.violation_subscribers["/test/file.py"]

        # Test unsubscribing
        detector.unsubscribe_from_violations("/test/file.py", "client_1")
        assert len(detector.violation_subscribers["/test/file.py"]) == 1
        assert "client_1" not in detector.violation_subscribers["/test/file.py"]
        assert "client_2" in detector.violation_subscribers["/test/file.py"]

        # Test unsubscribing last client
        detector.unsubscribe_from_violations("/test/file.py", "client_2")
        assert "/test/file.py" not in detector.violation_subscribers

        print("✅ Subscription management test passed")
        return True

    except Exception as e:
        print(f"❌ Subscription management test failed: {e}")
        return False


def test_detector_metrics():
    """Test detector metrics collection"""
    try:
        from app.services.architectural_violation_detector import (
            ArchitecturalViolationDetector,
        )

        detector = ArchitecturalViolationDetector()

        # Get initial metrics
        metrics = detector.get_metrics()

        assert "total_violations" in metrics
        assert "violations_by_type" in metrics
        assert "violations_by_severity" in metrics
        assert "rules_checked" in metrics
        assert "analysis_time_ms" in metrics
        assert "components_analyzed" in metrics
        assert "active_rules" in metrics
        assert "total_rules" in metrics
        assert "active_monitors" in metrics
        assert "violation_subscribers" in metrics
        assert "pending_analysis" in metrics
        assert "component_metrics_count" in metrics

        # Should have built-in rules
        assert metrics["total_rules"] > 0
        assert metrics["active_rules"] > 0
        assert metrics["total_violations"] == 0
        assert metrics["components_analyzed"] == 0

        print("✅ Detector metrics test passed")
        return True

    except Exception as e:
        print(f"❌ Detector metrics test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running Architectural Violation Detector Tests...")
    print()

    # Sync tests
    sync_tests = [
        (
            "Architectural Violation Detector Imports",
            test_architectural_violation_detector_imports,
        ),
        ("Violation Type Enums", test_violation_type_enums),
        ("Violation Severity Enums", test_violation_severity_enums),
        ("Architectural Layer Enums", test_architectural_layer_enums),
        ("Architectural Rule Creation", test_architectural_rule_creation),
        ("Violation Instance Creation", test_violation_instance_creation),
        ("Component Metrics Creation", test_component_metrics_creation),
        ("Architectural Report Creation", test_architectural_report_creation),
        ("Rule Management", test_rule_management),
        ("Violation Filtering", test_violation_filtering),
        ("Subscription Management", test_subscription_management),
        ("Detector Metrics", test_detector_metrics),
    ]

    # Async tests
    async_tests = [
        ("Detector Initialization", test_detector_initialization),
        ("Layer Determination", test_layer_determination),
        ("Analyze File", test_analyze_file),
        ("Size Violation Detection", test_size_violation_detection),
        ("Complexity Violation Detection", test_complexity_violation_detection),
        ("Coupling Violation Detection", test_coupling_violation_detection),
        ("Layer Violation Detection", test_layer_violation_detection),
        ("Anti-pattern Detection", test_anti_pattern_detection),
        ("Project Analysis", test_project_analysis),
    ]

    passed = 0
    total = len(sync_tests) + len(async_tests)

    # Run sync tests
    for test_name, test_func in sync_tests:
        print(f"Running {test_name} test...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
        print()

    # Run async tests
    for test_name, test_func in async_tests:
        print(f"Running {test_name} test...")
        try:
            if asyncio.run(test_func()):
                passed += 1
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
        print()

    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All architectural violation detector tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed or had issues")
