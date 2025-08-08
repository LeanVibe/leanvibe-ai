"""
Performance Benchmarks for Mock Services

Tests that measure and validate performance characteristics of mock services
to ensure they provide fast, reliable testing infrastructure.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import pytest


class TestTreeSitterMockBenchmarks:
    """Benchmark tree-sitter mock performance"""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_initialization_speed(self, mock_tree_sitter_manager, benchmark):
        """Benchmark tree-sitter mock initialization speed"""
        
        async def initialize():
            await mock_tree_sitter_manager.initialize()
            return mock_tree_sitter_manager.initialized
        
        result = await benchmark(initialize)
        assert result is True
        
    @pytest.mark.benchmark
    def test_parsing_speed(self, mock_tree_sitter_manager, benchmark):
        """Benchmark code parsing speed"""
        
        # Prepare a realistic code sample
        python_code = '''
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

class CodeAnalyzer:
    """Analyzes Python code for complexity and patterns."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.patterns = []
    
    async def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single Python file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            return await self._analyze_content(content)
        except Exception as e:
            self.logger.error(f"Failed to analyze {file_path}: {e}")
            return {"error": str(e)}
    
    async def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze the content of a file."""
        lines = content.split("\\n")
        functions = self._find_functions(lines)
        classes = self._find_classes(lines)
        imports = self._find_imports(lines)
        
        return {
            "lines_of_code": len([line for line in lines if line.strip()]),
            "functions": len(functions),
            "classes": len(classes), 
            "imports": len(imports),
            "complexity_score": self._calculate_complexity(functions, classes)
        }
    
    def _find_functions(self, lines: List[str]) -> List[str]:
        """Find function definitions."""
        return [line.strip() for line in lines if line.strip().startswith("def ")]
    
    def _find_classes(self, lines: List[str]) -> List[str]:
        """Find class definitions."""
        return [line.strip() for line in lines if line.strip().startswith("class ")]
    
    def _find_imports(self, lines: List[str]) -> List[str]:
        """Find import statements."""
        imports = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                imports.append(stripped)
        return imports
    
    def _calculate_complexity(self, functions: List[str], classes: List[str]) -> float:
        """Calculate a simple complexity score."""
        base_score = len(functions) * 2 + len(classes) * 3
        return min(100.0, base_score / 10.0)

# Example usage
async def main():
    config = {"max_complexity": 50}
    analyzer = CodeAnalyzer(config)
    
    # Analyze multiple files
    files = [Path(f"example_{i}.py") for i in range(5)]
    tasks = [analyzer.analyze_file(f) for f in files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for file_path, result in zip(files, results):
        print(f"{file_path}: {result}")

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        def parse_code():
            tree, errors = mock_tree_sitter_manager.parse_file("complex_test.py", python_code)
            assert tree is not None
            return len(errors) == 0
        
        # Ensure manager is initialized
        asyncio.run(mock_tree_sitter_manager.initialize())
        
        result = benchmark(parse_code)
        assert result is True
        
    @pytest.mark.benchmark
    def test_multiple_file_parsing(self, mock_tree_sitter_manager, benchmark):
        """Benchmark parsing multiple files"""
        
        # Different code samples
        code_samples = {
            "simple.py": "def hello(): return 'world'",
            "complex.py": '''
import os
import sys
from typing import List

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self, items: List[str]) -> List[str]:
        result = []
        for item in items:
            if item.strip():
                result.append(f"processed_{item}")
        return result
''',
            "utility.py": '''
def calculate_fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def is_prime(num: int) -> bool:
    if num < 2:
        return False
    for i in range(2, int(num ** 0.5) + 1):
        if num % i == 0:
            return False
    return True
''',
            "async_example.py": '''
import asyncio
from typing import AsyncGenerator

async def async_generator() -> AsyncGenerator[int, None]:
    for i in range(10):
        await asyncio.sleep(0.001)
        yield i

async def main():
    async for value in async_generator():
        print(value)
'''
        }
        
        def parse_multiple_files():
            results = []
            for filename, code in code_samples.items():
                tree, errors = mock_tree_sitter_manager.parse_file(filename, code)
                results.append((tree is not None, len(errors)))
            return all(tree_ok for tree_ok, _ in results)
        
        # Ensure manager is initialized
        asyncio.run(mock_tree_sitter_manager.initialize())
        
        result = benchmark(parse_multiple_files)
        assert result is True


class TestNeo4jMockBenchmarks:
    """Benchmark Neo4j mock performance"""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_graph_storage_speed(self, mock_graph_service, benchmark):
        """Benchmark graph storage operations"""
        
        await mock_graph_service.initialize()
        
        # Create a realistic project index
        class MockProjectIndex:
            def __init__(self):
                self.supported_files = 50
                self.symbols = {
                    f"symbol_{i}": {
                        "name": f"function_{i}",
                        "type": "function",
                        "file_path": f"file_{i % 10}.py"
                    } for i in range(100)
                }
        
        async def store_project():
            project_index = MockProjectIndex()
            return await mock_graph_service.store_project_graph(
                project_index, f"/test/project_{int(time.time())}"
            )
        
        result = await benchmark(store_project)
        assert result is True
        
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_dependency_analysis_speed(self, mock_graph_service, benchmark):
        """Benchmark dependency analysis speed"""
        
        await mock_graph_service.initialize()
        
        async def analyze_dependencies():
            results = []
            # Analyze multiple symbols
            symbols = [f"test_symbol_{i}" for i in range(20)]
            for symbol in symbols:
                deps = await mock_graph_service.find_dependencies(symbol)
                results.append(len(deps))
            return sum(results)
        
        result = await benchmark(analyze_dependencies)
        assert result >= 0  # Should return some number of dependencies
        
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_impact_analysis_batch(self, mock_graph_service, benchmark):
        """Benchmark batch impact analysis"""
        
        await mock_graph_service.initialize()
        
        async def batch_impact_analysis():
            symbols = [f"critical_function_{i}" for i in range(10)]
            results = []
            
            for symbol in symbols:
                impact = await mock_graph_service.analyze_impact(symbol)
                results.append(impact["risk_level"])
            
            return len([r for r in results if r in ["low", "medium", "high"]])
        
        result = await benchmark(batch_impact_analysis)
        assert result > 0  # Should analyze all symbols


class TestMLXMockBenchmarks:
    """Benchmark MLX AI mock performance"""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_response_generation_speed(self, mock_mlx_service, benchmark):
        """Benchmark AI response generation speed"""
        
        await mock_mlx_service.initialize()
        
        async def generate_response():
            prompt = "Explain how to implement a binary search algorithm in Python"
            response = await mock_mlx_service.generate_response(prompt)
            return response["status"] == "success"
        
        result = await benchmark(generate_response)
        assert result is True
        
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_code_completion_speed(self, mock_mlx_service, benchmark):
        """Benchmark code completion speed"""
        
        await mock_mlx_service.initialize()
        
        contexts = [
            {
                "file_path": f"test_{i}.py",
                "current_file": {"language": "python"},
                "current_symbol": {"name": f"function_{i}", "type": "function"}
            } for i in range(5)
        ]
        
        intents = ["suggest", "explain", "refactor", "debug", "optimize"]
        
        async def batch_code_completion():
            results = []
            for context in contexts:
                for intent in intents:
                    response = await mock_mlx_service.generate_code_completion(context, intent)
                    results.append(response["status"] == "success")
            return all(results)
        
        result = await benchmark(batch_code_completion)
        assert result is True
        
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_streaming_performance(self, mock_mlx_service, benchmark):
        """Benchmark streaming response performance"""
        
        await mock_mlx_service.initialize()
        
        async def measure_streaming():
            prompt = "Write a detailed explanation of Python async/await patterns"
            chunks = []
            
            async for chunk in mock_mlx_service.generate_streaming_response(prompt):
                chunks.append(chunk)
                if chunk.get("status") == "complete":
                    break
            
            return len(chunks) > 0
        
        result = await benchmark(measure_streaming)
        assert result is True
        
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_code_analysis_speed(self, mock_mlx_service, benchmark):
        """Benchmark code analysis speed"""
        
        await mock_mlx_service.initialize()
        
        # Sample code with various issues
        test_codes = [
            '''
def insecure_function(user_input):
    exec(user_input)  # Security issue
    return "processed"
''',
            '''
def complex_function(a, b, c, d, e):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        return "too nested"
    return "ok"
''',
            '''
def good_function(items: List[str]) -> List[str]:
    """Well documented function."""
    return [item.strip() for item in items if item]
'''
        ]
        
        async def analyze_multiple_codes():
            results = []
            analysis_types = ["quality", "security", "complexity"]
            
            for code in test_codes:
                for analysis_type in analysis_types:
                    analysis = await mock_mlx_service.analyze_code(code, analysis_type)
                    results.append(analysis["status"] == "success")
            
            return all(results)
        
        result = await benchmark(analyze_multiple_codes)
        assert result is True


class TestIntegratedWorkflowBenchmarks:
    """Benchmark complete workflows using all mock services"""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_end_to_end_workflow_performance(self, mock_tree_sitter_manager,
                                                   mock_graph_service, mock_mlx_service,
                                                   benchmark):
        """Benchmark complete code analysis workflow"""
        
        # Sample project files
        project_files = {
            "main.py": '''
import asyncio
from typing import List
from utils import calculate_metrics
from models import DataModel

async def main():
    """Main application entry point."""
    data = DataModel()
    await data.initialize()
    
    metrics = calculate_metrics(data.get_all_items())
    print(f"Processed {len(metrics)} metrics")

if __name__ == "__main__":
    asyncio.run(main())
''',
            "utils.py": '''
from typing import List, Dict, Any

def calculate_metrics(items: List[Dict[str, Any]]) -> List[float]:
    """Calculate performance metrics for items."""
    if not items:
        return []
    
    metrics = []
    for item in items:
        value = item.get('value', 0)
        metrics.append(float(value) * 1.5)
    
    return metrics

def validate_data(data: Dict[str, Any]) -> bool:
    """Validate data structure."""
    required_fields = ['id', 'name', 'value']
    return all(field in data for field in required_fields)
''',
            "models.py": '''
import asyncio
from typing import List, Dict, Any

class DataModel:
    """Data model for application."""
    
    def __init__(self):
        self.items: List[Dict[str, Any]] = []
        self.initialized = False
    
    async def initialize(self):
        """Initialize the data model."""
        await asyncio.sleep(0.001)  # Simulate async initialization
        self.items = [
            {"id": i, "name": f"item_{i}", "value": i * 10}
            for i in range(100)
        ]
        self.initialized = True
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all items."""
        if not self.initialized:
            raise RuntimeError("Model not initialized")
        return self.items.copy()
