"""
Comprehensive test suite for Enhanced NLP Service

Tests cover:
- Intent recognition accuracy
- Parameter extraction functionality  
- Fuzzy matching capabilities
- Context awareness
- Performance characteristics
- Edge cases and error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
import time

from app.services.enhanced_nlp_service import (
    EnhancedNLPService, 
    CommandIntent, 
    CommandParameter, 
    NLPCommand
)


class TestEnhancedNLPService:
    """Test suite for Enhanced NLP Service functionality"""

    @pytest.fixture
    def nlp_service(self):
        """Create NLP service instance for testing"""
        return EnhancedNLPService()

    @pytest.fixture
    def sample_context(self):
        """Sample context for testing"""
        return {
            "current_file": "test.py",
            "current_directory": "/home/user/project",
            "task_context": True,
            "voice_active": True
        }

    def test_initialization(self, nlp_service):
        """Test service initializes correctly"""
        assert nlp_service.is_initialized
        assert nlp_service.intent_patterns
        assert nlp_service.action_mappings
        assert nlp_service.parameter_extractors
        assert isinstance(nlp_service.context_history, list)
        assert isinstance(nlp_service.command_cache, dict)

    # INTENT RECOGNITION TESTS
    
    def test_system_status_intent_recognition(self, nlp_service):
        """Test system status intent recognition"""
        test_cases = [
            "show me the system status",
            "what is the status",
            "how is everything running",
            "is the system working",
            "check system health"
        ]
        
        for text in test_cases:
            result = nlp_service.process_command(text)
            assert result.intent == CommandIntent.SYSTEM_STATUS
            assert result.confidence > 0.7
            assert result.original_text == text

    def test_file_operations_intent_recognition(self, nlp_service):
        """Test file operations intent recognition"""
        test_cases = [
            "list files in current directory",
            "show me the files",
            "open file test.py",
            "create new file",
            "delete old files"
        ]
        
        for text in test_cases:
            result = nlp_service.process_command(text)
            assert result.intent == CommandIntent.FILE_OPERATIONS
            assert result.confidence > 0.7

    def test_project_navigation_intent_recognition(self, nlp_service):
        """Test project navigation intent recognition"""
        test_cases = [
            "go to the project directory",
            "navigate to home folder",
            "change directory to src",
            "where am i currently",
            "show current location"
        ]
        
        for text in test_cases:
            result = nlp_service.process_command(text)
            assert result.intent == CommandIntent.PROJECT_NAVIGATION
            assert result.confidence > 0.7

    def test_code_analysis_intent_recognition(self, nlp_service):
        """Test code analysis intent recognition"""
        test_cases = [
            "analyze this code file",
            "review the function implementation", 
            "check for bugs in the code",
            "explain what this function does",
            "find issues in the project"
        ]
        
        for text in test_cases:
            result = nlp_service.process_command(text)
            assert result.intent == CommandIntent.CODE_ANALYSIS
            assert result.confidence > 0.7

    def test_task_management_intent_recognition(self, nlp_service):
        """Test task management intent recognition"""
        test_cases = [
            "create new task for testing",
            "list all my tasks",
            "mark task as complete",
            "add task to backlog",
            "finish this task"
        ]
        
        for text in test_cases:
            result = nlp_service.process_command(text)
            assert result.intent == CommandIntent.TASK_MANAGEMENT
            assert result.confidence > 0.7

    def test_voice_control_intent_recognition(self, nlp_service):
        """Test voice control intent recognition"""
        test_cases = [
            "activate voice control",
            "change volume to 50",
            "mute the voice feedback",
            "listen to my commands",
            "turn up the volume"
        ]
        
        for text in test_cases:
            result = nlp_service.process_command(text)
            assert result.intent == CommandIntent.VOICE_CONTROL
            assert result.confidence > 0.7

    def test_help_intent_recognition(self, nlp_service):
        """Test help intent recognition"""
        test_cases = [
            "help me with commands",
            "what can you do",
            "show available options",
            "need assistance",
            "how do i use this"
        ]
        
        for text in test_cases:
            result = nlp_service.process_command(text)
            assert result.intent == CommandIntent.HELP
            assert result.confidence > 0.7

    # ACTION EXTRACTION TESTS

    def test_file_operations_action_extraction(self, nlp_service):
        """Test action extraction for file operations"""
        test_cases = [
            ("list all files", "list"),
            ("open the readme file", "open"),
            ("create new document", "create"),
            ("delete old logs", "delete"),
            ("copy this file", "copy")
        ]
        
        for text, expected_action in test_cases:
            result = nlp_service.process_command(text)
            assert result.intent == CommandIntent.FILE_OPERATIONS
            assert result.action == expected_action

    def test_task_management_action_extraction(self, nlp_service):
        """Test action extraction for task management"""
        test_cases = [
            ("create task for code review", "create"),
            ("list my current tasks", "list"),
            ("update task priority", "update"),
            ("complete this task", "complete"),
            ("remove finished task", "delete")
        ]
        
        for text, expected_action in test_cases:
            result = nlp_service.process_command(text)
            assert result.intent == CommandIntent.TASK_MANAGEMENT
            assert result.action == expected_action

    # PARAMETER EXTRACTION TESTS

    def test_filename_parameter_extraction(self, nlp_service):
        """Test filename parameter extraction"""
        test_cases = [
            ("open file test.py", "test.py"),
            ("analyze 'main.js' for issues", "main.js"),
            ('read file "config.json"', "config.json"),
            ("review the app.swift file", "app.swift")
        ]
        
        for text, expected_filename in test_cases:
            result = nlp_service.process_command(text)
            filename_params = [p for p in result.parameters if p.name == "filename"]
            assert len(filename_params) > 0
            assert filename_params[0].value == expected_filename
            assert filename_params[0].type == "file"

    def test_directory_parameter_extraction(self, nlp_service):
        """Test directory parameter extraction"""
        test_cases = [
            ("navigate to /home/user/project", "/home/user/project"),
            ("go to directory src/main", "src/main"),
            ("change to folder C:\\Users\\test", "C:\\Users\\test")
        ]
        
        for text, expected_directory in test_cases:
            result = nlp_service.process_command(text)
            dir_params = [p for p in result.parameters if p.name in ["directory", "path"]]
            assert len(dir_params) > 0
            assert dir_params[0].value == expected_directory
            assert dir_params[0].type == "directory"

    def test_task_text_parameter_extraction(self, nlp_service):
        """Test task text parameter extraction"""
        test_cases = [
            ('create task "Implement user authentication"', "Implement user authentication"),
            ("add new task for code review", "code review"),
            ("create task called database optimization", "database optimization")
        ]
        
        for text, expected_text in test_cases:
            result = nlp_service.process_command(text)
            task_params = [p for p in result.parameters if p.name == "task_text"]
            assert len(task_params) > 0
            assert expected_text.lower() in task_params[0].value.lower()
            assert task_params[0].type == "text"

    def test_volume_level_parameter_extraction(self, nlp_service):
        """Test volume level parameter extraction"""
        test_cases = [
            ("set volume to 75", "75"),
            ("mute the voice", "0"),
            ("make it loud", "100"),
            ("turn volume quiet", "25")
        ]
        
        for text, expected_volume in test_cases:
            result = nlp_service.process_command(text)
            volume_params = [p for p in result.parameters if p.name == "volume_level"]
            assert len(volume_params) > 0
            assert volume_params[0].value == expected_volume
            assert volume_params[0].type == "number"

    def test_function_name_parameter_extraction(self, nlp_service):
        """Test function name parameter extraction"""
        test_cases = [
            ("explain function getUserById", "getUserById"),
            ("analyze method calculateTotal", "calculateTotal"), 
            ("review def processData function", "processData")
        ]
        
        for text, expected_function in test_cases:
            result = nlp_service.process_command(text)
            func_params = [p for p in result.parameters if p.name == "function_name"]
            assert len(func_params) > 0
            assert func_params[0].value == expected_function
            assert func_params[0].type == "text"

    def test_priority_parameter_extraction(self, nlp_service):
        """Test priority parameter extraction"""
        test_cases = [
            ("create urgent task for bug fix", "urgent"),
            ("add high priority item", "high"),
            ("normal priority task", "medium"),
            ("low importance task", "low")
        ]
        
        for text, expected_priority in test_cases:
            result = nlp_service.process_command(text)
            priority_params = [p for p in result.parameters if p.name == "priority"]
            assert len(priority_params) > 0
            assert priority_params[0].value == expected_priority
            assert priority_params[0].type == "text"

    # FUZZY MATCHING TESTS

    def test_fuzzy_intent_matching(self, nlp_service):
        """Test fuzzy matching for partial intent recognition"""
        test_cases = [
            ("stat system", CommandIntent.SYSTEM_STATUS),
            ("fil list", CommandIntent.FILE_OPERATIONS),
            ("navigat project", CommandIntent.PROJECT_NAVIGATION),
            ("analyz cod", CommandIntent.CODE_ANALYSIS),
            ("tsk manag", CommandIntent.TASK_MANAGEMENT),
            ("voic contrl", CommandIntent.VOICE_CONTROL),
            ("hlp command", CommandIntent.HELP)
        ]
        
        for text, expected_intent in test_cases:
            result = nlp_service.process_command(text)
            assert result.intent == expected_intent
            # Fuzzy matching should have lower confidence
            assert 0.3 <= result.confidence <= 0.8

    def test_fuzzy_matching_with_typos(self, nlp_service):
        """Test fuzzy matching with common typos"""
        test_cases = [
            ("show stsus", CommandIntent.SYSTEM_STATUS),
            ("lst fils", CommandIntent.FILE_OPERATIONS),
            ("navig project", CommandIntent.PROJECT_NAVIGATION),
            ("analze code", CommandIntent.CODE_ANALYSIS)
        ]
        
        for text, expected_intent in test_cases:
            result = nlp_service.process_command(text)
            assert result.intent == expected_intent
            assert result.confidence > 0.3

    # CONTEXT AWARENESS TESTS

    def test_context_awareness_file_operations(self, nlp_service, sample_context):
        """Test context awareness for file operations"""
        # Context should boost confidence for file operations
        result_with_context = nlp_service.process_command("analyze this file", sample_context)
        result_without_context = nlp_service.process_command("analyze this file")
        
        assert result_with_context.intent == CommandIntent.CODE_ANALYSIS
        assert result_without_context.intent == CommandIntent.CODE_ANALYSIS
        # Context should increase confidence
        assert result_with_context.confidence >= result_without_context.confidence

    def test_context_current_file_extraction(self, nlp_service, sample_context):
        """Test extraction of current file from context"""
        result = nlp_service.process_command("analyze current file", sample_context)
        assert result.intent == CommandIntent.CODE_ANALYSIS
        
        # Should extract current file from context
        filename_params = [p for p in result.parameters if p.name == "filename"]
        assert len(filename_params) > 0
        assert filename_params[0].value == "test.py"

    def test_context_task_management_boost(self, nlp_service, sample_context):
        """Test context boost for task management"""
        result = nlp_service.process_command("create something", sample_context)
        # With task context, should prefer task management
        assert result.intent == CommandIntent.TASK_MANAGEMENT

    def test_context_voice_control_boost(self, nlp_service, sample_context):
        """Test context boost for voice control when voice is active"""
        result = nlp_service.process_command("change volume", sample_context)
        assert result.intent == CommandIntent.VOICE_CONTROL
        # Voice context should boost confidence
        assert result.confidence > 0.8

    # PERFORMANCE AND CACHING TESTS

    def test_command_caching(self, nlp_service):
        """Test command result caching for performance"""
        command_text = "show system status please"
        
        # First call - no cache
        start_time = time.time()
        result1 = nlp_service.process_command(command_text)
        first_call_time = time.time() - start_time
        
        # Second call - should use cache
        start_time = time.time()
        result2 = nlp_service.process_command(command_text)
        second_call_time = time.time() - start_time
        
        # Results should be identical
        assert result1.intent == result2.intent
        assert result1.action == result2.action
        assert result1.confidence == result2.confidence
        
        # Second call should be faster (cached)
        assert second_call_time <= first_call_time
        
        # Check cache hit in performance stats
        metrics = nlp_service.get_performance_metrics()
        assert metrics["cache_hits"] >= 1

    def test_context_history_tracking(self, nlp_service):
        """Test context history is maintained"""
        commands = [
            "show status",
            "list files", 
            "create task"
        ]
        
        for command in commands:
            nlp_service.process_command(command)
        
        # History should contain all commands
        assert len(nlp_service.context_history) == len(commands)
        
        # Commands should be in order
        for i, command in enumerate(commands):
            assert command in nlp_service.context_history[i].original_text

    def test_performance_metrics(self, nlp_service):
        """Test performance metrics collection"""
        # Process several commands
        test_commands = [
            "show status",
            "list files",
            "create task test",
            "help me"
        ]
        
        for command in test_commands:
            nlp_service.process_command(command)
        
        metrics = nlp_service.get_performance_metrics()
        
        # Verify metrics structure
        assert "total_processed" in metrics
        assert "cache_hits" in metrics
        assert "cache_hit_ratio" in metrics
        assert "avg_processing_time" in metrics
        assert "cache_size" in metrics
        assert "history_size" in metrics
        assert "supported_intents" in metrics
        assert "supported_actions" in metrics
        assert "is_initialized" in metrics
        
        # Verify metrics values
        assert metrics["total_processed"] >= len(test_commands)
        assert metrics["avg_processing_time"] > 0
        assert metrics["is_initialized"] is True
        assert metrics["supported_intents"] > 0
        assert metrics["supported_actions"] > 0

    # COMMAND SUGGESTIONS TESTS

    def test_command_suggestions_basic(self, nlp_service):
        """Test basic command suggestions"""
        suggestions = nlp_service.get_command_suggestions("show")
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert all(isinstance(s, str) for s in suggestions)
        assert any("show" in s.lower() for s in suggestions)

    def test_command_suggestions_partial_match(self, nlp_service):
        """Test command suggestions with partial matches"""
        suggestions = nlp_service.get_command_suggestions("fil")
        
        assert len(suggestions) > 0
        # Should suggest file-related commands
        assert any("file" in s.lower() for s in suggestions)

    def test_command_suggestions_empty_input(self, nlp_service):
        """Test command suggestions with empty input"""
        suggestions = nlp_service.get_command_suggestions("")
        
        # Should return default suggestions
        assert len(suggestions) > 0
        assert len(suggestions) <= 5  # Default limit

    def test_command_suggestions_limit(self, nlp_service):
        """Test command suggestions respect limit"""
        suggestions = nlp_service.get_command_suggestions("show", limit=3)
        
        assert len(suggestions) <= 3

    # EDGE CASES AND ERROR HANDLING

    def test_empty_command_handling(self, nlp_service):
        """Test handling of empty commands"""
        result = nlp_service.process_command("")
        
        assert result.intent == CommandIntent.UNKNOWN
        assert result.confidence == 0.0
        assert result.action == "unknown"

    def test_very_long_command_handling(self, nlp_service):
        """Test handling of very long commands"""
        long_command = "show " + "very " * 100 + "long command"
        result = nlp_service.process_command(long_command)
        
        # Should still process but may have lower confidence
        assert isinstance(result, NLPCommand)
        assert result.processing_time > 0

    def test_special_characters_handling(self, nlp_service):
        """Test handling of special characters"""
        special_commands = [
            "show status @#$%",
            "list files with spaces & symbols!",
            "create task with émojis 🚀",
        ]
        
        for command in special_commands:
            result = nlp_service.process_command(command)
            assert isinstance(result, NLPCommand)
            # Should handle gracefully without errors

    def test_non_english_command_handling(self, nlp_service):
        """Test handling of non-English commands"""
        non_english_commands = [
            "mostrar estado del sistema",  # Spanish
            "liste des fichiers",          # French
            "システム状態",                    # Japanese
        ]
        
        for command in non_english_commands:
            result = nlp_service.process_command(command)
            # Should return unknown but not crash
            assert result.intent == CommandIntent.UNKNOWN
            assert result.confidence == 0.0

    def test_confidence_calculation_accuracy(self, nlp_service):
        """Test confidence calculation accuracy"""
        # High confidence commands
        high_confidence_commands = [
            "show system status",
            "list files in directory",
            "create task urgent priority"
        ]
        
        for command in high_confidence_commands:
            result = nlp_service.process_command(command)
            assert result.confidence > 0.8
        
        # Low confidence commands
        low_confidence_commands = [
            "maybe do something",
            "xyz abc def",
            "random words here"
        ]
        
        for command in low_confidence_commands:
            result = nlp_service.process_command(command)
            assert result.confidence < 0.5

    def test_canonical_form_generation(self, nlp_service):
        """Test canonical form generation"""
        result = nlp_service.process_command("create task test priority high")
        
        canonical = result.canonical_form
        assert result.intent.value in canonical
        assert result.action in canonical
        
        # Should include parameters if present
        if result.parameters:
            assert "(" in canonical and ")" in canonical

    def test_multiple_parameter_extraction(self, nlp_service):
        """Test extraction of multiple parameters from single command"""
        result = nlp_service.process_command(
            'create urgent task "Fix bug in user.py function getUserData"'
        )
        
        assert result.intent == CommandIntent.TASK_MANAGEMENT
        assert len(result.parameters) >= 2  # Should extract task text and priority
        
        param_names = [p.name for p in result.parameters]
        assert "task_text" in param_names
        assert "priority" in param_names

    def test_health_status(self, nlp_service):
        """Test health status reporting"""
        health = nlp_service.get_health_status()
        
        assert "status" in health
        assert "is_initialized" in health  
        assert "capabilities" in health
        assert "metrics" in health
        
        assert health["status"] == "healthy"
        assert health["is_initialized"] is True
        assert health["capabilities"]["intent_recognition"] is True
        assert health["capabilities"]["parameter_extraction"] is True


# INTEGRATION TESTS

class TestEnhancedNLPServiceIntegration:
    """Integration tests for Enhanced NLP Service with other components"""

    @pytest.fixture
    def nlp_service(self):
        return EnhancedNLPService()

    def test_integration_with_unified_mlx_service_structure(self, nlp_service):
        """Test NLP service integration structure matches expected interface"""
        # Test that the service provides expected methods for integration
        assert hasattr(nlp_service, 'process_command')
        assert hasattr(nlp_service, 'get_command_suggestions')
        assert hasattr(nlp_service, 'get_performance_metrics')
        assert hasattr(nlp_service, 'get_health_status')
        
        # Test return types match integration expectations
        result = nlp_service.process_command("test command")
        assert hasattr(result, 'intent')
        assert hasattr(result, 'action') 
        assert hasattr(result, 'parameters')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'canonical_form')

    def test_real_world_voice_commands(self, nlp_service):
        """Test realistic voice commands that users might speak"""
        realistic_commands = [
            "Hey, can you please show me the system status?",
            "I need to see what files are in this directory",
            "Could you help me create a task for code review?",
            "Let me check the current project directory",
            "Please analyze the main.py file for any issues",
            "Can you turn up the volume a bit?",
            "I want to mark task number 5 as completed",
            "Show me what commands are available to use"
        ]
        
        for command in realistic_commands:
            result = nlp_service.process_command(command)
            
            # Should process all realistic commands successfully
            assert result.intent != CommandIntent.UNKNOWN
            assert result.confidence > 0.5
            assert result.processing_time < 0.1  # Should be fast


# PERFORMANCE BENCHMARKS

class TestEnhancedNLPServicePerformance:
    """Performance benchmark tests for Enhanced NLP Service"""

    @pytest.fixture
    def nlp_service(self):
        return EnhancedNLPService()

    def test_processing_speed_benchmark(self, nlp_service):
        """Benchmark processing speed for typical commands"""
        test_commands = [
            "show system status",
            "list files in current directory",
            "create new task for testing", 
            "analyze code file main.py",
            "help with available commands"
        ]
        
        processing_times = []
        
        for command in test_commands:
            start_time = time.time()
            result = nlp_service.process_command(command)
            end_time = time.time()
            
            processing_time = end_time - start_time
            processing_times.append(processing_time)
            
            # Individual command should process quickly
            assert processing_time < 0.1  # 100ms max
            assert result.processing_time < 0.1
        
        # Average processing time should be very fast
        avg_time = sum(processing_times) / len(processing_times)
        assert avg_time < 0.05  # 50ms average

    def test_cache_performance_improvement(self, nlp_service):
        """Test that caching improves performance for repeated commands"""
        command = "show system status please"
        
        # Measure first call (no cache)
        first_times = []
        for _ in range(5):
            start_time = time.time()
            nlp_service.process_command(command)
            first_times.append(time.time() - start_time)
        
        # Clear the service and create new one to test caching
        nlp_service.command_cache.clear()
        
        # Process command once to populate cache
        nlp_service.process_command(command)
        
        # Measure cached calls
        cached_times = []
        for _ in range(5):
            start_time = time.time()
            nlp_service.process_command(command)
            cached_times.append(time.time() - start_time)
        
        avg_first = sum(first_times) / len(first_times)
        avg_cached = sum(cached_times) / len(cached_times)
        
        # Cached calls should be faster or equal
        assert avg_cached <= avg_first * 1.1  # Allow 10% variance

    def test_memory_usage_reasonable(self, nlp_service):
        """Test that memory usage stays reasonable under load"""
        # Process many commands to build up cache and history
        commands = [f"create task number {i}" for i in range(100)]
        
        for command in commands:
            nlp_service.process_command(command)
        
        # Cache should be limited in size
        assert len(nlp_service.command_cache) <= 100
        
        # History should be limited in size  
        assert len(nlp_service.context_history) <= 20
        
        # Performance metrics should be reasonable
        metrics = nlp_service.get_performance_metrics()
        assert metrics["cache_size"] <= 100
        assert metrics["history_size"] <= 20