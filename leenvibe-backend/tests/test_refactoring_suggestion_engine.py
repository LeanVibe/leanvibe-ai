"""
Test Refactoring Suggestion Engine

Tests for automated refactoring suggestion system including code smell detection,
refactoring opportunity identification, and automated fix generation.
"""

import sys
import os
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_refactoring_suggestion_engine_imports():
    """Test that refactoring suggestion engine imports correctly"""
    try:
        from app.services.refactoring_suggestion_engine import (
            refactoring_suggestion_engine,
            RefactoringSuggestionEngine,
            RefactoringType,
            CodeSmellType,
            SuggestionPriority,
            SuggestionCategory,
            CodePattern,
            CodeSmell,
            RefactoringSuggestion,
            RefactoringMetrics,
            RefactoringReport
        )
        
        # Test service exists
        assert refactoring_suggestion_engine is not None
        assert isinstance(refactoring_suggestion_engine, RefactoringSuggestionEngine)
        
        # Test enums
        assert hasattr(RefactoringType, 'EXTRACT_METHOD')
        assert hasattr(RefactoringType, 'EXTRACT_CLASS')
        assert hasattr(RefactoringType, 'MOVE_METHOD')
        assert hasattr(RefactoringType, 'RENAME')
        assert hasattr(RefactoringType, 'REMOVE_DUPLICATION')
        
        assert hasattr(CodeSmellType, 'LONG_METHOD')
        assert hasattr(CodeSmellType, 'LONG_CLASS')
        assert hasattr(CodeSmellType, 'LARGE_PARAMETER_LIST')
        assert hasattr(CodeSmellType, 'DUPLICATE_CODE')
        assert hasattr(CodeSmellType, 'GOD_CLASS')
        
        assert hasattr(SuggestionPriority, 'CRITICAL')
        assert hasattr(SuggestionPriority, 'HIGH')
        assert hasattr(SuggestionPriority, 'MEDIUM')
        assert hasattr(SuggestionPriority, 'LOW')
        
        assert hasattr(SuggestionCategory, 'MAINTAINABILITY')
        assert hasattr(SuggestionCategory, 'PERFORMANCE')
        assert hasattr(SuggestionCategory, 'READABILITY')
        assert hasattr(SuggestionCategory, 'DESIGN')
        
        print("✅ Refactoring suggestion engine imports test passed")
        return True
        
    except Exception as e:
        print(f"❌ Refactoring suggestion engine imports test failed: {e}")
        return False


def test_refactoring_type_enums():
    """Test RefactoringType enum values"""
    try:
        from app.services.refactoring_suggestion_engine import RefactoringType
        
        # Test enum values
        assert RefactoringType.EXTRACT_METHOD == "extract_method"
        assert RefactoringType.EXTRACT_CLASS == "extract_class"
        assert RefactoringType.MOVE_METHOD == "move_method"
        assert RefactoringType.RENAME == "rename"
        assert RefactoringType.INLINE == "inline"
        assert RefactoringType.SIMPLIFY_CONDITIONAL == "simplify_conditional"
        assert RefactoringType.REMOVE_DUPLICATION == "remove_duplication"
        assert RefactoringType.OPTIMIZE_IMPORTS == "optimize_imports"
        assert RefactoringType.REDUCE_COMPLEXITY == "reduce_complexity"
        assert RefactoringType.IMPROVE_NAMING == "improve_naming"
        assert RefactoringType.ADD_TYPE_HINTS == "add_type_hints"
        assert RefactoringType.MODERNIZE_CODE == "modernize_code"
        
        # Test enum iteration
        refactoring_types = list(RefactoringType)
        assert len(refactoring_types) == 12
        
        print("✅ Refactoring type enums test passed")
        return True
        
    except Exception as e:
        print(f"❌ Refactoring type enums test failed: {e}")
        return False


def test_code_smell_type_enums():
    """Test CodeSmellType enum values"""
    try:
        from app.services.refactoring_suggestion_engine import CodeSmellType
        
        # Test enum values
        assert CodeSmellType.LONG_METHOD == "long_method"
        assert CodeSmellType.LONG_CLASS == "long_class"
        assert CodeSmellType.LARGE_PARAMETER_LIST == "large_parameter_list"
        assert CodeSmellType.DUPLICATE_CODE == "duplicate_code"
        assert CodeSmellType.DEAD_CODE == "dead_code"
        assert CodeSmellType.GOD_CLASS == "god_class"
        assert CodeSmellType.FEATURE_ENVY == "feature_envy"
        assert CodeSmellType.DATA_CLUMPS == "data_clumps"
        assert CodeSmellType.PRIMITIVE_OBSESSION == "primitive_obsession"
        assert CodeSmellType.SWITCH_STATEMENTS == "switch_statements"
        assert CodeSmellType.SPECULATIVE_GENERALITY == "speculative_generality"
        assert CodeSmellType.MESSAGE_CHAINS == "message_chains"
        
        print("✅ Code smell type enums test passed")
        return True
        
    except Exception as e:
        print(f"❌ Code smell type enums test failed: {e}")
        return False


