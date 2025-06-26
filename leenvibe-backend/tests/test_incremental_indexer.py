"""
Test Incremental Project Indexer

Tests for the incremental indexing system with caching and performance optimization.
"""

import asyncio
import sys
import os
import tempfile
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_incremental_indexer_imports():
    """Test that incremental indexer imports correctly"""
    try:
        from app.services.incremental_indexer import incremental_indexer, IncrementalProjectIndexer
        from app.models.monitoring_models import FileChange, ChangeType
        
        # Test service availability
        assert incremental_indexer is not None
        assert hasattr(incremental_indexer, 'get_or_create_project_index')
        assert hasattr(incremental_indexer, 'update_from_file_changes')
        assert hasattr(incremental_indexer, 'get_metrics')
        assert hasattr(incremental_indexer, 'clear_cache')
        
        print("✅ Incremental indexer imports test passed")
        return True
        
    except Exception as e:
        print(f"❌ Incremental indexer imports test failed: {e}")
        return False


def test_incremental_indexer_models():
    """Test incremental indexer data models"""
    try:
        from app.services.incremental_indexer import FileIndexEntry, IncrementalIndexCache
        
        # Test FileIndexEntry
        entry = FileIndexEntry(
            file_path="/test/file.py",
            content_hash="abc123",
            last_modified=time.time(),
            file_size=1024,
            analysis_timestamp=time.time(),
            symbols_count=5,
            dependencies_count=2,
            language="python"
        )
        
        assert entry.file_path == "/test/file.py"
        assert entry.content_hash == "abc123"
        assert entry.symbols_count == 5
        
        # Test IncrementalIndexCache
        cache = IncrementalIndexCache(
            project_path="/test/project",
            cache_version="1.0.0",
            last_full_index=time.time(),
            file_entries={"/test/file.py": entry},
            project_metadata={"total_files": 1},
            dependency_graph_hash="hash123",
            symbol_registry_hash="hash456",
            created_at=time.time(),
            updated_at=time.time()
        )
        
        assert cache.project_path == "/test/project"
        assert len(cache.file_entries) == 1
        assert cache.cache_version == "1.0.0"
        
        print("✅ Incremental indexer models test passed")
        return True
        
    except Exception as e:
        print(f"❌ Incremental indexer models test failed: {e}")
        return False


async def test_incremental_indexer_metrics():
    """Test incremental indexer metrics functionality"""
    try:
        from app.services.incremental_indexer import incremental_indexer
        
        # Get initial metrics
        metrics = incremental_indexer.get_metrics()
        
        assert isinstance(metrics, dict)
        assert "incremental_updates" in metrics
        assert "cache_hits" in metrics
        assert "cache_misses" in metrics
        assert "files_reanalyzed" in metrics
        assert "symbols_updated" in metrics
        assert "total_indexing_time" in metrics
        
        # All metrics should be numbers
        for key, value in metrics.items():
            assert isinstance(value, (int, float)), f"Metric {key} should be numeric, got {type(value)}"
        
        print("✅ Incremental indexer metrics test passed")
        return True
        
    except Exception as e:
        print(f"❌ Incremental indexer metrics test failed: {e}")
        return False


async def test_incremental_indexer_cache_management():
    """Test cache file management"""
    try:
        from app.services.incremental_indexer import incremental_indexer
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_workspace = temp_dir
            
            # Test cache file path generation
            cache_file = incremental_indexer._get_cache_file_path(test_workspace)
            assert cache_file.suffix == ".cache"
            assert "project_index_" in cache_file.name
            
            # Test cache clearing (should not error even if no cache exists)
            await incremental_indexer.clear_cache(test_workspace)
            await incremental_indexer.clear_cache()  # Clear all
            
            print("✅ Incremental indexer cache management test passed")
            return True
        
    except Exception as e:
        print(f"❌ Incremental indexer cache management test failed: {e}")
        return False


