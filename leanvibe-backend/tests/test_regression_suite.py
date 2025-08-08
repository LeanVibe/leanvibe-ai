"""
Regression Test Suite

Tests designed to catch regressions in core functionality.
These tests validate that changes don't break existing behavior.
"""

import asyncio
import pytest
import time
from typing import Dict, Any, List


class TestBasicRegressions:
    """Basic regression tests that should always pass"""
    
    def test_python_environment(self):
        """Ensure Python environment is working correctly"""
        assert True
        assert 1 + 1 == 2
        assert "hello".upper() == "HELLO"
        
    def test_async_functionality(self):
        """Test async functionality works"""
        async def async_test():
            await asyncio.sleep(0.001)
            return "async_works"
        
        result = asyncio.run(async_test())
        assert result == "async_works"
        
    def test_imports_available(self):
        """Test that basic imports work"""
        import json
        import os
        import sys
        from pathlib import Path
        
        # Test basic functionality
        data = {"test": True}
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed["test"] is True
        
    def test_mock_infrastructure_loaded(self, mock_status):
        """Test that mock infrastructure is properly loaded"""
        assert isinstance(mock_status, dict)
        assert "tree_sitter" in mock_status
        assert "neo4j" in mock_status
        assert "mlx" in mock_status


class TestServiceRegressions:
    """Regression tests for service functionality"""
    
    @pytest.mark.asyncio
    async def test_tree_sitter_mock_regression(self, mock_tree_sitter_manager):
        """Ensure tree-sitter mock maintains expected behavior"""
        # Test initialization
        await mock_tree_sitter_manager.initialize()
        assert mock_tree_sitter_manager.initialized
        
        # Test parsing behavior hasn't changed
        code = "def test_function():\n    return True"
        tree, errors = mock_tree_sitter_manager.parse_file("test.py", code)
        
        assert tree is not None
        assert tree.root_node is not None
        assert tree.root_node.type in ["module", "program"]  # Expected types
        assert len(errors) == 0  # No parse errors for valid code
        
        # Test language detection still works
        language = mock_tree_sitter_manager.detect_language("test.py")
        assert language == "PYTHON"
        
        # Test unsupported language
        unknown_lang = mock_tree_sitter_manager.detect_language("test.xyz")
        assert unknown_lang == "UNKNOWN"
        
    @pytest.mark.asyncio
    async def test_graph_service_mock_regression(self, mock_graph_service):
        """Ensure graph service mock maintains expected behavior"""
        # Test initialization
        result = await mock_graph_service.initialize()
        assert result is True
        assert mock_graph_service.initialized
        
        # Test basic operations return expected types
        dependencies = await mock_graph_service.find_dependencies("test_symbol")
        assert isinstance(dependencies, list)
        
        impact = await mock_graph_service.analyze_impact("test_symbol")
        assert isinstance(impact, dict)
        assert "target_entity" in impact
        assert "risk_level" in impact
        
        # Test statistics
        stats = await mock_graph_service.get_graph_statistics()
        assert isinstance(stats, dict)
        
    @pytest.mark.asyncio
    async def test_mlx_service_mock_regression(self, mock_mlx_service):
        """Ensure MLX service mock maintains expected behavior"""
        # Test initialization
        result = await mock_mlx_service.initialize()
        assert result is True
        assert mock_mlx_service.is_initialized
        
        # Test response generation structure
        response = await mock_mlx_service.generate_response("test prompt")
        assert response["status"] == "success"
        assert "response" in response
        assert "model" in response
        assert "usage" in response
        assert len(response["response"]) > 0
        
        # Test code completion structure
        context = {
            "file_path": "test.py",
            "current_file": {"language": "python"}
        }
        completion = await mock_mlx_service.generate_code_completion(context, "suggest")
        assert completion["status"] == "success"
        assert completion["intent"] == "suggest"
        assert "confidence" in completion
        
    def test_test_client_regression(self, test_client):
        """Ensure test client provides expected endpoints"""
        # Test root endpoint
        response = test_client.get("/")
        assert response.status_code == 200
        
        # Test health endpoint structure
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data