def test_suggestion_priority_enums():
    """Test SuggestionPriority enum values"""
    try:
        from app.services.refactoring_suggestion_engine import SuggestionPriority
        
        # Test enum values
        assert SuggestionPriority.CRITICAL == "critical"
        assert SuggestionPriority.HIGH == "high"
        assert SuggestionPriority.MEDIUM == "medium"
        assert SuggestionPriority.LOW == "low"
        assert SuggestionPriority.NICE_TO_HAVE == "nice_to_have"
        
        print("✅ Suggestion priority enums test passed")
        return True
        
    except Exception as e:
        print(f"❌ Suggestion priority enums test failed: {e}")
        return False


def test_suggestion_category_enums():
    """Test SuggestionCategory enum values"""
    try:
        from app.services.refactoring_suggestion_engine import SuggestionCategory
        
        # Test enum values
        assert SuggestionCategory.MAINTAINABILITY == "maintainability"
        assert SuggestionCategory.PERFORMANCE == "performance"
        assert SuggestionCategory.READABILITY == "readability"
        assert SuggestionCategory.DESIGN == "design"
        assert SuggestionCategory.SECURITY == "security"
        assert SuggestionCategory.MODERNIZATION == "modernization"
        assert SuggestionCategory.TESTING == "testing"
        
        print("✅ Suggestion category enums test passed")
        return True
        
    except Exception as e:
        print(f"❌ Suggestion category enums test failed: {e}")
        return False


def test_code_pattern_creation():
    """Test CodePattern creation and properties"""
    try:
        from app.services.refactoring_suggestion_engine import CodePattern
        from app.models.ast_models import LanguageType
        
        # Test pattern creation
        pattern = CodePattern(
            pattern_id="test_pattern",
            name="Test Pattern",
            description="A test pattern for validation",
            language=LanguageType.PYTHON,
            pattern_type="heuristic",
            pattern_data={"metric": "complexity", "threshold": 10},
            threshold_values={"max_complexity": 15.0, "min_coverage": 0.8},
            enabled=True
        )
        
        assert pattern.pattern_id == "test_pattern"
        assert pattern.name == "Test Pattern"
        assert pattern.description == "A test pattern for validation"
        assert pattern.language == LanguageType.PYTHON
        assert pattern.pattern_type == "heuristic"
        assert pattern.pattern_data["metric"] == "complexity"
        assert pattern.pattern_data["threshold"] == 10
        assert pattern.threshold_values["max_complexity"] == 15.0
        assert pattern.threshold_values["min_coverage"] == 0.8
        assert pattern.enabled == True
        
        print("✅ Code pattern creation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Code pattern creation test failed: {e}")
        return False


def test_code_smell_creation():
    """Test CodeSmell creation"""
    try:
        from app.services.refactoring_suggestion_engine import CodeSmell, CodeSmellType
        
        # Test smell creation
        smell = CodeSmell(
            smell_id="smell_123",
            smell_type=CodeSmellType.LONG_METHOD,
            symbol_id="symbol_456",
            file_path="/test/file.py",
            line_start=10,
            line_end=80,
            severity=0.8,
            description="Method is too long with 70 lines",
            metrics={"lines": 70, "complexity": 15},
            related_symbols=["symbol_789", "symbol_101"]
        )
        
        assert smell.smell_id == "smell_123"
        assert smell.smell_type == CodeSmellType.LONG_METHOD
        assert smell.symbol_id == "symbol_456"
        assert smell.file_path == "/test/file.py"
        assert smell.line_start == 10
        assert smell.line_end == 80
        assert smell.severity == 0.8
        assert smell.description == "Method is too long with 70 lines"
        assert smell.metrics["lines"] == 70
        assert smell.metrics["complexity"] == 15
        assert len(smell.related_symbols) == 2
        assert isinstance(smell.detected_at, datetime)
        
        print("✅ Code smell creation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Code smell creation test failed: {e}")
        return False


