"""
Comprehensive Vector Store Service Tests

Tests for the upgraded vector store service with sentence transformers
and production-quality embeddings.
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import List
import time

from app.services.vector_store_service import (
    VectorStoreService,
    CodeEmbedding,
    SearchResult,
    SENTENCE_TRANSFORMERS_AVAILABLE,
    CHROMADB_AVAILABLE
)


@pytest.fixture
async def vector_store():
    """Create a temporary vector store for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = VectorStoreService(db_path=temp_dir)
        await service.initialize()
        yield service


@pytest.fixture
def sample_code_embeddings():
    """Create sample code embeddings for testing"""
    return [
        CodeEmbedding(
            id="test_func_1",
            content="def calculate_sum(a, b): return a + b",
            file_path="/test/utils.py",
            language="python",
            symbol_type="function",
            symbol_name="calculate_sum",
            start_line=1,
            end_line=1
        ),
        CodeEmbedding(
            id="test_class_1",
            content="class DataProcessor: def __init__(self): self.data = []",
            file_path="/test/processor.py",
            language="python",
            symbol_type="class",
            symbol_name="DataProcessor",
            start_line=1,
            end_line=2
        ),
        CodeEmbedding(
            id="test_func_2",
            content="async def fetch_data(url): return await http_client.get(url)",
            file_path="/test/api.py",
            language="python",
            symbol_type="function",
            symbol_name="fetch_data",
            start_line=5,
            end_line=5
        ),
        CodeEmbedding(
            id="test_js_func",
            content="function validateEmail(email) { return /\\S+@\\S+\\.\\S+/.test(email); }",
            file_path="/test/validation.js",
            language="javascript",
            symbol_type="function",
            symbol_name="validateEmail",
            start_line=10,
            end_line=10
        )
    ]


@pytest.mark.asyncio
async def test_vector_store_initialization(vector_store):
    """Test vector store initializes correctly"""
    assert vector_store.is_initialized
    assert vector_store.chromadb_available == CHROMADB_AVAILABLE
    assert vector_store.sentence_transformers_available == SENTENCE_TRANSFORMERS_AVAILABLE
    
    # Check embedding type
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        assert vector_store.embedding_type == "sentence_transformer"
        assert vector_store.embedding_model is not None
    else:
        assert vector_store.embedding_type == "hash"


@pytest.mark.asyncio
async def test_embedding_creation_methods(vector_store):
    """Test different embedding creation methods"""
    test_content = "def hello_world(): print('Hello, World!')"
    
    # Test general embedding creation
    embedding = vector_store._create_embedding(test_content)
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert all(isinstance(x, (int, float)) for x in embedding)
    
    # Test hash embedding specifically
    hash_embedding = vector_store._create_hash_embedding(test_content)
    assert isinstance(hash_embedding, list)
    assert len(hash_embedding) == 384  # Standard size
    
    # Test sentence transformer if available
    if vector_store.sentence_transformers_available and vector_store.embedding_model:
        st_embedding = vector_store._create_sentence_transformer_embedding(test_content)
        assert isinstance(st_embedding, list)
        assert len(st_embedding) > 0
        
        # Sentence transformer embeddings should be different from hash
        assert st_embedding != hash_embedding


@pytest.mark.asyncio
async def test_content_preprocessing(vector_store):
    """Test code content preprocessing for embeddings"""
    test_content = """
    def   complex_function(   param1,    param2   ):
        # This is a complex function with lots of whitespace
        result = param1 + param2
        return result
    """
    
    processed = vector_store._preprocess_code_for_embedding(test_content)
    
    # Should remove excessive whitespace
    assert "   " not in processed
    assert processed.count(" ") < test_content.count(" ")
    
    # Should preserve basic structure
    assert "def complex_function" in processed
    assert "param1" in processed
    assert "param2" in processed