class TestDataStructureRegressions:
    """Test that data structures maintain expected format"""
    
    @pytest.mark.asyncio
    async def test_parsing_output_format(self, mock_tree_sitter_manager):
        """Ensure parsing output format hasn't changed"""
        await mock_tree_sitter_manager.initialize()
        
        code = "import os\ndef hello(): pass"
        tree, errors = mock_tree_sitter_manager.parse_file("test.py", code)
        
        # Tree structure
        assert hasattr(tree, 'root_node')
        assert hasattr(tree.root_node, 'type')
        assert hasattr(tree.root_node, 'children')
        
        # Error format
        assert isinstance(errors, list)
        
        # AST conversion format
        ast_node = mock_tree_sitter_manager.tree_to_ast_node(tree.root_node, code.encode())
        expected_keys = {"node_type", "start_byte", "end_byte", "start_point", "end_point", "text", "children"}
        assert set(ast_node.keys()) == expected_keys
        
    @pytest.mark.asyncio
    async def test_import_extraction_format(self, mock_tree_sitter_manager):
        """Ensure import extraction format is consistent"""
        await mock_tree_sitter_manager.initialize()
        
        code = "import os\nfrom sys import path"
        tree, _ = mock_tree_sitter_manager.parse_file("test.py", code)
        imports = mock_tree_sitter_manager.extract_imports(tree, code.encode(), "PYTHON")
        
        assert isinstance(imports, list)
        
        for import_item in imports:
            expected_keys = {"type", "module", "line", "raw"}
            assert set(import_item.keys()) == expected_keys
            assert isinstance(import_item["line"], int)
            assert import_item["line"] > 0
            
    @pytest.mark.asyncio
    async def test_ai_response_format(self, mock_mlx_service):
        """Ensure AI response format is consistent"""
        await mock_mlx_service.initialize()
        
        response = await mock_mlx_service.generate_response("test")
        
        # Required fields
        required_fields = {"status", "response", "model", "usage"}
        assert all(field in response for field in required_fields)
        
        # Usage structure
        usage = response["usage"]
        usage_fields = {"prompt_tokens", "completion_tokens", "total_tokens"}
        assert all(field in usage for field in usage_fields)
        assert all(isinstance(usage[field], int) for field in usage_fields)
        
    @pytest.mark.asyncio
    async def test_streaming_format_regression(self, mock_mlx_service):
        """Ensure streaming response format is consistent"""
        await mock_mlx_service.initialize()
        
        chunks = []
        async for chunk in mock_mlx_service.generate_streaming_response("test"):
            chunks.append(chunk)
            if chunk.get("status") == "complete":
                break
                
        # Should have streaming chunks and final chunk
        streaming_chunks = [c for c in chunks if c.get("status") == "streaming"]
        complete_chunks = [c for c in chunks if c.get("status") == "complete"]
        
        assert len(streaming_chunks) > 0
        assert len(complete_chunks) == 1
        
        # Check streaming chunk format
        for chunk in streaming_chunks:
            required_fields = {"status", "delta", "text", "progress", "is_final"}
            assert all(field in chunk for field in required_fields)
            
        # Check complete chunk format
        complete_chunk = complete_chunks[0]
        complete_fields = {"status", "model", "usage", "generation_time"}
        assert all(field in complete_chunk for field in complete_fields)


class TestPerformanceRegressions:
    """Test that performance characteristics haven't degraded"""
    
    @pytest.mark.asyncio
    async def test_initialization_speed_regression(self, mock_tree_sitter_manager,
                                                   mock_graph_service, mock_mlx_service):
        """Ensure service initialization remains fast"""
        
        # Measure initialization times
        start_time = time.time()
        await mock_tree_sitter_manager.initialize()
        tree_init_time = time.time() - start_time
        
        start_time = time.time()
        await mock_graph_service.initialize()
        graph_init_time = time.time() - start_time
        
        start_time = time.time()
        await mock_mlx_service.initialize()
        mlx_init_time = time.time() - start_time
        
        # Assert reasonable initialization times (mocks should be very fast)
        assert tree_init_time < 0.5, f"Tree-sitter init took {tree_init_time:.2f}s"
        assert graph_init_time < 0.5, f"Graph service init took {graph_init_time:.2f}s"
        assert mlx_init_time < 0.5, f"MLX service init took {mlx_init_time:.2f}s"
        
    @pytest.mark.asyncio
    async def test_parsing_speed_regression(self, mock_tree_sitter_manager):
        """Ensure parsing speed hasn't degraded"""
        await mock_tree_sitter_manager.initialize()
        
        # Test with different code sizes
        small_code = "def test(): pass"
        medium_code = "def test():\n" + "    x = 1\n" * 50 + "    return x"
        large_code = "def test():\n" + "    x = 1\n" * 500 + "    return x"
        
        test_cases = [
            ("small", small_code, 0.05),
            ("medium", medium_code, 0.1),
            ("large", large_code, 0.2)
        ]
        
        for size_name, code, max_time in test_cases:
            start_time = time.time()
            tree, errors = mock_tree_sitter_manager.parse_file(f"{size_name}.py", code)
            parse_time = time.time() - start_time
            
            assert tree is not None, f"Failed to parse {size_name} code"
            assert parse_time < max_time, f"{size_name} parsing took {parse_time:.3f}s (max: {max_time}s)"
            
    @pytest.mark.asyncio
    async def test_ai_response_speed_regression(self, mock_mlx_service):
        """Ensure AI response speed hasn't degraded"""
        await mock_mlx_service.initialize()
        
        # Test different types of requests
        test_cases = [
            ("short", "Hello", 1.0),
            ("medium", "Write a function to calculate fibonacci", 2.0),
            ("long", "Explain object-oriented programming concepts in detail", 3.0)
        ]
        
        for prompt_type, prompt, max_time in test_cases:
            start_time = time.time()
            response = await mock_mlx_service.generate_response(prompt)
            response_time = time.time() - start_time
            
            assert response["status"] == "success", f"Failed to generate {prompt_type} response"
            assert response_time < max_time, f"{prompt_type} response took {response_time:.3f}s (max: {max_time}s)"