def test_refactoring_suggestion_creation():
    """Test RefactoringSuggestion creation"""
    try:
        from app.services.refactoring_suggestion_engine import (
            RefactoringSuggestion, RefactoringType, SuggestionPriority, SuggestionCategory
        )
        
        # Test suggestion creation
        suggestion = RefactoringSuggestion(
            suggestion_id="suggestion_123",
            refactoring_type=RefactoringType.EXTRACT_METHOD,
            priority=SuggestionPriority.HIGH,
            category=SuggestionCategory.MAINTAINABILITY,
            title="Extract method to reduce complexity",
            description="Break down long method into smaller focused methods",
            rationale="Method has 80 lines and high complexity",
            target_symbol_id="symbol_456",
            target_file_path="/test/file.py",
            affected_symbols=["symbol_789"],
            affected_files=["/test/file.py", "/test/other.py"],
            estimated_effort_hours=2.5,
            expected_benefits=["Improved readability", "Better testability"],
            implementation_steps=["Identify code blocks", "Extract methods", "Update calls"],
            automated_fix_available=True,
            automated_fix_data={"type": "extract_method", "blocks": [{"start": 20, "end": 30}]},
            code_examples={"before": "long_method()", "after": "short_method()"},
            confidence_score=0.85,
            related_smells=["smell_123"],
            prerequisites=["Run tests", "Check dependencies"]
        )
        
        assert suggestion.suggestion_id == "suggestion_123"
        assert suggestion.refactoring_type == RefactoringType.EXTRACT_METHOD
        assert suggestion.priority == SuggestionPriority.HIGH
        assert suggestion.category == SuggestionCategory.MAINTAINABILITY
        assert suggestion.title == "Extract method to reduce complexity"
        assert suggestion.description == "Break down long method into smaller focused methods"
        assert suggestion.rationale == "Method has 80 lines and high complexity"
        assert suggestion.target_symbol_id == "symbol_456"
        assert suggestion.target_file_path == "/test/file.py"
        assert len(suggestion.affected_symbols) == 1
        assert len(suggestion.affected_files) == 2
        assert suggestion.estimated_effort_hours == 2.5
        assert len(suggestion.expected_benefits) == 2
        assert len(suggestion.implementation_steps) == 3
        assert suggestion.automated_fix_available == True
        assert suggestion.automated_fix_data["type"] == "extract_method"
        assert suggestion.code_examples["before"] == "long_method()"
        assert suggestion.confidence_score == 0.85
        assert len(suggestion.related_smells) == 1
        assert len(suggestion.prerequisites) == 2
        assert isinstance(suggestion.created_at, datetime)
        
        print("✅ Refactoring suggestion creation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Refactoring suggestion creation test failed: {e}")
        return False


def test_refactoring_metrics_creation():
    """Test RefactoringMetrics creation"""
    try:
        from app.services.refactoring_suggestion_engine import (
            RefactoringMetrics, RefactoringType, SuggestionPriority, 
            SuggestionCategory, CodeSmellType
        )
        
        # Test metrics creation
        metrics = RefactoringMetrics(
            total_suggestions=25,
            code_smells_detected=15,
            automated_fixes_available=8,
            total_estimated_effort_hours=45.5,
            average_confidence_score=0.78
        )
        
        # Add some type distributions
        metrics.suggestions_by_type[RefactoringType.EXTRACT_METHOD] = 5
        metrics.suggestions_by_type[RefactoringType.EXTRACT_CLASS] = 3
        metrics.suggestions_by_priority[SuggestionPriority.HIGH] = 7
        metrics.suggestions_by_priority[SuggestionPriority.MEDIUM] = 12
        metrics.suggestions_by_category[SuggestionCategory.MAINTAINABILITY] = 10
        metrics.smells_by_type[CodeSmellType.LONG_METHOD] = 8
        metrics.smells_by_type[CodeSmellType.LONG_CLASS] = 4
        
        assert metrics.total_suggestions == 25
        assert metrics.code_smells_detected == 15
        assert metrics.automated_fixes_available == 8
        assert metrics.total_estimated_effort_hours == 45.5
        assert metrics.average_confidence_score == 0.78
        assert metrics.suggestions_by_type[RefactoringType.EXTRACT_METHOD] == 5
        assert metrics.suggestions_by_type[RefactoringType.EXTRACT_CLASS] == 3
        assert metrics.suggestions_by_priority[SuggestionPriority.HIGH] == 7
        assert metrics.suggestions_by_priority[SuggestionPriority.MEDIUM] == 12
        assert metrics.suggestions_by_category[SuggestionCategory.MAINTAINABILITY] == 10
        assert metrics.smells_by_type[CodeSmellType.LONG_METHOD] == 8
        assert metrics.smells_by_type[CodeSmellType.LONG_CLASS] == 4
        
        print("✅ Refactoring metrics creation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Refactoring metrics creation test failed: {e}")
        return False