@pytest.mark.asyncio
async def test_add_code_embeddings(vector_store, sample_code_embeddings):
    """Test adding code embeddings to the store"""
    
    for embedding in sample_code_embeddings:
        result = await vector_store.add_code_embedding(embedding)
        assert result is True
    
    # Verify embeddings were added
    stats = await vector_store.get_collection_stats()
    if vector_store.chromadb_available:
        assert stats["total_embeddings"] == len(sample_code_embeddings)
    else:
        # Mock storage
        assert len(vector_store.mock_embeddings) == len(sample_code_embeddings)


@pytest.mark.asyncio
async def test_semantic_search_quality(vector_store, sample_code_embeddings):
    """Test semantic search quality and relevance"""
    
    # Add embeddings first
    for embedding in sample_code_embeddings:
        await vector_store.add_code_embedding(embedding)
    
    # Test semantic searches
    test_queries = [
        ("sum calculation", "calculate_sum"),  # Should find calculate_sum function
        ("data processing class", "DataProcessor"),  # Should find DataProcessor class
        ("async http request", "fetch_data"),  # Should find fetch_data function
        ("email validation", "validateEmail"),  # Should find validateEmail function
    ]
    
    for query, expected_symbol in test_queries:
        results = await vector_store.search_similar_code(query, n_results=3)
        
        assert len(results) > 0, f"No results for query: {query}"
        assert isinstance(results[0], SearchResult)
        
        # Check if the expected symbol is in the top results
        found_symbols = [r.symbol_name for r in results]
        assert expected_symbol in found_symbols, f"Expected {expected_symbol} in results for '{query}', got: {found_symbols}"
        
        # Verify similarity scores
        for result in results:
            assert 0.0 <= result.similarity_score <= 1.0
            assert result.file_path.startswith("/test/")


@pytest.mark.asyncio
async def test_search_filtering(vector_store, sample_code_embeddings):
    """Test search filtering by file and symbol type"""
    
    # Add embeddings
    for embedding in sample_code_embeddings:
        await vector_store.add_code_embedding(embedding)
    
    # Test file filtering
    results = await vector_store.search_similar_code(
        "function",
        n_results=10,
        file_filter="utils.py"
    )
    
    for result in results:
        assert "utils.py" in result.file_path
    
    # Test symbol type filtering
    results = await vector_store.search_similar_code(
        "code",
        n_results=10,
        symbol_type_filter="function"
    )
    
    for result in results:
        assert result.symbol_type == "function"


@pytest.mark.asyncio
async def test_performance_benchmarks(vector_store):
    """Test performance requirements for vector operations"""
    
    # Create larger test dataset
    large_embeddings = []
    for i in range(100):
        embedding = CodeEmbedding(
            id=f"perf_test_{i}",
            content=f"def function_{i}(param): return param * {i}",
            file_path=f"/test/file_{i}.py",
            language="python",
            symbol_type="function",
            symbol_name=f"function_{i}",
            start_line=1,
            end_line=1
        )
        large_embeddings.append(embedding)
    
    # Test bulk insertion performance
    start_time = time.time()
    for embedding in large_embeddings:
        await vector_store.add_code_embedding(embedding)
    insertion_time = time.time() - start_time
    
    # Should handle 100 embeddings in reasonable time
    assert insertion_time < 30.0, f"Insertion took too long: {insertion_time}s"
    
    # Test search performance
    start_time = time.time()
    results = await vector_store.search_similar_code("function", n_results=10)
    search_time = time.time() - start_time
    
    # Search should be fast
    assert search_time < 1.0, f"Search took too long: {search_time}s"
    assert len(results) > 0