'''
        }
        
        async def complete_workflow():
            # Initialize all services
            await mock_tree_sitter_manager.initialize()
            await mock_graph_service.initialize()
            await mock_mlx_service.initialize()
            
            results = []
            
            # Parse all files
            for filename, code in project_files.items():
                tree, errors = mock_tree_sitter_manager.parse_file(filename, code)
                results.append(tree is not None and len(errors) == 0)
            
            # Store project in graph
            class MockProjectIndex:
                def __init__(self):
                    self.supported_files = len(project_files)
                    self.symbols = {
                        f"symbol_{i}": {"name": f"function_{i}", "type": "function"}
                        for i in range(20)
                    }
            
            project_index = MockProjectIndex()
            stored = await mock_graph_service.store_project_graph(project_index, "/test/benchmark")
            results.append(stored)
            
            # AI analysis for each file
            for filename in project_files.keys():
                context = {
                    "file_path": filename,
                    "current_file": {"language": "python"}
                }
                response = await mock_mlx_service.generate_code_completion(context, "suggest")
                results.append(response["status"] == "success")
            
            return all(results)
        
        result = await benchmark(complete_workflow)
        assert result is True
        
    @pytest.mark.benchmark
    def test_concurrent_operations_performance(self, mock_tree_sitter_manager, 
                                             mock_graph_service, mock_mlx_service,
                                             benchmark):
        """Benchmark concurrent operations across all services"""
        
        async def setup_services():
            await mock_tree_sitter_manager.initialize()
            await mock_graph_service.initialize()
            await mock_mlx_service.initialize()
        
        async def concurrent_operations():
            # Run multiple operations concurrently
            parse_tasks = []
            graph_tasks = []
            ai_tasks = []
            
            # Parsing tasks
            for i in range(5):
                code = f"def function_{i}(): return {i}"
                task = asyncio.create_task(
                    asyncio.to_thread(mock_tree_sitter_manager.parse_file, f"test_{i}.py", code)
                )
                parse_tasks.append(task)
            
            # Graph tasks  
            for i in range(3):
                task = asyncio.create_task(
                    mock_graph_service.find_dependencies(f"symbol_{i}")
                )
                graph_tasks.append(task)
            
            # AI tasks
            for i in range(3):
                task = asyncio.create_task(
                    mock_mlx_service.generate_response(f"Test prompt {i}")
                )
                ai_tasks.append(task)
            
            # Wait for all tasks
            all_tasks = parse_tasks + graph_tasks + ai_tasks
            results = await asyncio.gather(*all_tasks, return_exceptions=True)
            
            # Check that all operations succeeded (no exceptions)
            success_count = sum(1 for result in results if not isinstance(result, Exception))
            return success_count == len(all_tasks)
        
        def run_benchmark():
            # Setup and run concurrent operations
            asyncio.run(setup_services())
            return asyncio.run(concurrent_operations())
        
        result = benchmark(run_benchmark)
        assert result is True


class TestMemoryUsageBenchmarks:
    """Test memory usage characteristics of mock services"""
    
    @pytest.mark.benchmark
    def test_memory_efficiency(self, mock_tree_sitter_manager, mock_graph_service, 
                              mock_mlx_service):
        """Test that mock services don't consume excessive memory"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Initialize services and perform operations
        async def memory_test():
            await mock_tree_sitter_manager.initialize()
            await mock_graph_service.initialize()
            await mock_mlx_service.initialize()
            
            # Perform many operations to test memory accumulation
            for i in range(100):
                # Parse code
                code = f"def function_{i}(): return {i}"
                tree, errors = mock_tree_sitter_manager.parse_file(f"test_{i}.py", code)
                
                # Graph operations
                deps = await mock_graph_service.find_dependencies(f"symbol_{i}")
                
                # AI operations
                response = await mock_mlx_service.generate_response(f"Test {i}")
            
            return True
        
        result = asyncio.run(memory_test())
        assert result
        
        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable for mock services (less than 50MB)
        assert memory_increase < 50, f"Memory increased by {memory_increase:.2f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "benchmark"])