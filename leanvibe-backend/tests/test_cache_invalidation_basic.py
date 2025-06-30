"""
Basic Cache Invalidation Service Test

Simple tests for cache invalidation service without external dependencies.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_cache_invalidation_service_basic():
    """Test basic cache invalidation service functionality"""
    try:
        from app.services.cache_invalidation_service import (
            CacheInvalidationService,
            cache_invalidation_service,
        )

        # Test service exists
        assert cache_invalidation_service is not None
        assert isinstance(cache_invalidation_service, CacheInvalidationService)

        # Test basic methods exist
        assert hasattr(cache_invalidation_service, "invalidate_file_cache")
        assert hasattr(cache_invalidation_service, "invalidate_multiple_files")
        assert hasattr(cache_invalidation_service, "build_dependency_graph")
        assert hasattr(cache_invalidation_service, "get_metrics")
        assert hasattr(cache_invalidation_service, "get_dependency_info")
        assert hasattr(cache_invalidation_service, "get_invalidation_history")

        # Test configuration values
        assert hasattr(cache_invalidation_service, "max_propagation_depth")
        assert hasattr(cache_invalidation_service, "cascade_threshold")
        assert hasattr(cache_invalidation_service, "symbol_invalidation_enabled")

        assert cache_invalidation_service.max_propagation_depth == 10
        assert cache_invalidation_service.cascade_threshold == 5
        assert cache_invalidation_service.symbol_invalidation_enabled is True

        # Test metrics
        metrics = cache_invalidation_service.get_metrics()
        assert isinstance(metrics, dict)

        expected_metrics = [
            "total_invalidations",
            "cascade_invalidations",
            "symbol_based_invalidations",
            "external_dependency_invalidations",
            "average_propagation_depth",
            "cache_coherency_events",
            "dependency_graph_size",
            "symbol_mappings",
            "import_mappings",
            "recent_events",
        ]

        for metric in expected_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))

        print("✅ Cache invalidation service basic test passed")
        return True

    except Exception as e:
        print(f"❌ Cache invalidation service basic test failed: {e}")
        return False


def test_cache_invalidation_models():
    """Test cache invalidation data models"""
    try:
        from datetime import datetime

        from app.services.cache_invalidation_service import (
            DependencyNode,
            InvalidationEvent,
        )

        # Test InvalidationEvent creation
        event = InvalidationEvent(
            file_path="/test/file.py",
            invalidation_type="direct",
            triggered_by="/test/file.py",
            timestamp=datetime.now(),
            propagation_depth=0,
            affected_symbols=["function_name"],
        )

        assert event.file_path == "/test/file.py"
        assert event.invalidation_type == "direct"
        assert event.propagation_depth == 0
        assert len(event.affected_symbols) == 1

        # Test DependencyNode creation
        node = DependencyNode(
            file_path="/test/file.py",
            dependencies={"dep1.py"},
            dependents={"dep2.py"},
            last_modified=1234567890.0,
            symbols={"function_name", "class_name"},
            external_imports={"os", "json"},
        )

        assert node.file_path == "/test/file.py"
        assert len(node.dependencies) == 1
        assert len(node.dependents) == 1
        assert len(node.symbols) == 2
        assert len(node.external_imports) == 2

        print("✅ Cache invalidation models test passed")
        return True

    except Exception as e:
        print(f"❌ Cache invalidation models test failed: {e}")
        return False


def test_incremental_indexer_integration():
    """Test incremental indexer has cache invalidation integration"""
    try:
        from app.services.incremental_indexer import incremental_indexer

        # Check that incremental indexer exists
        assert incremental_indexer is not None
        assert hasattr(incremental_indexer, "clear_cache")

        # Test that clear_cache method is callable
        clear_cache_method = getattr(incremental_indexer, "clear_cache")
        assert callable(clear_cache_method)

        print("✅ Incremental indexer integration test passed")
        return True

    except Exception as e:
        print(f"❌ Incremental indexer integration test failed: {e}")
        return False


def test_file_monitor_integration():
    """Test file monitor service has cache invalidation integration"""
    try:
        from app.services.file_monitor_service import file_monitor_service

        # Check that file monitor service exists
        assert file_monitor_service is not None
        assert hasattr(file_monitor_service, "_trigger_incremental_index_update")

        # Test that the trigger method is callable
        trigger_method = getattr(
            file_monitor_service, "_trigger_incremental_index_update"
        )
        assert callable(trigger_method)

        print("✅ File monitor integration test passed")
        return True

    except Exception as e:
        print(f"❌ File monitor integration test failed: {e}")
        return False


def test_enhanced_agent_cache_tools():
    """Test enhanced agent has cache invalidation tools"""
    try:
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent

        # Check that the class has the new cache tools
        expected_tools = ["_get_indexer_metrics_tool", "_refresh_project_index_tool"]

        for tool in expected_tools:
            assert hasattr(EnhancedL3CodingAgent, tool), f"Missing tool: {tool}"
            method = getattr(EnhancedL3CodingAgent, tool)
            assert callable(method), f"Tool {tool} is not callable"

        print("✅ Enhanced agent cache tools test passed")
        return True

    except Exception as e:
        print(f"❌ Enhanced agent cache tools test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running Basic Cache Invalidation Tests...")
    print()

    tests = [
        ("Cache Invalidation Service Basic", test_cache_invalidation_service_basic),
        ("Cache Invalidation Models", test_cache_invalidation_models),
        ("Incremental Indexer Integration", test_incremental_indexer_integration),
        ("File Monitor Integration", test_file_monitor_integration),
        ("Enhanced Agent Cache Tools", test_enhanced_agent_cache_tools),
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
        print("🎉 All basic cache invalidation tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed or had issues")
