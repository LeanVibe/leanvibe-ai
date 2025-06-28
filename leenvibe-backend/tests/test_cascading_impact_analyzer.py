"""
Test Cascading Impact Analyzer

Tests for cascading impact analysis across project boundaries,
breaking change detection, and cross-project dependency tracking.
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_cascading_impact_analyzer_imports():
    """Test that cascading impact analyzer imports correctly"""
    try:
        from app.services.cascading_impact_analyzer import (
            CascadingImpact,
            CascadingImpactAnalyzer,
            ChangeCompatibility,
            CrossProjectDependency,
            ImpactPropagation,
            ImpactSummary,
            ProjectBoundary,
            ProjectBoundaryType,
            ProjectDependencyGraph,
            cascading_impact_analyzer,
        )

        # Test service exists
        assert cascading_impact_analyzer is not None
        assert isinstance(cascading_impact_analyzer, CascadingImpactAnalyzer)

        # Test enums
        assert hasattr(ProjectBoundaryType, "INTERNAL")
        assert hasattr(ProjectBoundaryType, "WORKSPACE")
        assert hasattr(ProjectBoundaryType, "EXTERNAL")
        assert hasattr(ProjectBoundaryType, "PUBLISHED")
        assert hasattr(ProjectBoundaryType, "SYSTEM")

        assert hasattr(ImpactPropagation, "DIRECT")
        assert hasattr(ImpactPropagation, "TRANSITIVE")
        assert hasattr(ImpactPropagation, "RUNTIME")
        assert hasattr(ImpactPropagation, "BUILD_TIME")

        assert hasattr(ChangeCompatibility, "COMPATIBLE")
        assert hasattr(ChangeCompatibility, "BACKWARD_COMPATIBLE")
        assert hasattr(ChangeCompatibility, "BREAKING")

        print("✅ Cascading impact analyzer imports test passed")
        return True

    except Exception as e:
        print(f"❌ Cascading impact analyzer imports test failed: {e}")
        return False


def test_project_boundary_creation():
    """Test ProjectBoundary creation and properties"""
    try:
        from app.services.cascading_impact_analyzer import (
            ProjectBoundary,
            ProjectBoundaryType,
        )

        # Test boundary creation
        boundary = ProjectBoundary(
            boundary_id="projectA->projectB",
            source_project="projectA",
            target_project="projectB",
            boundary_type=ProjectBoundaryType.WORKSPACE,
            dependencies=["symbol1", "symbol2"],
            version_constraint="^1.0.0",
            is_published=False,
        )

        assert boundary.boundary_id == "projectA->projectB"
        assert boundary.source_project == "projectA"
        assert boundary.target_project == "projectB"
        assert boundary.boundary_type == ProjectBoundaryType.WORKSPACE
        assert len(boundary.dependencies) == 2
        assert boundary.version_constraint == "^1.0.0"
        assert boundary.is_published == False
        assert isinstance(boundary.last_updated, datetime)

        print("✅ Project boundary creation test passed")
        return True

    except Exception as e:
        print(f"❌ Project boundary creation test failed: {e}")
        return False


def test_cross_project_dependency_creation():
    """Test CrossProjectDependency creation"""
    try:
        from app.services.cascading_impact_analyzer import (
            CrossProjectDependency,
            ImpactPropagation,
        )
        from app.services.symbol_dependency_tracker import DependencyType

        # Test cross-project dependency
        dep = CrossProjectDependency(
            dependency_id="dep_123",
            source_symbol_id="symbolA",
            target_symbol_id="symbolB",
            source_project="projectA",
            target_project="projectB",
            dependency_type=DependencyType.IMPORT,
            propagation_type=ImpactPropagation.DIRECT,
            version_requirement=">=1.0.0",
            is_breaking_change_risk=True,
        )

        assert dep.dependency_id == "dep_123"
        assert dep.source_symbol_id == "symbolA"
        assert dep.target_symbol_id == "symbolB"
        assert dep.source_project == "projectA"
        assert dep.target_project == "projectB"
        assert dep.dependency_type == DependencyType.IMPORT
        assert dep.propagation_type == ImpactPropagation.DIRECT
        assert dep.is_breaking_change_risk == True

        print("✅ Cross-project dependency creation test passed")
        return True

    except Exception as e:
        print(f"❌ Cross-project dependency creation test failed: {e}")
        return False


def test_cascading_impact_structure():
    """Test CascadingImpact structure and fields"""
    try:
        from app.services.cascading_impact_analyzer import (
            CascadingImpact,
            ChangeCompatibility,
        )

        # Test cascading impact
        impact = CascadingImpact(
            impact_id="impact_123",
            origin_symbol_id="symbol_origin",
            origin_project="project_origin",
            change_type="modified",
        )

        # Add affected projects
        impact.affected_projects["projectA"] = ["symbol1", "symbol2"]
        impact.affected_projects["projectB"] = ["symbol3"]
        impact.total_affected_symbols = 3
        impact.max_propagation_depth = 5
        impact.compatibility_assessment = ChangeCompatibility.POTENTIALLY_BREAKING
        impact.breaking_changes = ["symbol1"]
        impact.recommendations = ["Update documentation", "Test thoroughly"]
        impact.estimated_effort_hours = 8.5

        assert impact.impact_id == "impact_123"
        assert impact.origin_symbol_id == "symbol_origin"
        assert impact.origin_project == "project_origin"
        assert len(impact.affected_projects) == 2
        assert impact.total_affected_symbols == 3
        assert impact.max_propagation_depth == 5
        assert (
            impact.compatibility_assessment == ChangeCompatibility.POTENTIALLY_BREAKING
        )
        assert len(impact.breaking_changes) == 1
        assert len(impact.recommendations) == 2
        assert impact.estimated_effort_hours == 8.5

        print("✅ Cascading impact structure test passed")
        return True

    except Exception as e:
        print(f"❌ Cascading impact structure test failed: {e}")
        return False


def test_impact_summary_structure():
    """Test ImpactSummary structure"""
    try:
        from app.services.cascading_impact_analyzer import ImpactSummary

        # Test impact summary
        summary = ImpactSummary(
            total_projects_affected=5,
            total_symbols_affected=25,
            critical_paths=[["A", "B", "C"], ["X", "Y", "Z"]],
            risk_assessment="High",
            migration_strategy="Phased migration",
            rollback_plan="Use feature flags",
            communication_plan=["Notify teams", "Update docs"],
        )

        assert summary.total_projects_affected == 5
        assert summary.total_symbols_affected == 25
        assert len(summary.critical_paths) == 2
        assert summary.risk_assessment == "High"
        assert summary.migration_strategy == "Phased migration"
        assert summary.rollback_plan == "Use feature flags"
        assert len(summary.communication_plan) == 2

        print("✅ Impact summary structure test passed")
        return True

    except Exception as e:
        print(f"❌ Impact summary structure test failed: {e}")
        return False


def test_project_boundary_type_enums():
    """Test ProjectBoundaryType enum values"""
    try:
        from app.services.cascading_impact_analyzer import ProjectBoundaryType

        # Test enum values
        assert ProjectBoundaryType.INTERNAL == "internal"
        assert ProjectBoundaryType.WORKSPACE == "workspace"
        assert ProjectBoundaryType.EXTERNAL == "external"
        assert ProjectBoundaryType.PUBLISHED == "published"
        assert ProjectBoundaryType.SYSTEM == "system"

        # Test enum iteration
        boundary_types = list(ProjectBoundaryType)
        assert len(boundary_types) == 5

        print("✅ Project boundary type enums test passed")
        return True

    except Exception as e:
        print(f"❌ Project boundary type enums test failed: {e}")
        return False


def test_impact_propagation_enums():
    """Test ImpactPropagation enum values"""
    try:
        from app.services.cascading_impact_analyzer import ImpactPropagation

        # Test enum values
        assert ImpactPropagation.DIRECT == "direct"
        assert ImpactPropagation.TRANSITIVE == "transitive"
        assert ImpactPropagation.RUNTIME == "runtime"
        assert ImpactPropagation.BUILD_TIME == "build_time"
        assert ImpactPropagation.OPTIONAL == "optional"

        print("✅ Impact propagation enums test passed")
        return True

    except Exception as e:
        print(f"❌ Impact propagation enums test failed: {e}")
        return False


def test_change_compatibility_enums():
    """Test ChangeCompatibility enum values"""
    try:
        from app.services.cascading_impact_analyzer import ChangeCompatibility

        # Test enum values
        assert ChangeCompatibility.COMPATIBLE == "compatible"
        assert ChangeCompatibility.BACKWARD_COMPATIBLE == "backward_compatible"
        assert ChangeCompatibility.BREAKING == "breaking"
        assert ChangeCompatibility.POTENTIALLY_BREAKING == "potentially_breaking"
        assert ChangeCompatibility.UNKNOWN == "unknown"

        print("✅ Change compatibility enums test passed")
        return True

    except Exception as e:
        print(f"❌ Change compatibility enums test failed: {e}")
        return False


async def test_analyzer_initialization():
    """Test cascading impact analyzer initialization"""
    try:
        from app.services.cascading_impact_analyzer import CascadingImpactAnalyzer

        analyzer = CascadingImpactAnalyzer()

        # Test initial state
        assert analyzer.project_graph is not None
        assert len(analyzer.cross_project_dependencies) == 0
        assert len(analyzer.project_boundaries) == 0
        assert len(analyzer.cascading_impacts) == 0
        assert len(analyzer.active_analyses) == 0
        assert len(analyzer.impact_cache) == 0

        # Test configuration
        assert analyzer.max_propagation_depth == 20
        assert analyzer.impact_threshold == 0.3
        assert len(analyzer.breaking_change_patterns) > 0
        assert len(analyzer.external_project_patterns) > 0

        # Test metrics
        metrics = analyzer.get_metrics()
        assert metrics["total_analyses"] == 0
        assert metrics["cross_project_impacts"] == 0
        assert metrics["breaking_changes_detected"] == 0

        print("✅ Analyzer initialization test passed")
        return True

    except Exception as e:
        print(f"❌ Analyzer initialization test failed: {e}")
        return False


async def test_register_project_boundary():
    """Test registering project boundaries"""
    try:
        from app.services.cascading_impact_analyzer import (
            CascadingImpactAnalyzer,
            ProjectBoundaryType,
        )

        analyzer = CascadingImpactAnalyzer()

        # Register boundary
        result = await analyzer.register_project_boundary(
            source_project="backend",
            target_project="frontend",
            boundary_type=ProjectBoundaryType.WORKSPACE,
            dependencies=["api_client", "data_models"],
            version_constraint="^2.0.0",
        )

        assert result == True

        # Verify boundary was registered
        boundary_id = "backend->frontend"
        assert boundary_id in analyzer.project_boundaries

        boundary = analyzer.project_boundaries[boundary_id]
        assert boundary.source_project == "backend"
        assert boundary.target_project == "frontend"
        assert boundary.boundary_type == ProjectBoundaryType.WORKSPACE
        assert len(boundary.dependencies) == 2

        # Verify project graph updated
        assert "frontend" in analyzer.project_graph.projects["backend"]
        assert "backend" in analyzer.project_graph.reverse_dependencies["frontend"]

        print("✅ Register project boundary test passed")
        return True

    except Exception as e:
        print(f"❌ Register project boundary test failed: {e}")
        return False


async def test_cascading_impact_basic():
    """Test basic cascading impact analysis"""
    try:
        from app.services.cascading_impact_analyzer import (
            CascadingImpactAnalyzer,
            ChangeCompatibility,
        )

        analyzer = CascadingImpactAnalyzer()

        # Mock symbol dependency tracker
        with patch(
            "app.services.cascading_impact_analyzer.symbol_dependency_tracker"
        ) as mock_tracker:
            mock_tracker.get_symbol_dependencies = AsyncMock(
                return_value={
                    "direct_dependents": [
                        {
                            "symbol_id": "dependent1",
                            "symbol": {"file_path": "/project2/file.py"},
                            "dependency_type": "import",
                        }
                    ]
                }
            )

            # Run analysis
            impact = await analyzer.analyze_cascading_impact(
                symbol_id="test_symbol",
                project_id="project1",
                change_type="modified",
                include_external=False,
            )

            assert impact.impact_id != "error"
            assert impact.origin_symbol_id == "test_symbol"
            assert impact.origin_project == "project1"
            assert impact.change_type == "modified"
            assert impact.compatibility_assessment != ChangeCompatibility.UNKNOWN

        print("✅ Cascading impact basic test passed")
        return True

    except Exception as e:
        print(f"❌ Cascading impact basic test failed: {e}")
        return False


async def test_impact_summary_generation():
    """Test impact summary generation"""
    try:
        from app.services.cascading_impact_analyzer import (
            CascadingImpact,
            CascadingImpactAnalyzer,
            ChangeCompatibility,
        )

        analyzer = CascadingImpactAnalyzer()

        # Create test impacts
        impact1 = CascadingImpact(
            impact_id="impact1",
            origin_symbol_id="symbol1",
            origin_project="project1",
            change_type="modified",
        )
        impact1.affected_projects = {"project2": ["sym1", "sym2"], "project3": ["sym3"]}
        impact1.breaking_changes = ["sym1"]
        impact1.total_affected_symbols = 3

        impact2 = CascadingImpact(
            impact_id="impact2",
            origin_symbol_id="symbol2",
            origin_project="project1",
            change_type="deleted",
        )
        impact2.affected_projects = {"project2": ["sym4"], "project4": ["sym5"]}
        impact2.breaking_changes = ["sym4", "sym5"]
        impact2.total_affected_symbols = 2

        # Generate summary
        summary = await analyzer.generate_impact_summary([impact1, impact2])

        assert summary.total_projects_affected == 3  # project2, project3, project4
        assert summary.total_symbols_affected == 5  # sym1-5
        assert summary.risk_assessment in ["Low", "Medium", "High", "Critical"]
        assert summary.migration_strategy is not None
        assert len(summary.communication_plan) > 0

        print("✅ Impact summary generation test passed")
        return True

    except Exception as e:
        print(f"❌ Impact summary generation test failed: {e}")
        return False


async def test_project_detection():
    """Test project detection from file paths"""
    try:
        from app.services.cascading_impact_analyzer import CascadingImpactAnalyzer

        analyzer = CascadingImpactAnalyzer()

        # Test various project path patterns
        test_cases = [
            "/workspace/backend/src/main.py",
            "/projects/frontend/lib/components/Button.js",
            "/app/services/auth.py",
            "/packages/shared/index.ts",
            "unknown/path.py",
        ]

        for file_path in test_cases:
            detected = analyzer._get_symbol_project(file_path)
            # Basic check - should return something meaningful
            assert detected is not None and detected != "", f"Failed for {file_path}"
            assert isinstance(detected, str), f"Expected string, got {type(detected)}"

        print("✅ Project detection test passed")
        return True

    except Exception as e:
        print(f"❌ Project detection test failed: {e}")
        return False


async def test_breaking_change_detection():
    """Test breaking change detection logic"""
    try:
        from app.services.cascading_impact_analyzer import CascadingImpactAnalyzer
        from app.services.symbol_dependency_tracker import DependencyType

        analyzer = CascadingImpactAnalyzer()

        # Test breaking change patterns
        test_cases = [
            (
                "signature_changed",
                {"dependency_type": DependencyType.FUNCTION_CALL},
                True,
            ),
            ("removed", {"dependency_type": DependencyType.IMPORT}, True),
            ("moved", {"dependency_type": DependencyType.VARIABLE_ACCESS}, True),
            ("added", {"dependency_type": DependencyType.FUNCTION_CALL}, False),
            ("modified", {"dependency_type": DependencyType.INHERITANCE}, True),
            ("modified", {"dependency_type": DependencyType.ANNOTATION}, False),
        ]

        for change_type, dep_info, expected_breaking in test_cases:
            is_breaking = analyzer._is_breaking_change(change_type, dep_info)
            assert (
                is_breaking == expected_breaking
            ), f"Failed for {change_type} with {dep_info}"

        print("✅ Breaking change detection test passed")
        return True

    except Exception as e:
        print(f"❌ Breaking change detection test failed: {e}")
        return False


async def test_compatibility_assessment():
    """Test change compatibility assessment"""
    try:
        from app.services.cascading_impact_analyzer import (
            CascadingImpactAnalyzer,
            ChangeCompatibility,
        )

        analyzer = CascadingImpactAnalyzer()

        # Test compatibility assessment
        test_cases = [
            ("modified", [], ChangeCompatibility.COMPATIBLE),
            ("added", ["sym1"], ChangeCompatibility.BACKWARD_COMPATIBLE),
            ("deleted", ["sym1", "sym2"], ChangeCompatibility.BREAKING),
            ("modified", ["sym1"] * 15, ChangeCompatibility.BREAKING),
            ("modified", ["sym1", "sym2"], ChangeCompatibility.POTENTIALLY_BREAKING),
        ]

        for change_type, breaking_changes, expected_compat in test_cases:
            compat = analyzer._assess_compatibility(change_type, breaking_changes)
            assert (
                compat == expected_compat
            ), f"Failed for {change_type} with {len(breaking_changes)} breaking changes"

        print("✅ Compatibility assessment test passed")
        return True

    except Exception as e:
        print(f"❌ Compatibility assessment test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running Cascading Impact Analyzer Tests...")
    print()

    # Sync tests
    sync_tests = [
        ("Cascading Impact Analyzer Imports", test_cascading_impact_analyzer_imports),
        ("Project Boundary Creation", test_project_boundary_creation),
        ("Cross-Project Dependency Creation", test_cross_project_dependency_creation),
        ("Cascading Impact Structure", test_cascading_impact_structure),
        ("Impact Summary Structure", test_impact_summary_structure),
        ("Project Boundary Type Enums", test_project_boundary_type_enums),
        ("Impact Propagation Enums", test_impact_propagation_enums),
        ("Change Compatibility Enums", test_change_compatibility_enums),
    ]

    # Async tests
    async_tests = [
        ("Analyzer Initialization", test_analyzer_initialization),
        ("Register Project Boundary", test_register_project_boundary),
        ("Cascading Impact Basic", test_cascading_impact_basic),
        ("Impact Summary Generation", test_impact_summary_generation),
        ("Project Detection", test_project_detection),
        ("Breaking Change Detection", test_breaking_change_detection),
        ("Compatibility Assessment", test_compatibility_assessment),
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
        print("🎉 All cascading impact analyzer tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed or had issues")