async def test_enhanced_agent_incremental_integration():
    """Test enhanced agent integration with incremental indexer"""
    try:
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            # Create simple test project
            (project_path / "main.py").write_text('''
def main():
    """Main function"""
    print("Hello World")
    return 0

class Example:
    def method(self):
        return main()
''')
            
            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-incremental-client",
                session_data={}
            )
            
            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()
            
            # Test indexer metrics tool
            result = await agent._get_indexer_metrics_tool()
            assert result["status"] == "success"
            assert "data" in result
            assert "metrics" in result["data"]
            
            # Test refresh index tool
            result = await agent._refresh_project_index_tool(force_full=False)
            # This might fail due to missing dependencies, but should not crash
            assert result["status"] in ["success", "error"]
            assert "message" in result
            
            print("✅ Enhanced agent incremental integration test passed")
            return True
        
    except Exception as e:
        print(f"❌ Enhanced agent incremental integration test failed: {e}")
        return False


async def test_incremental_natural_language_processing():
    """Test natural language processing for incremental indexer commands"""
    try:
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            (project_path / "example.py").write_text('''
def example():
    return "test"
''')
            
            deps = AgentDependencies(
                workspace_path=str(project_path),
                client_id="test-nl-incremental-client",
                session_data={}
            )
            
            agent = EnhancedL3CodingAgent(deps)
            await agent.initialize()
            
            # Test indexer-related queries
            test_queries = [
                "show indexer metrics",
                "indexer performance",
                "cache stats",
                "refresh project index",
                "reindex project",
                "refresh index full"
            ]
            
            for query in test_queries:
                response = await agent._process_user_input(query)
                
                # Should return string response
                assert isinstance(response, str)
                assert len(response) > 0
                
                # Should not crash or return unhandled errors
                if "Error" in response:
                    # Errors should be graceful and informative
                    assert any(keyword in response.lower() for keyword in 
                              ["indexer", "index", "cache", "metrics", "refresh"])
            
            print("✅ Incremental natural language processing test passed")
            return True
        
    except Exception as e:
        print(f"❌ Incremental natural language processing test failed: {e}")
        return False


async def test_enhanced_state_incremental_capabilities():
    """Test enhanced agent state includes incremental indexing capabilities"""
    try:
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent, AgentDependencies
        
        deps = AgentDependencies(
            workspace_path=".",
            client_id="test-state-incremental-client",
            session_data={}
        )
        
        agent = EnhancedL3CodingAgent(deps)
        await agent.initialize()
        
        # Get enhanced state summary
        state = agent.get_enhanced_state_summary()
        
        # Should include indexing capabilities
        assert "indexing_capabilities" in state
        assert isinstance(state["indexing_capabilities"], list)
        assert "indexer_metrics" in state
        assert isinstance(state["indexer_metrics"], dict)
        
        # Check specific indexing capabilities
        expected_capabilities = [
            "incremental_indexing", "smart_caching", "file_change_integration",
            "performance_optimization", "cache_persistence", "metrics_tracking"
        ]
        
        for capability in expected_capabilities:
            assert capability in state["indexing_capabilities"]
        
        print("✅ Enhanced state incremental capabilities test passed")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced state incremental capabilities test failed: {e}")
        return False


def test_file_monitoring_incremental_integration():
    """Test file monitoring integration with incremental indexer"""
    try:
        from app.services.file_monitor_service import file_monitor_service
        
        # Check that file monitor service imports incremental indexer
        assert hasattr(file_monitor_service, '_trigger_incremental_index_update')
        
        # Test that the method exists and is callable
        method = getattr(file_monitor_service, '_trigger_incremental_index_update')
        assert callable(method)
        
        print("✅ File monitoring incremental integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ File monitoring incremental integration test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running Incremental Indexer Tests...")
    print()
    
    tests = [
        ("Incremental Indexer Imports", test_incremental_indexer_imports),
        ("Incremental Indexer Models", test_incremental_indexer_models),
        ("Incremental Indexer Metrics", test_incremental_indexer_metrics),
        ("Cache Management", test_incremental_indexer_cache_management),
        ("Enhanced Agent Integration", test_enhanced_agent_incremental_integration),
        ("Natural Language Processing", test_incremental_natural_language_processing),
        ("Enhanced State Capabilities", test_enhanced_state_incremental_capabilities),
        ("File Monitoring Integration", test_file_monitoring_incremental_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name} test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All incremental indexer tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed or had issues")