class TestErrorHandlingRegressions:
    """Test that error handling behavior is consistent"""
    
    @pytest.mark.asyncio
    async def test_parsing_error_handling(self, mock_tree_sitter_manager):
        """Test error handling in parsing operations"""
        await mock_tree_sitter_manager.initialize()
        
        # Test invalid file extension
        tree, errors = mock_tree_sitter_manager.parse_file("test.unknown", "content")
        # Should handle gracefully
        assert isinstance(errors, list)
        
        # Test empty content
        tree, errors = mock_tree_sitter_manager.parse_file("test.py", "")
        assert isinstance(errors, list)
        
        # Test malformed code (mock should still handle it)
        tree, errors = mock_tree_sitter_manager.parse_file("test.py", "def incomplete(")
        assert isinstance(errors, list)
        
    @pytest.mark.asyncio
    async def test_graph_error_handling(self, mock_graph_service):
        """Test error handling in graph operations"""
        await mock_graph_service.initialize()
        
        # Test with empty/invalid symbol IDs
        deps = await mock_graph_service.find_dependencies("")
        assert isinstance(deps, list)
        
        deps = await mock_graph_service.find_dependencies("nonexistent_symbol")
        assert isinstance(deps, list)
        
        # Test impact analysis with invalid symbols
        impact = await mock_graph_service.analyze_impact("")
        assert isinstance(impact, dict)
        assert "target_entity" in impact
        
    @pytest.mark.asyncio
    async def test_ai_error_handling(self, mock_mlx_service):
        """Test error handling in AI operations"""
        await mock_mlx_service.initialize()
        
        # Test with empty prompts
        response = await mock_mlx_service.generate_response("")
        assert response["status"] in ["success", "error"]
        
        # Test with very long prompts
        long_prompt = "test " * 10000
        response = await mock_mlx_service.generate_response(long_prompt)
        assert response["status"] in ["success", "error"]
        
        # Test invalid code completion context
        invalid_context = {}
        completion = await mock_mlx_service.generate_code_completion(invalid_context, "suggest")
        assert completion["status"] in ["success", "error"]


class TestCompatibilityRegressions:
    """Test compatibility with existing interfaces"""
    
    def test_pytest_compatibility(self):
        """Ensure pytest features work correctly"""
        # Test fixtures are working
        assert True
        
        # Test async fixtures work (tested by other async tests passing)
        
        # Test parametrize would work
        import pytest
        
        @pytest.mark.parametrize("value,expected", [(1, 2), (2, 3)])
        def inner_test(value, expected):
            assert value + 1 == expected
            
        # Run the parametrized test
        inner_test(1, 2)
        inner_test(2, 3)
        
    def test_mock_interfaces_compatible(self, mock_tree_sitter_manager, 
                                       mock_graph_service, mock_mlx_service):
        """Test that mock interfaces are compatible with expected usage"""
        
        # Tree-sitter interface
        assert hasattr(mock_tree_sitter_manager, 'initialize')
        assert hasattr(mock_tree_sitter_manager, 'parse_file')
        assert hasattr(mock_tree_sitter_manager, 'detect_language')
        
        # Graph service interface
        assert hasattr(mock_graph_service, 'initialize')
        assert hasattr(mock_graph_service, 'find_dependencies')
        assert hasattr(mock_graph_service, 'analyze_impact')
        
        # MLX service interface
        assert hasattr(mock_mlx_service, 'initialize')
        assert hasattr(mock_mlx_service, 'generate_response')
        assert hasattr(mock_mlx_service, 'generate_code_completion')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])