@pytest.mark.asyncio
async def test_large_codebase_handling(vector_store):
    """Test handling of large codebase scenarios"""
    
    # Create embeddings with large content
    large_content = """
    class LargeClass:
        def __init__(self):
            self.data = {}
            self.processors = []
            self.config = {
                'setting1': 'value1',
                'setting2': 'value2',
                'setting3': 'value3'
            }
        
        def process_data(self, input_data):
            for item in input_data:
                if self.validate_item(item):
                    processed = self.transform_item(item)
                    self.store_result(processed)
        
        def validate_item(self, item):
            return item is not None and hasattr(item, 'id')
        
        def transform_item(self, item):
            return {'id': item.id, 'processed': True}
        
        def store_result(self, result):
            self.data[result['id']] = result
    """ * 10  # Repeat to make it large
    
    embedding = CodeEmbedding(
        id="large_class",
        content=large_content,
        file_path="/test/large_file.py",
        language="python",
        symbol_type="class",
        symbol_name="LargeClass",
        start_line=1,
        end_line=100
    )
    
    # Should handle large content gracefully
    result = await vector_store.add_code_embedding(embedding)
    assert result is True
    
    # Should be able to search in large content
    results = await vector_store.search_similar_code("process data", n_results=1)
    assert len(results) > 0


@pytest.mark.asyncio
async def test_embedding_model_fallback(vector_store):
    """Test graceful fallback between embedding models"""
    
    # Test that embedding creation always works
    test_content = "def test_function(): pass"
    
    # Save original model
    original_model = vector_store.embedding_model
    original_type = vector_store.embedding_type
    
    try:
        # Force fallback to hash embeddings
        vector_store.embedding_model = None
        vector_store.embedding_type = "hash"
        
        hash_embedding = vector_store._create_embedding(test_content)
        assert isinstance(hash_embedding, list)
        assert len(hash_embedding) == 384
        
        # Restore original model if available
        if original_model:
            vector_store.embedding_model = original_model
            vector_store.embedding_type = original_type
            
            st_embedding = vector_store._create_embedding(test_content)
            assert isinstance(st_embedding, list)
            
            # Different methods should produce different embeddings
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                assert st_embedding != hash_embedding
    
    finally:
        # Always restore original state
        vector_store.embedding_model = original_model
        vector_store.embedding_type = original_type


@pytest.mark.asyncio
async def test_collection_statistics(vector_store, sample_code_embeddings):
    """Test collection statistics and metadata analysis"""
    
    # Add embeddings
    for embedding in sample_code_embeddings:
        await vector_store.add_code_embedding(embedding)
    
    stats = await vector_store.get_collection_stats()
    
    assert "total_embeddings" in stats
    assert "embedding_model" in stats
    assert "db_path" in stats
    
    if vector_store.chromadb_available:
        assert stats["total_embeddings"] == len(sample_code_embeddings)
        
        if "languages" in stats:
            assert "python" in stats["languages"]
            assert "javascript" in stats["languages"]
        
        if "symbol_types" in stats:
            assert "function" in stats["symbol_types"]
            assert "class" in stats["symbol_types"]


@pytest.mark.asyncio
async def test_file_embedding_operations(vector_store):
    """Test file-level embedding operations"""
    
    # Create a mock file structure for testing
    mock_code_structure = type('MockCodeStructure', (), {
        'language': 'python',
        'lines_of_code': 20,
        'symbols': [
            type('Symbol', (), {
                'name': 'test_function',
                'type': 'function',
                'parameters': ['param1', 'param2'],
                'start_line': 5,
                'end_line': 10
            })(),
            type('Symbol', (), {
                'name': 'TestClass',
                'type': 'class',
                'parameters': [],
                'start_line': 15,
                'end_line': 20
            })()
        ]
    })()
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def test_function(param1, param2):
    return param1 + param2

class TestClass:
    def __init__(self):
        pass
