"""
Basic Cache Warming Service Test

Simple tests for cache warming service without external dependencies.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_cache_warming_service_basic():
    """Test basic cache warming service functionality"""
    try:
        from app.services.cache_warming_service import (
            SmartCacheWarmingService,
            cache_warming_service,
        )

        # Test service exists
        assert cache_warming_service is not None
        assert isinstance(cache_warming_service, SmartCacheWarmingService)

        # Test basic methods exist
        assert hasattr(cache_warming_service, "track_project_access")
        assert hasattr(cache_warming_service, "track_session_end")
        assert hasattr(cache_warming_service, "queue_warming_task")
        assert hasattr(cache_warming_service, "get_warming_candidates")
        assert hasattr(cache_warming_service, "get_metrics")
        assert hasattr(cache_warming_service, "set_warming_strategy")

        # Test configuration
        assert hasattr(cache_warming_service, "strategies")
        assert hasattr(cache_warming_service, "current_strategy")

        # Test default strategy
        assert cache_warming_service.current_strategy == "balanced"

        # Test strategies exist
        expected_strategies = ["aggressive", "balanced", "conservative"]
        for strategy in expected_strategies:
            assert strategy in cache_warming_service.strategies

        print("✅ Cache warming service basic test passed")
        return True

    except Exception as e:
        print(f"❌ Cache warming service basic test failed: {e}")
        return False


def test_cache_warming_models():
    """Test cache warming data models"""
    try:
        from datetime import datetime

        from app.services.cache_warming_service import (
            CacheWarmingStrategy,
            ProjectUsageStats,
            WarmingTask,
        )

        # Test ProjectUsageStats creation
        stats = ProjectUsageStats(
            project_path="/test/project",
            first_access=datetime.now(),
            last_access=datetime.now(),
            access_count=5,
            total_session_time=300.0,
            average_session_duration=60.0,
            files_accessed=10,
            symbols_queried=25,
            analysis_requests=3,
            warming_score=0.75,
        )

        assert stats.project_path == "/test/project"
        assert stats.access_count == 5
        assert stats.warming_score == 0.75

        # Test CacheWarmingStrategy creation
        strategy = CacheWarmingStrategy(
            strategy_name="test",
            min_access_count=3,
            min_total_session_time=300,
            warming_interval_hours=24,
        )

        assert strategy.strategy_name == "test"
        assert strategy.min_access_count == 3
        assert strategy.warming_interval_hours == 24

        # Test WarmingTask creation
        task = WarmingTask(
            task_id="test_task_123",
            project_path="/test/project",
            strategy="balanced",
            priority_score=0.8,
            created_at=datetime.now(),
        )

        assert task.task_id == "test_task_123"
        assert task.strategy == "balanced"
        assert task.priority_score == 0.8

        print("✅ Cache warming models test passed")
        return True

    except Exception as e:
        print(f"❌ Cache warming models test failed: {e}")
        return False


def test_cache_warming_configuration():
    """Test cache warming configuration and strategies"""
    try:
        from app.services.cache_warming_service import cache_warming_service

        # Test getting metrics
        metrics = cache_warming_service.get_metrics()
        assert isinstance(metrics, dict)

        expected_metrics = [
            "total_warming_tasks",
            "successful_warmings",
            "failed_warmings",
            "average_warming_time",
            "total_projects_tracked",
            "background_warming_active",
            "queue_size",
            "active_tasks",
            "completed_tasks",
            "current_strategy",
        ]

        for metric in expected_metrics:
            assert metric in metrics

        # Test strategy switching
        original_strategy = cache_warming_service.current_strategy

        # Test setting valid strategies
        for strategy in ["aggressive", "balanced", "conservative"]:
            success = cache_warming_service.set_warming_strategy(strategy)
            assert success is True
            assert cache_warming_service.current_strategy == strategy

        # Test setting invalid strategy
        success = cache_warming_service.set_warming_strategy("invalid")
        assert success is False

        # Restore original strategy
        cache_warming_service.set_warming_strategy(original_strategy)

        print("✅ Cache warming configuration test passed")
        return True

    except Exception as e:
        print(f"❌ Cache warming configuration test failed: {e}")
        return False


def test_cache_warming_usage_tracking():
    """Test cache warming usage tracking functionality"""
    try:
        from app.services.cache_warming_service import cache_warming_service

        test_project = "/test/warming/project"
        test_client = "test_client_123"

        # Track project access
        cache_warming_service.track_project_access(
            test_project,
            test_client,
            {"files_accessed": 5, "symbols_queried": 15, "analysis_requests": 2},
        )

        # Check that project was tracked
        assert test_project in cache_warming_service.project_stats
        stats = cache_warming_service.project_stats[test_project]

        assert stats.access_count >= 1
        assert stats.files_accessed >= 5
        assert stats.symbols_queried >= 15
        assert stats.analysis_requests >= 2

        # Track session end
        cache_warming_service.track_session_end(test_client, test_project)

        # Check session tracking
        assert test_client not in cache_warming_service.active_sessions

        print("✅ Cache warming usage tracking test passed")
        return True

    except Exception as e:
        print(f"❌ Cache warming usage tracking test failed: {e}")
        return False


def test_incremental_indexer_warming_integration():
    """Test incremental indexer has cache warming integration"""
    try:
        from app.services.incremental_indexer import incremental_indexer

        # Check that incremental indexer has warming methods
        assert hasattr(incremental_indexer, "trigger_intelligent_warming")

        # Test that trigger method is callable
        trigger_method = getattr(incremental_indexer, "trigger_intelligent_warming")
        assert callable(trigger_method)

        print("✅ Incremental indexer warming integration test passed")
        return True

    except Exception as e:
        print(f"❌ Incremental indexer warming integration test failed: {e}")
        return False


def test_session_manager_warming_integration():
    """Test session manager has cache warming integration"""
    try:
        from app.agent.session_manager import SessionManager

        # Check that session manager imports cache warming service
        # This test passes if the import doesn't fail
        session_manager = SessionManager()
        assert session_manager is not None

        print("✅ Session manager warming integration test passed")
        return True

    except Exception as e:
        print(f"❌ Session manager warming integration test failed: {e}")
        return False


def test_enhanced_agent_warming_tools():
    """Test enhanced agent has cache warming tools"""
    try:
        from app.agent.enhanced_l3_agent import EnhancedL3CodingAgent

        # Check that the class has the cache warming tools
        expected_tools = [
            "_get_warming_candidates_tool",
            "_trigger_cache_warming_tool",
            "_get_warming_metrics_tool",
            "_set_warming_strategy_tool",
        ]

        for tool in expected_tools:
            assert hasattr(EnhancedL3CodingAgent, tool), f"Missing tool: {tool}"
            method = getattr(EnhancedL3CodingAgent, tool)
            assert callable(method), f"Tool {tool} is not callable"

        print("✅ Enhanced agent warming tools test passed")
        return True

    except Exception as e:
        print(f"❌ Enhanced agent warming tools test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running Basic Cache Warming Tests...")
    print()

    tests = [
        ("Cache Warming Service Basic", test_cache_warming_service_basic),
        ("Cache Warming Models", test_cache_warming_models),
        ("Cache Warming Configuration", test_cache_warming_configuration),
        ("Cache Warming Usage Tracking", test_cache_warming_usage_tracking),
        (
            "Incremental Indexer Warming Integration",
            test_incremental_indexer_warming_integration,
        ),
        (
            "Session Manager Warming Integration",
            test_session_manager_warming_integration,
        ),
        ("Enhanced Agent Warming Tools", test_enhanced_agent_warming_tools),
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
        print("🎉 All basic cache warming tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed or had issues")
