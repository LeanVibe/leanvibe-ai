"""
Test Change Classifier

Tests for intelligent change classification service that automatically
classifies code changes as breaking, non-breaking, or potentially breaking.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_change_classifier_imports():
    """Test that change classifier imports correctly"""
    try:
        from app.services.change_classifier import (
            BreakingChangeType,
            ChangeCategory,
            ChangeClassifier,
            ChangeRisk,
            CompatibilityLevel,
            change_classifier,
        )

        # Test service exists
        assert change_classifier is not None
        assert isinstance(change_classifier, ChangeClassifier)

        # Test enums
        assert hasattr(BreakingChangeType, "SIGNATURE_CHANGE")
        assert hasattr(BreakingChangeType, "REMOVAL")
        assert hasattr(BreakingChangeType, "VISIBILITY_REDUCTION")
        assert hasattr(BreakingChangeType, "RETURN_TYPE_CHANGE")
        assert hasattr(BreakingChangeType, "PARAMETER_REMOVAL")

        assert hasattr(ChangeCategory, "API_CHANGE")
        assert hasattr(ChangeCategory, "IMPLEMENTATION_CHANGE")
        assert hasattr(ChangeCategory, "STRUCTURAL_CHANGE")
        assert hasattr(ChangeCategory, "DOCUMENTATION_CHANGE")

        assert hasattr(ChangeRisk, "SAFE")
        assert hasattr(ChangeRisk, "LOW_RISK")
        assert hasattr(ChangeRisk, "MEDIUM_RISK")
        assert hasattr(ChangeRisk, "HIGH_RISK")
        assert hasattr(ChangeRisk, "BREAKING")

        assert hasattr(CompatibilityLevel, "BACKWARD_COMPATIBLE")
        assert hasattr(CompatibilityLevel, "FORWARD_COMPATIBLE")
        assert hasattr(CompatibilityLevel, "COMPATIBLE")
        assert hasattr(CompatibilityLevel, "POTENTIALLY_BREAKING")
        assert hasattr(CompatibilityLevel, "BREAKING")

        print("✅ Change classifier imports test passed")
        return True

    except Exception as e:
        print(f"❌ Change classifier imports test failed: {e}")
        return False


def test_breaking_change_type_enums():
    """Test BreakingChangeType enum values"""
    try:
        from app.services.change_classifier import BreakingChangeType

        # Test enum values
        assert BreakingChangeType.SIGNATURE_CHANGE == "signature_change"
        assert BreakingChangeType.REMOVAL == "removal"
        assert BreakingChangeType.VISIBILITY_REDUCTION == "visibility_reduction"
        assert BreakingChangeType.RETURN_TYPE_CHANGE == "return_type_change"
        assert BreakingChangeType.PARAMETER_REMOVAL == "parameter_removal"
        assert BreakingChangeType.PARAMETER_TYPE_CHANGE == "parameter_type_change"
        assert BreakingChangeType.INHERITANCE_CHANGE == "inheritance_change"
        assert BreakingChangeType.INTERFACE_CHANGE == "interface_change"
        assert BreakingChangeType.EXCEPTION_CHANGE == "exception_change"
        assert BreakingChangeType.BEHAVIOR_CHANGE == "behavior_change"
        assert BreakingChangeType.API_CONTRACT_CHANGE == "api_contract_change"

        # Test enum iteration
        breaking_types = list(BreakingChangeType)
        assert len(breaking_types) == 11

        print("✅ Breaking change type enums test passed")
        return True

    except Exception as e:
        print(f"❌ Breaking change type enums test failed: {e}")
        return False


def test_change_category_enums():
    """Test ChangeCategory enum values"""
    try:
        from app.services.change_classifier import ChangeCategory

        # Test enum values
        assert ChangeCategory.API_CHANGE == "api_change"
        assert ChangeCategory.IMPLEMENTATION_CHANGE == "implementation_change"
        assert ChangeCategory.STRUCTURAL_CHANGE == "structural_change"
        assert ChangeCategory.DOCUMENTATION_CHANGE == "documentation_change"
        assert ChangeCategory.TEST_CHANGE == "test_change"
        assert ChangeCategory.BUILD_CHANGE == "build_change"
        assert ChangeCategory.CONFIGURATION_CHANGE == "configuration_change"

        print("✅ Change category enums test passed")
        return True

    except Exception as e:
        print(f"❌ Change category enums test failed: {e}")
        return False


def test_change_risk_enums():
    """Test ChangeRisk enum values"""
    try:
        from app.services.change_classifier import ChangeRisk

        # Test enum values
        assert ChangeRisk.SAFE == "safe"
        assert ChangeRisk.LOW_RISK == "low_risk"
        assert ChangeRisk.MEDIUM_RISK == "medium_risk"
        assert ChangeRisk.HIGH_RISK == "high_risk"
        assert ChangeRisk.BREAKING == "breaking"

        print("✅ Change risk enums test passed")
        return True

    except Exception as e:
        print(f"❌ Change risk enums test failed: {e}")
        return False


def test_compatibility_level_enums():
    """Test CompatibilityLevel enum values"""
    try:
        from app.services.change_classifier import CompatibilityLevel

        # Test enum values
        assert CompatibilityLevel.BACKWARD_COMPATIBLE == "backward_compatible"
        assert CompatibilityLevel.FORWARD_COMPATIBLE == "forward_compatible"
        assert CompatibilityLevel.COMPATIBLE == "compatible"
        assert CompatibilityLevel.POTENTIALLY_BREAKING == "potentially_breaking"
        assert CompatibilityLevel.BREAKING == "breaking"
        assert CompatibilityLevel.UNKNOWN == "unknown"

        print("✅ Compatibility level enums test passed")
        return True

    except Exception as e:
        print(f"❌ Compatibility level enums test failed: {e}")
        return False


def test_change_pattern_creation():
    """Test ChangePattern creation and properties"""
    try:
        from app.models.ast_models import LanguageType
        from app.services.change_classifier import ChangePattern

        # Test pattern creation
        pattern = ChangePattern(
            pattern_id="test_pattern",
            name="Test Pattern",
            description="A test pattern for validation",
            language=LanguageType.PYTHON,
            file_patterns=["*.py", "*.pyi"],
            ast_patterns=["function_def", "class_def"],
            regex_patterns=[r"def\s+\w+\s*\(", r"class\s+\w+"],
            breaking_indicators=["signature_change", "removal"],
            safe_indicators=["comment_change", "formatting"],
            weight=1.5,
            confidence_threshold=0.8,
        )

        assert pattern.pattern_id == "test_pattern"
        assert pattern.name == "Test Pattern"
        assert pattern.description == "A test pattern for validation"
        assert pattern.language == LanguageType.PYTHON
        assert len(pattern.file_patterns) == 2
        assert len(pattern.ast_patterns) == 2
        assert len(pattern.regex_patterns) == 2
        assert len(pattern.breaking_indicators) == 2
        assert len(pattern.safe_indicators) == 2
        assert pattern.weight == 1.5
        assert pattern.confidence_threshold == 0.8

        print("✅ Change pattern creation test passed")
        return True

    except Exception as e:
        print(f"❌ Change pattern creation test failed: {e}")
        return False


def test_change_signature_creation():
    """Test ChangeSignature creation"""
    try:
        from app.models.ast_models import SymbolType
        from app.services.change_classifier import ChangeSignature

        # Test signature creation
        signature = ChangeSignature(
            symbol_id="symbol_123",
            symbol_name="test_function",
            symbol_type=SymbolType.FUNCTION,
            old_signature="def test_function(a, b)",
            new_signature="def test_function(a, b, c=None)",
            visibility_old="public",
            visibility_new="public",
            parameters_old=["a", "b"],
            parameters_new=["a", "b", "c=None"],
            return_type_old="int",
            return_type_new="Optional[int]",
            inheritance_old=["BaseClass"],
            inheritance_new=["BaseClass", "Mixin"],
        )

        assert signature.symbol_id == "symbol_123"
        assert signature.symbol_name == "test_function"
        assert signature.symbol_type == SymbolType.FUNCTION
        assert signature.old_signature == "def test_function(a, b)"
        assert signature.new_signature == "def test_function(a, b, c=None)"
        assert len(signature.parameters_old) == 2
        assert len(signature.parameters_new) == 3
        assert signature.return_type_old == "int"
        assert signature.return_type_new == "Optional[int]"
        assert len(signature.inheritance_old) == 1
        assert len(signature.inheritance_new) == 2

        print("✅ Change signature creation test passed")
        return True

    except Exception as e:
        print(f"❌ Change signature creation test failed: {e}")
        return False


def test_change_classification_creation():
    """Test ChangeClassification creation"""
    try:
        from app.models.monitoring_models import ChangeType
        from app.services.change_classifier import (
            BreakingChangeType,
            ChangeCategory,
            ChangeClassification,
            ChangeRisk,
            CompatibilityLevel,
        )

        # Test classification creation
        classification = ChangeClassification(
            change_id="change_123",
            file_path="/test/file.py",
            change_type=ChangeType.MODIFIED,
            category=ChangeCategory.API_CHANGE,
            risk_level=ChangeRisk.HIGH_RISK,
            compatibility=CompatibilityLevel.POTENTIALLY_BREAKING,
        )

        # Add details
        classification.breaking_changes = [BreakingChangeType.SIGNATURE_CHANGE]
        classification.confidence_score = 0.85
        classification.reasons = ["Function signature modified", "Public API change"]
        classification.affected_symbols = ["function_a", "function_b"]
        classification.migration_suggestions = [
            "Update function calls",
            "Add parameter validation",
        ]

        assert classification.change_id == "change_123"
        assert classification.file_path == "/test/file.py"
        assert classification.change_type == ChangeType.MODIFIED
        assert classification.category == ChangeCategory.API_CHANGE
        assert classification.risk_level == ChangeRisk.HIGH_RISK
        assert classification.compatibility == CompatibilityLevel.POTENTIALLY_BREAKING
        assert len(classification.breaking_changes) == 1
        assert classification.confidence_score == 0.85
        assert len(classification.reasons) == 2
        assert len(classification.affected_symbols) == 2
        assert len(classification.migration_suggestions) == 2
        assert isinstance(classification.analysis_timestamp, datetime)

        print("✅ Change classification creation test passed")
        return True

    except Exception as e:
        print(f"❌ Change classification creation test failed: {e}")
        return False


def test_classification_rule_creation():
    """Test ClassificationRule creation"""
    try:
        from app.services.change_classifier import (
            BreakingChangeType,
            ChangeRisk,
            ClassificationRule,
        )

        # Test rule creation
        rule = ClassificationRule(
            rule_id="public_function_deletion",
            name="Public Function Deletion",
            description="Detects deletion of public functions",
            conditions=[
                "change_type == DELETED",
                "symbol_type == FUNCTION",
                "visibility == public",
            ],
            classification=ChangeRisk.BREAKING,
            breaking_types=[BreakingChangeType.REMOVAL],
            confidence=0.95,
            priority=10,
        )

        assert rule.rule_id == "public_function_deletion"
        assert rule.name == "Public Function Deletion"
        assert rule.description == "Detects deletion of public functions"
        assert len(rule.conditions) == 3
        assert rule.classification == ChangeRisk.BREAKING
        assert len(rule.breaking_types) == 1
        assert rule.breaking_types[0] == BreakingChangeType.REMOVAL
        assert rule.confidence == 0.95
        assert rule.priority == 10

        print("✅ Classification rule creation test passed")
        return True

    except Exception as e:
        print(f"❌ Classification rule creation test failed: {e}")
        return False


def test_change_metrics_creation():
    """Test ChangeMetrics creation"""
    try:
        from app.services.change_classifier import ChangeMetrics

        # Test metrics creation
        metrics = ChangeMetrics(
            total_changes=100,
            breaking_changes=15,
            safe_changes=70,
            uncertain_changes=15,
            false_positives=2,
            false_negatives=3,
            accuracy=0.95,
            precision=0.88,
            recall=0.83,
        )

        assert metrics.total_changes == 100
        assert metrics.breaking_changes == 15
        assert metrics.safe_changes == 70
        assert metrics.uncertain_changes == 15
        assert metrics.false_positives == 2
        assert metrics.false_negatives == 3
        assert metrics.accuracy == 0.95
        assert metrics.precision == 0.88
        assert metrics.recall == 0.83

        print("✅ Change metrics creation test passed")
        return True

    except Exception as e:
        print(f"❌ Change metrics creation test failed: {e}")
        return False


async def test_classifier_initialization():
    """Test change classifier initialization"""
    try:
        from app.services.change_classifier import ChangeClassifier

        classifier = ChangeClassifier()

        # Test initial state
        assert len(classifier.patterns) > 0  # Should have built-in patterns
        assert len(classifier.rules) > 0  # Should have built-in rules
        assert len(classifier.classifications) == 0
        assert len(classifier.classification_cache) == 0
        assert len(classifier.training_data) == 0

        # Test configuration
        assert classifier.confidence_threshold == 0.7
        assert classifier.breaking_change_threshold == 0.8
        assert classifier.max_cache_size == 1000

        # Test metrics
        assert classifier.metrics.total_changes == 0
        assert classifier.metrics.breaking_changes == 0
        assert classifier.metrics.safe_changes == 0

        # Test initialization
        success = await classifier.initialize()
        assert success is True

        print("✅ Classifier initialization test passed")
        return True

    except Exception as e:
        print(f"❌ Classifier initialization test failed: {e}")
        return False


async def test_basic_change_classification():
    """Test basic change classification"""
    try:
        from app.models.monitoring_models import ChangeType, FileChange
        from app.services.change_classifier import ChangeClassifier

        classifier = ChangeClassifier()
        await classifier.initialize()

        # Test code file modification
        change = FileChange(
            id="test_change_1",
            file_path="/project/src/main.py",
            change_type=ChangeType.MODIFIED,
            timestamp=datetime.now(),
        )

        classification = await classifier.classify_change(change)

        assert classification.change_id == "test_change_1"
        assert classification.file_path == "/project/src/main.py"
        assert classification.change_type == ChangeType.MODIFIED
        assert classification.risk_level is not None
        assert classification.compatibility is not None
        assert classification.confidence_score >= 0.0
        assert len(classification.reasons) > 0

        print("✅ Basic change classification test passed")
        return True

    except Exception as e:
        print(f"❌ Basic change classification test failed: {e}")
        return False


async def test_file_deletion_classification():
    """Test classification of file deletions"""
    try:
        from app.models.monitoring_models import ChangeType, FileChange
        from app.services.change_classifier import ChangeClassifier, ChangeRisk

        classifier = ChangeClassifier()
        await classifier.initialize()

        # Test API file deletion
        change = FileChange(
            id="test_deletion",
            file_path="/project/api/user_service.py",
            change_type=ChangeType.DELETED,
            timestamp=datetime.now(),
        )

        classification = await classifier.classify_change(change)

        assert classification.change_type == ChangeType.DELETED
        assert classification.risk_level in [ChangeRisk.HIGH_RISK, ChangeRisk.BREAKING]
        assert "deletion" in classification.reasons[0].lower()

        print("✅ File deletion classification test passed")
        return True

    except Exception as e:
        print(f"❌ File deletion classification test failed: {e}")
        return False


async def test_file_creation_classification():
    """Test classification of file creation"""
    try:
        from app.models.monitoring_models import ChangeType, FileChange
        from app.services.change_classifier import ChangeClassifier, ChangeRisk

        classifier = ChangeClassifier()
        await classifier.initialize()

        # Test new file creation
        change = FileChange(
            id="test_creation",
            file_path="/project/src/new_feature.py",
            change_type=ChangeType.CREATED,
            timestamp=datetime.now(),
        )

        classification = await classifier.classify_change(
            change, new_content="def new_function(): pass"
        )

        assert classification.change_type == ChangeType.CREATED
        assert classification.risk_level == ChangeRisk.SAFE
        assert classification.confidence_score >= 0.8

        print("✅ File creation classification test passed")
        return True

    except Exception as e:
        print(f"❌ File creation classification test failed: {e}")
        return False


async def test_non_code_file_classification():
    """Test classification of non-code files"""
    try:
        from app.models.monitoring_models import ChangeType, FileChange
        from app.services.change_classifier import (
            ChangeCategory,
            ChangeClassifier,
            ChangeRisk,
        )

        classifier = ChangeClassifier()
        await classifier.initialize()

        # Test documentation file
        doc_change = FileChange(
            id="test_doc",
            file_path="/project/README.md",
            change_type=ChangeType.MODIFIED,
            timestamp=datetime.now(),
        )

        classification = await classifier.classify_change(doc_change)

        assert classification.category == ChangeCategory.DOCUMENTATION_CHANGE
        assert classification.risk_level == ChangeRisk.SAFE
        assert classification.confidence_score >= 0.8

        # Test config file
        config_change = FileChange(
            id="test_config",
            file_path="/project/package.json",
            change_type=ChangeType.MODIFIED,
            timestamp=datetime.now(),
        )

        config_classification = await classifier.classify_change(config_change)

        assert config_classification.category == ChangeCategory.BUILD_CHANGE

        print("✅ Non-code file classification test passed")
        return True

    except Exception as e:
        print(f"❌ Non-code file classification test failed: {e}")
        return False


async def test_batch_classification():
    """Test batch change classification"""
    try:
        from app.models.monitoring_models import ChangeType, FileChange
        from app.services.change_classifier import ChangeClassifier

        classifier = ChangeClassifier()
        await classifier.initialize()

        # Create multiple changes
        changes = [
            FileChange(
                id=f"change_{i}",
                file_path=f"/project/file_{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(5)
        ]

        classifications = await classifier.classify_batch_changes(changes)

        assert len(classifications) == 5
        for i, classification in enumerate(classifications):
            assert classification.change_id == f"change_{i}"
            assert classification.file_path == f"/project/file_{i}.py"
            assert classification.risk_level is not None

        print("✅ Batch classification test passed")
        return True

    except Exception as e:
        print(f"❌ Batch classification test failed: {e}")
        return False


async def test_symbol_breaking_change_analysis():
    """Test symbol breaking change analysis"""
    try:
        from app.models.ast_models import Symbol, SymbolType
        from app.services.change_classifier import BreakingChangeType, ChangeClassifier

        classifier = ChangeClassifier()

        # Create old and new symbol versions
        old_symbol = Symbol(
            id="symbol_1",
            name="test_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="/test/file.py",
            line_start=10,
            line_end=15,
            column_start=0,
            column_end=10,
            signature="def test_function(a, b)",
        )

        new_symbol = Symbol(
            id="symbol_1",
            name="test_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="/test/file.py",
            line_start=10,
            line_end=15,
            column_start=0,
            column_end=10,
            signature="def test_function(a)",  # Parameter removed
        )

        breaking_changes = await classifier.analyze_breaking_changes(
            old_symbol, new_symbol
        )

        assert BreakingChangeType.SIGNATURE_CHANGE in breaking_changes

        print("✅ Symbol breaking change analysis test passed")
        return True

    except Exception as e:
        print(f"❌ Symbol breaking change analysis test failed: {e}")
        return False


def test_classification_summary():
    """Test classification summary generation"""
    try:
        from app.models.monitoring_models import ChangeType
        from app.services.change_classifier import (
            ChangeCategory,
            ChangeClassification,
            ChangeClassifier,
            ChangeRisk,
        )

        classifier = ChangeClassifier()

        # Create test classifications
        classifications = [
            ChangeClassification(
                change_id=f"change_{i}",
                file_path=f"/test/file_{i}.py",
                change_type=ChangeType.MODIFIED,
                category=ChangeCategory.IMPLEMENTATION_CHANGE,
                risk_level=ChangeRisk.SAFE if i < 3 else ChangeRisk.HIGH_RISK,
                compatibility=None,
                confidence_score=0.8 + (i * 0.02),
            )
            for i in range(5)
        ]

        summary = classifier.get_classification_summary(classifications)

        assert summary["total_changes"] == 5
        assert summary["safe_changes"] == 3
        assert summary["breaking_changes"] == 2  # HIGH_RISK counted as breaking
        assert summary["average_confidence"] > 0.8
        assert "risk_distribution" in summary
        assert "category_distribution" in summary

        print("✅ Classification summary test passed")
        return True

    except Exception as e:
        print(f"❌ Classification summary test failed: {e}")
        return False


def test_file_type_detection():
    """Test file type detection methods"""
    try:
        from app.services.change_classifier import ChangeClassifier

        classifier = ChangeClassifier()

        # Test code file detection
        assert classifier._is_code_file("/test/app.py") is True
        assert classifier._is_code_file("/test/component.js") is True
        assert classifier._is_code_file("/test/service.ts") is True
        assert classifier._is_code_file("/test/README.md") is False
        assert classifier._is_code_file("/test/config.json") is False

        # Test category determination
        from app.models.monitoring_models import ChangeType, FileChange
        from app.services.change_classifier import ChangeCategory

        doc_change = FileChange(
            id="doc",
            file_path="/test/README.md",
            change_type=ChangeType.MODIFIED,
            timestamp=datetime.now(),
        )
        assert (
            classifier._determine_category(doc_change)
            == ChangeCategory.DOCUMENTATION_CHANGE
        )

        test_change = FileChange(
            id="test",
            file_path="/test/test_app.py",
            change_type=ChangeType.MODIFIED,
            timestamp=datetime.now(),
        )
        assert classifier._determine_category(test_change) == ChangeCategory.TEST_CHANGE

        config_change = FileChange(
            id="config",
            file_path="/test/package.json",
            change_type=ChangeType.MODIFIED,
            timestamp=datetime.now(),
        )
        assert (
            classifier._determine_category(config_change) == ChangeCategory.BUILD_CHANGE
        )

        print("✅ File type detection test passed")
        return True

    except Exception as e:
        print(f"❌ File type detection test failed: {e}")
        return False


def test_classifier_metrics():
    """Test classifier metrics tracking"""
    try:
        from app.services.change_classifier import ChangeClassifier

        classifier = ChangeClassifier()

        # Get initial metrics
        metrics = classifier.get_metrics()

        assert "total_changes" in metrics
        assert "breaking_changes" in metrics
        assert "safe_changes" in metrics
        assert "uncertain_changes" in metrics
        assert "accuracy" in metrics
        assert "patterns_loaded" in metrics
        assert "rules_loaded" in metrics
        assert "cache_size" in metrics
        assert "confidence_threshold" in metrics

        # Should have loaded patterns and rules
        assert metrics["patterns_loaded"] > 0
        assert metrics["rules_loaded"] > 0
        assert metrics["confidence_threshold"] == 0.7

        print("✅ Classifier metrics test passed")
        return True

    except Exception as e:
        print(f"❌ Classifier metrics test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running Change Classifier Tests...")
    print()

    # Sync tests
    sync_tests = [
        ("Change Classifier Imports", test_change_classifier_imports),
        ("Breaking Change Type Enums", test_breaking_change_type_enums),
        ("Change Category Enums", test_change_category_enums),
        ("Change Risk Enums", test_change_risk_enums),
        ("Compatibility Level Enums", test_compatibility_level_enums),
        ("Change Pattern Creation", test_change_pattern_creation),
        ("Change Signature Creation", test_change_signature_creation),
        ("Change Classification Creation", test_change_classification_creation),
        ("Classification Rule Creation", test_classification_rule_creation),
        ("Change Metrics Creation", test_change_metrics_creation),
        ("Classification Summary", test_classification_summary),
        ("File Type Detection", test_file_type_detection),
        ("Classifier Metrics", test_classifier_metrics),
    ]

    # Async tests
    async_tests = [
        ("Classifier Initialization", test_classifier_initialization),
        ("Basic Change Classification", test_basic_change_classification),
        ("File Deletion Classification", test_file_deletion_classification),
        ("File Creation Classification", test_file_creation_classification),
        ("Non-Code File Classification", test_non_code_file_classification),
        ("Batch Classification", test_batch_classification),
        ("Symbol Breaking Change Analysis", test_symbol_breaking_change_analysis),
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
        print("🎉 All change classifier tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed or had issues")