""")
        temp_file_path = f.name
    
    try:
        # Test adding file embeddings
        count = await vector_store.add_file_embeddings(temp_file_path, mock_code_structure)
        assert count > 0  # Should add file + symbol embeddings
        
        # Test removing file embeddings
        if vector_store.chromadb_available:
            removed_count = await vector_store.remove_file_embeddings(temp_file_path)
            assert removed_count >= 0
    
    finally:
        # Cleanup
        Path(temp_file_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_vector_store_status(vector_store):
    """Test vector store status reporting"""
    
    status = vector_store.get_status()
    
    required_fields = [
        "initialized", "chromadb_available", "db_path", 
        "collection_name", "embedding_model", "storage_mode"
    ]
    
    for field in required_fields:
        assert field in status
    
    assert status["initialized"] is True
    assert status["storage_mode"] in ["chromadb", "mock"]
    
    # Embedding model should indicate the type
    embedding_model = status["embedding_model"]
    assert ":" in embedding_model  # Should be "type:model_name"
    
    embedding_type = embedding_model.split(":")[0]
    assert embedding_type in ["sentence_transformer", "hash"]


@pytest.mark.asyncio
async def test_error_handling_and_resilience(vector_store):
    """Test error handling and system resilience"""
    
    # Test with invalid content
    invalid_embedding = CodeEmbedding(
        id="invalid_test",
        content="",  # Empty content
        file_path="",
        language="",
        symbol_type="",
        symbol_name="",
        start_line=0,
        end_line=0
    )
    
    # Should handle gracefully
    result = await vector_store.add_code_embedding(invalid_embedding)
    assert isinstance(result, bool)  # Should not crash
    
    # Test search with empty query
    results = await vector_store.search_similar_code("", n_results=5)
    assert isinstance(results, list)  # Should not crash
    
    # Test search with very long query
    long_query = "function " * 1000
    results = await vector_store.search_similar_code(long_query, n_results=1)
    assert isinstance(results, list)


@pytest.mark.skipif(not SENTENCE_TRANSFORMERS_AVAILABLE, reason="Sentence transformers not available")
@pytest.mark.asyncio
async def test_sentence_transformer_specific_features(vector_store):
    """Test features specific to sentence transformer embeddings"""
    
    if vector_store.embedding_type != "sentence_transformer":
        pytest.skip("Sentence transformers not active")
    
    # Test that sentence transformers provide better semantic understanding
    code_samples = [
        "def calculate_sum(a, b): return a + b",
        "def add_numbers(x, y): return x + y",
        "def multiply(a, b): return a * b",
        "class DatabaseConnection: pass"
    ]
    
    embeddings = []
    for code in code_samples:
        embedding = vector_store._create_sentence_transformer_embedding(code)
        embeddings.append(embedding)
    
    # The first two (both addition functions) should be more similar
    # than the first and third (addition vs multiplication)
    def cosine_similarity(v1, v2):
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude1 = sum(a * a for a in v1) ** 0.5
        magnitude2 = sum(b * b for b in v2) ** 0.5
        return dot_product / (magnitude1 * magnitude2)
    
    sim_add_add = cosine_similarity(embeddings[0], embeddings[1])
    sim_add_mult = cosine_similarity(embeddings[0], embeddings[2])
    sim_add_class = cosine_similarity(embeddings[0], embeddings[3])
    
    # Addition functions should be more similar to each other
    assert sim_add_add > sim_add_mult
    assert sim_add_add > sim_add_class


if __name__ == "__main__":
    # Run basic test
    async def run_basic_test():
        with tempfile.TemporaryDirectory() as temp_dir:
            service = VectorStoreService(db_path=temp_dir)
            await service.initialize()
            
            print(f"Vector Store Status:")
            print(f"  Initialized: {service.is_initialized}")
            print(f"  ChromaDB Available: {service.chromadb_available}")
            print(f"  Sentence Transformers Available: {service.sentence_transformers_available}")
            print(f"  Embedding Type: {service.embedding_type}")
            print(f"  Model: {service.embedding_model_name}")
            
            # Test basic embedding
            test_embedding = service._create_embedding("def hello(): print('hello')")
            print(f"  Sample Embedding Length: {len(test_embedding)}")
            print(f"  Sample Embedding Preview: {test_embedding[:5]}")
    
    asyncio.run(run_basic_test())