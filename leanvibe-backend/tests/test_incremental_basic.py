"""
Basic Incremental Indexer Test

Simple tests for incremental indexer without external dependencies.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_incremental_indexer_basic():
    """Test basic incremental indexer functionality"""
    try:
        from app.services.incremental_indexer import (
            IncrementalProjectIndexer,
            incremental_indexer,
        )

        # Test service exists
        assert incremental_indexer is not None
        assert isinstance(incremental_indexer, IncrementalProjectIndexer)

        # Test basic methods exist
        assert hasattr(incremental_indexer, "get_or_create_project_index")
        assert hasattr(incremental_indexer, "update_from_file_changes")
        assert hasattr(incremental_indexer, "get_metrics")
        assert hasattr(incremental_indexer, "clear_cache")

        # Test metrics
        metrics = incremental_indexer.get_metrics()
        assert isinstance(metrics, dict)

        expected_metrics = [
            "incremental_updates",
            "cache_hits",
            "cache_misses",
            "files_reanalyzed",
            "symbols_updated",
            "total_indexing_time",
        ]

        for metric in expected_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))

        print("✅ Incremental indexer basic test passed")
        return True

    except Exception as e:
        print(f"❌ Incremental indexer basic test failed: {e}")
        return False


def test_incremental_indexer_models():
    """Test incremental indexer data models"""
    try:
        import time

        from app.services.incremental_indexer import (
            FileIndexEntry,
            IncrementalIndexCache,
        )

        # Test FileIndexEntry creation
        entry = FileIndexEntry(
            file_path="/test/file.py",
            content_hash="abc123",
            last_modified=time.time(),
            file_size=1024,
            analysis_timestamp=time.time(),
            symbols_count=5,
            dependencies_count=2,
            language="python",
        )

        assert entry.file_path == "/test/file.py"
        assert entry.content_hash == "abc123"
        assert entry.symbols_count == 5
        assert entry.language == "python"

        # Test IncrementalIndexCache creation
        cache = IncrementalIndexCache(
            project_path="/test/project",
            cache_version="1.0.0",
            last_full_index=time.time(),
            file_entries={"/test/file.py": entry},
            project_metadata={"total_files": 1},
            dependency_graph_hash="hash123",
            symbol_registry_hash="hash456",
            created_at=time.time(),
            updated_at=time.time(),
        )

        assert cache.project_path == "/test/project"
        assert len(cache.file_entries) == 1
        assert cache.cache_version == "1.0.0"
        assert cache.project_metadata["total_files"] == 1

        print("✅ Incremental indexer models test passed")
        return True

    except Exception as e:
        print(f"❌ Incremental indexer models test failed: {e}")
        return False


def test_enhanced_agent_indexer_tools():
    """Test enhanced agent has incremental indexer tools"""
    try:
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent

        # Check that the class has the new indexer tools
        expected_tools = ["_get_indexer_metrics_tool", "_refresh_project_index_tool"]

        for tool in expected_tools:
            assert hasattr(EnhancedL3CodingAgent, tool), f"Missing tool: {tool}"
            method = getattr(EnhancedL3CodingAgent, tool)
            assert callable(method), f"Tool {tool} is not callable"

        print("✅ Enhanced agent indexer tools test passed")
        return True

    except Exception as e:
        print(f"❌ Enhanced agent indexer tools test failed: {e}")
        return False


def test_file_monitor_integration():
    """Test file monitor service has incremental indexer integration"""
    try:
        from app.services.file_monitor_service import file_monitor_service

        # Check that file monitor has the trigger method
        assert hasattr(file_monitor_service, "_trigger_incremental_index_update")

        method = getattr(file_monitor_service, "_trigger_incremental_index_update")
        assert callable(method)

        print("✅ File monitor integration test passed")
        return True

    except Exception as e:
        print(f"❌ File monitor integration test failed: {e}")
        return False


def test_incremental_indexer_configuration():
    """Test incremental indexer configuration"""
    try:
        from app.services.incremental_indexer import incremental_indexer

        # Check configuration values
        assert hasattr(incremental_indexer, "cache_version")
        assert hasattr(incremental_indexer, "full_index_interval")
        assert hasattr(incremental_indexer, "max_cache_age")
        assert hasattr(incremental_indexer, "batch_size")

        assert incremental_indexer.cache_version == "1.0.0"
        assert incremental_indexer.full_index_interval > 0
        assert incremental_indexer.max_cache_age > 0
        assert incremental_indexer.batch_size > 0

        print("✅ Incremental indexer configuration test passed")
        return True

    except Exception as e:
        print(f"❌ Incremental indexer configuration test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running Basic Incremental Indexer Tests...")
    print()

    tests = [
        ("Incremental Indexer Basic", test_incremental_indexer_basic),
        ("Incremental Indexer Models", test_incremental_indexer_models),
        ("Enhanced Agent Indexer Tools", test_enhanced_agent_indexer_tools),
        ("File Monitor Integration", test_file_monitor_integration),
        ("Incremental Indexer Configuration", test_incremental_indexer_configuration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
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

    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All basic incremental indexer tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed or had issues")