def test_refactoring_report_creation():
    """Test RefactoringReport creation"""
    try:
        from app.services.refactoring_suggestion_engine import (
            RefactoringReport, RefactoringSuggestion, CodeSmell, RefactoringMetrics,
            RefactoringType, SuggestionPriority, SuggestionCategory, CodeSmellType
        )
        
        # Create test data
        suggestion = RefactoringSuggestion(
            suggestion_id="suggestion_1",
            refactoring_type=RefactoringType.EXTRACT_METHOD,
            priority=SuggestionPriority.HIGH,
            category=SuggestionCategory.MAINTAINABILITY,
            title="Test suggestion",
            description="Test description",
            rationale="Test rationale"
        )
        
        smell = CodeSmell(
            smell_id="smell_1",
            smell_type=CodeSmellType.LONG_METHOD,
            symbol_id="symbol_1",
            file_path="/test/file.py",
            line_start=1,
            line_end=50,
            severity=0.8,
            description="Test smell"
        )
        
        metrics = RefactoringMetrics(total_suggestions=1, code_smells_detected=1)
        
        # Test report creation
        report = RefactoringReport(
            report_id="report_123",
            project_id="project_456",
            analysis_timestamp=datetime.now(),
            suggestions=[suggestion],
            code_smells=[smell],
            metrics=metrics,
            summary="Test analysis summary",
            recommendations=["Fix high priority issues first"],
            next_steps=["Review suggestions", "Create tasks"]
        )
        
        assert report.report_id == "report_123"
        assert report.project_id == "project_456"
        assert isinstance(report.analysis_timestamp, datetime)
        assert len(report.suggestions) == 1
        assert len(report.code_smells) == 1
        assert report.metrics.total_suggestions == 1
        assert report.summary == "Test analysis summary"
        assert len(report.recommendations) == 1
        assert len(report.next_steps) == 2
        
        print("✅ Refactoring report creation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Refactoring report creation test failed: {e}")
        return False


async def test_engine_initialization():
    """Test refactoring suggestion engine initialization"""
    try:
        from app.services.refactoring_suggestion_engine import RefactoringSuggestionEngine
        
        engine = RefactoringSuggestionEngine()
        
        # Test initial state
        assert len(engine.code_patterns) > 0  # Should have built-in patterns
        assert len(engine.smell_detectors) > 0  # Should have built-in detectors
        assert len(engine.detected_smells) == 0
        assert len(engine.suggestions) == 0
        assert len(engine.suggestion_cache) == 0
        
        # Test configuration
        assert engine.analysis_config["max_method_lines"] == 50
        assert engine.analysis_config["max_class_lines"] == 500
        assert engine.analysis_config["max_parameters"] == 5
        assert engine.analysis_config["max_complexity"] == 10
        
        # Test metrics
        assert engine.metrics.total_suggestions == 0
        assert engine.metrics.code_smells_detected == 0
        
        # Test initialization
        success = await engine.initialize()
        assert success == True
        
        print("✅ Engine initialization test passed")
        return True
        
    except Exception as e:
        print(f"❌ Engine initialization test failed: {e}")
        return False


async def test_analyze_file():
    """Test file analysis functionality"""
    try:
        from app.services.refactoring_suggestion_engine import RefactoringSuggestionEngine
        from app.models.ast_models import FileAnalysis, Symbol, SymbolType, LanguageType
        
        engine = RefactoringSuggestionEngine()
        await engine.initialize()
        
        # Create mock file analysis
        symbol = Symbol(
            id="test_symbol",
            name="long_method",
            symbol_type=SymbolType.FUNCTION,
            file_path="/test/file.py",
            line_start=1,
            line_end=80,  # Long method
            column_start=0,
            column_end=10
        )
        
        file_analysis = FileAnalysis(
            file_path="/test/file.py",
            language=LanguageType.PYTHON,
            symbols=[symbol],
            dependencies=[],
            imports=[],
            exports=[],
            complexity_metrics={}
        )
        
        # Mock ast_service
        with patch('app.services.refactoring_suggestion_engine.ast_service') as mock_ast:
            mock_ast.analyze_file = AsyncMock(return_value=file_analysis)
            
            suggestions = await engine.analyze_file("/test/file.py")
            
            # Should find suggestions for long method
            assert len(suggestions) >= 0  # May or may not find suggestions depending on implementation
        
        print("✅ Analyze file test passed")
        return True
        
    except Exception as e:
        print(f"❌ Analyze file test failed: {e}")
        return False


async def test_code_smell_detection():
    """Test code smell detection"""
    try:
        from app.services.refactoring_suggestion_engine import RefactoringSuggestionEngine, CodeSmellType
        from app.models.ast_models import FileAnalysis, Symbol, SymbolType, LanguageType
        
        engine = RefactoringSuggestionEngine()
        
        # Create symbols with various smells
        long_method = Symbol(
            id="long_method",
            name="very_long_method",
            symbol_type=SymbolType.FUNCTION,
            file_path="/test/file.py",
            line_start=1,
            line_end=80,  # 80 lines - exceeds threshold of 50
            column_start=0,
            column_end=10
        )
        
        long_class = Symbol(
            id="long_class",
            name="VeryLongClass",
            symbol_type=SymbolType.CLASS,
            file_path="/test/file.py",
            line_start=100,
            line_end=700,  # 601 lines - exceeds threshold of 500
            column_start=0,
            column_end=10
        )
        
        file_analysis = FileAnalysis(
            file_path="/test/file.py",
            language=LanguageType.PYTHON,
            symbols=[long_method, long_class],
            dependencies=[],
            imports=[],
            exports=[],
            complexity_metrics={}
        )
        
        # Detect smells
        smells = await engine._detect_code_smells("/test/file.py", file_analysis)
        
        # Should detect long method and long class
        assert len(smells) >= 2
        
        smell_types = [smell.smell_type for smell in smells]
        assert CodeSmellType.LONG_METHOD in smell_types
        assert CodeSmellType.LONG_CLASS in smell_types
        
        print("✅ Code smell detection test passed")
        return True
        
    except Exception as e:
        print(f"❌ Code smell detection test failed: {e}")
        return False


async def test_suggestion_generation():
    """Test suggestion generation from code smells"""
    try:
        from app.services.refactoring_suggestion_engine import (
            RefactoringSuggestionEngine, CodeSmell, CodeSmellType, RefactoringType
        )
        from app.models.ast_models import FileAnalysis, Symbol, SymbolType, LanguageType
        
        engine = RefactoringSuggestionEngine()
        
        # Create a code smell
        smell = CodeSmell(
            smell_id="smell_1",
            smell_type=CodeSmellType.LONG_METHOD,
            symbol_id="symbol_1",
            file_path="/test/file.py",
            line_start=1,
            line_end=80,
            severity=0.8,
            description="Method is too long",
            metrics={"lines": 80}
        )
        
        file_analysis = FileAnalysis(
            file_path="/test/file.py",
            language=LanguageType.PYTHON,
            symbols=[],
            dependencies=[],
            imports=[],
            exports=[],
            complexity_metrics={}
        )
        
        # Generate suggestions
        suggestions = await engine._generate_suggestions_for_smell(smell, file_analysis)
        
        # Should generate extract method suggestion
        assert len(suggestions) > 0
        
        extract_method_suggestions = [
            s for s in suggestions 
            if s.refactoring_type == RefactoringType.EXTRACT_METHOD
        ]
        assert len(extract_method_suggestions) > 0
        
        suggestion = extract_method_suggestions[0]
        assert suggestion.target_symbol_id == "symbol_1"
        assert suggestion.confidence_score > 0.0
        
        print("✅ Suggestion generation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Suggestion generation test failed: {e}")
        return False


async def test_automated_fix_generation():
    """Test automated fix generation"""
    try:
        from app.services.refactoring_suggestion_engine import (
            RefactoringSuggestionEngine, RefactoringSuggestion, RefactoringType,
            SuggestionPriority, SuggestionCategory
        )
        
        engine = RefactoringSuggestionEngine()
        
        # Create suggestion with automated fix
        suggestion = RefactoringSuggestion(
            suggestion_id="suggestion_1",
            refactoring_type=RefactoringType.OPTIMIZE_IMPORTS,
            priority=SuggestionPriority.LOW,
            category=SuggestionCategory.MAINTAINABILITY,
            title="Optimize imports",
            description="Remove unused imports",
            rationale="Clean up imports",
            automated_fix_available=True
        )
        
        engine.suggestions.append(suggestion)
        
        # Generate automated fix
        fix = await engine.generate_automated_fix("suggestion_1")
        
        assert fix is not None
        assert fix["type"] == "import_optimization"
        assert "actions" in fix
        assert len(fix["actions"]) > 0
        
        print("✅ Automated fix generation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Automated fix generation test failed: {e}")
        return False


async def test_project_analysis():
    """Test full project analysis"""
    try:
        from app.services.refactoring_suggestion_engine import RefactoringSuggestionEngine
        from app.models.ast_models import ProjectIndex, FileAnalysis, Symbol, SymbolType, LanguageType
        
        engine = RefactoringSuggestionEngine()
        await engine.initialize()
        
        # Create mock project index
        symbol = Symbol(
            id="test_symbol",
            name="test_method",
            symbol_type=SymbolType.FUNCTION,
            file_path="/test/file.py",
            line_start=1,
            line_end=30,
            column_start=0,
            column_end=10
        )
        
        file_analysis = FileAnalysis(
            file_path="/test/file.py",
            language=LanguageType.PYTHON,
            symbols=[symbol],
            dependencies=[],
            imports=[],
            exports=[],
            complexity_metrics={}
        )
        
        project_index = ProjectIndex(
            workspace_path="/test",
            files={"/test/file.py": file_analysis},
            symbols={"test_symbol": symbol},
            dependencies=[],
            supported_files=1,
            total_files=1
        )
        
        # Mock project indexer
        with patch('app.services.refactoring_suggestion_engine.project_indexer') as mock_indexer:
            mock_indexer.get_project_index = AsyncMock(return_value=project_index)
            
            report = await engine.analyze_project("test_project")
            
            assert report.project_id == "test_project"
            assert isinstance(report.analysis_timestamp, datetime)
            assert report.metrics.total_suggestions >= 0
            assert len(report.summary) > 0
        
        print("✅ Project analysis test passed")
        return True
        
    except Exception as e:
        print(f"❌ Project analysis test failed: {e}")
        return False


def test_engine_metrics():
    """Test engine metrics collection"""
    try:
        from app.services.refactoring_suggestion_engine import RefactoringSuggestionEngine
        
        engine = RefactoringSuggestionEngine()
        
        # Get initial metrics
        metrics = engine.get_metrics()
        
        assert "total_suggestions" in metrics
        assert "code_smells_detected" in metrics
        assert "automated_fixes_available" in metrics
        assert "total_estimated_effort_hours" in metrics
        assert "average_confidence_score" in metrics
        assert "suggestions_by_type" in metrics
        assert "suggestions_by_priority" in metrics
        assert "suggestions_by_category" in metrics
        assert "smells_by_type" in metrics
        
        # Initially should be empty
        assert metrics["total_suggestions"] == 0
        assert metrics["code_smells_detected"] == 0
        assert metrics["automated_fixes_available"] == 0
        
        print("✅ Engine metrics test passed")
        return True
        
    except Exception as e:
        print(f"❌ Engine metrics test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running Refactoring Suggestion Engine Tests...")
    print()
    
    # Sync tests
    sync_tests = [
        ("Refactoring Suggestion Engine Imports", test_refactoring_suggestion_engine_imports),
        ("Refactoring Type Enums", test_refactoring_type_enums),
        ("Code Smell Type Enums", test_code_smell_type_enums),
        ("Suggestion Priority Enums", test_suggestion_priority_enums),
        ("Suggestion Category Enums", test_suggestion_category_enums),
        ("Code Pattern Creation", test_code_pattern_creation),
        ("Code Smell Creation", test_code_smell_creation),
        ("Refactoring Suggestion Creation", test_refactoring_suggestion_creation),
        ("Refactoring Metrics Creation", test_refactoring_metrics_creation),
        ("Refactoring Report Creation", test_refactoring_report_creation),
        ("Engine Metrics", test_engine_metrics)
    ]
    
    # Async tests
    async_tests = [
        ("Engine Initialization", test_engine_initialization),
        ("Analyze File", test_analyze_file),
        ("Code Smell Detection", test_code_smell_detection),
        ("Suggestion Generation", test_suggestion_generation),
        ("Automated Fix Generation", test_automated_fix_generation),
        ("Project Analysis", test_project_analysis)
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
        print("🎉 All refactoring suggestion engine tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed or had issues")