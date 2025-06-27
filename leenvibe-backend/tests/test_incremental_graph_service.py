"""
Test Incremental Graph Update Service

Tests for the incremental graph update service with relationship propagation.
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_incremental_graph_service_imports():
    """Test that incremental graph service imports correctly"""
    try:
        from app.services.incremental_graph_service import (
            GraphChange,
            GraphUpdateBatch,
            GraphUpdateType,
            IncrementalGraphUpdateService,
            PropagationResult,
            incremental_graph_service,
        )

        # Test service exists
        assert incremental_graph_service is not None
        assert isinstance(incremental_graph_service, IncrementalGraphUpdateService)

        # Test enums and classes
        assert hasattr(GraphUpdateType, "NODE_ADDED")
        assert hasattr(GraphUpdateType, "NODE_UPDATED")
        assert hasattr(GraphUpdateType, "NODE_DELETED")
        assert hasattr(GraphUpdateType, "RELATIONSHIP_ADDED")
        assert hasattr(GraphUpdateType, "RELATIONSHIP_UPDATED")
        assert hasattr(GraphUpdateType, "RELATIONSHIP_DELETED")

        print("✅ Incremental graph service imports test passed")
        return True

    except Exception as e:
        print(f"❌ Incremental graph service imports test failed: {e}")
        return False


def test_graph_change_creation():
    """Test GraphChange data class creation"""
    try:
        from app.services.incremental_graph_service import GraphChange, GraphUpdateType

        # Test basic creation
        change = GraphChange(
            change_id="test_change_123",
            update_type=GraphUpdateType.NODE_ADDED,
            entity_type="file",
            entity_id="/test/file.py",
        )

        assert change.change_id == "test_change_123"
        assert change.update_type == GraphUpdateType.NODE_ADDED
        assert change.entity_type == "file"
        assert change.entity_id == "/test/file.py"
        assert change.old_data is None
        assert change.new_data is None
        assert isinstance(change.timestamp, datetime)
        assert change.related_changes == []

        # Test with data
        change_with_data = GraphChange(
            change_id="test_change_with_data",
            update_type=GraphUpdateType.NODE_UPDATED,
            entity_type="symbol",
            entity_id="test_symbol",
            old_data={"name": "old_name"},
            new_data={"name": "new_name"},
        )

        assert change_with_data.old_data == {"name": "old_name"}
        assert change_with_data.new_data == {"name": "new_name"}

        print("✅ Graph change creation test passed")
        return True

    except Exception as e:
        print(f"❌ Graph change creation test failed: {e}")
        return False


def test_graph_update_batch_creation():
    """Test GraphUpdateBatch data class creation"""
    try:
        from app.services.incremental_graph_service import (
            GraphChange,
            GraphUpdateBatch,
            GraphUpdateType,
        )

        # Create some test changes
        changes = [
            GraphChange(
                change_id="change_1",
                update_type=GraphUpdateType.NODE_ADDED,
                entity_type="file",
                entity_id="/test/file1.py",
            ),
            GraphChange(
                change_id="change_2",
                update_type=GraphUpdateType.NODE_UPDATED,
                entity_type="file",
                entity_id="/test/file2.py",
            ),
        ]

        # Create batch
        batch = GraphUpdateBatch(
            batch_id="test_batch_123", changes=changes, project_id="test_project"
        )

        assert batch.batch_id == "test_batch_123"
        assert len(batch.changes) == 2
        assert batch.project_id == "test_project"
        assert isinstance(batch.created_at, datetime)
        assert batch.applied_at is None
        assert batch.success is False
        assert batch.error_message is None
        assert batch.rollback_data is None

        print("✅ Graph update batch creation test passed")
        return True

    except Exception as e:
        print(f"❌ Graph update batch creation test failed: {e}")
        return False


def test_propagation_result_creation():
    """Test PropagationResult data class creation"""
    try:
        from app.services.incremental_graph_service import PropagationResult

        # Test basic creation
        result = PropagationResult(
            nodes_affected=10,
            relationships_updated=25,
            propagation_depth=3,
            execution_time_ms=150.5,
        )

        assert result.nodes_affected == 10
        assert result.relationships_updated == 25
        assert result.propagation_depth == 3
        assert result.execution_time_ms == 150.5
        assert result.warnings == []

        # Test with warnings
        result_with_warnings = PropagationResult(
            nodes_affected=5,
            relationships_updated=10,
            propagation_depth=2,
            execution_time_ms=75.0,
            warnings=["Test warning"],
        )

        assert result_with_warnings.warnings == ["Test warning"]

        print("✅ Propagation result creation test passed")
        return True

    except Exception as e:
        print(f"❌ Propagation result creation test failed: {e}")
        return False


def test_service_initialization():
    """Test incremental graph service initialization"""
    try:
        from app.services.incremental_graph_service import IncrementalGraphUpdateService

        service = IncrementalGraphUpdateService()

        # Test initialization
        assert hasattr(service, "pending_changes")
        assert hasattr(service, "update_history")
        assert hasattr(service, "max_history_size")
        assert hasattr(service, "max_propagation_depth")
        assert hasattr(service, "batch_size")
        assert hasattr(service, "propagation_timeout_seconds")
        assert hasattr(service, "metrics")
        assert hasattr(service, "relationship_types")

        # Test default values
        assert service.max_history_size == 100
        assert service.max_propagation_depth == 10
        assert service.batch_size == 50
        assert service.propagation_timeout_seconds == 30

        # Test metrics initialization
        expected_metrics = [
            "total_updates",
            "successful_updates",
            "failed_updates",
            "nodes_added",
            "nodes_updated",
            "nodes_deleted",
            "relationships_added",
            "relationships_updated",
            "relationships_deleted",
            "average_propagation_time_ms",
            "max_propagation_depth_reached",
        ]

        for metric in expected_metrics:
            assert metric in service.metrics
            assert isinstance(service.metrics[metric], (int, float))

        # Test relationship types
        expected_relationships = [
            "import",
            "call",
            "inheritance",
            "contains",
            "defines",
            "references",
            "depends_on",
        ]

        for rel_type in expected_relationships:
            assert rel_type in service.relationship_types

        print("✅ Service initialization test passed")
        return True

    except Exception as e:
        print(f"❌ Service initialization test failed: {e}")
        return False


def test_service_methods_exist():
    """Test that all required service methods exist"""
    try:
        from app.services.incremental_graph_service import incremental_graph_service

        # Test main public methods
        public_methods = [
            "process_file_changes",
            "rollback_batch",
            "get_metrics",
            "get_update_history",
        ]

        for method in public_methods:
            assert hasattr(incremental_graph_service, method)
            assert callable(getattr(incremental_graph_service, method))

        # Test helper methods
        helper_methods = [
            "_build_deletion_changes",
            "_build_update_changes",
            "_build_basic_file_update",
            "_build_move_changes",
            "_build_dependency_changes",
            "_apply_update_batch",
            "_propagate_relationship_changes",
            "_apply_node_additions",
            "_apply_node_updates",
            "_apply_node_deletions",
            "_apply_relationship_additions",
            "_apply_relationship_updates",
            "_apply_relationship_deletions",
            "_batch_changes",
            "_has_symbol_changed",
            "_get_dependency_key",
            "_get_node_data",
            "_get_file_symbols",
            "_get_file_dependencies",
            "_get_connected_nodes",
            "_update_metrics",
        ]

        for method in helper_methods:
            assert hasattr(incremental_graph_service, method)
            assert callable(getattr(incremental_graph_service, method))

        print("✅ Service methods exist test passed")
        return True

    except Exception as e:
        print(f"❌ Service methods exist test failed: {e}")
        return False


@patch("app.services.incremental_graph_service.graph_service")
async def test_process_file_changes_basic(mock_graph_service):
    """Test basic process_file_changes functionality"""
    try:
        from app.models.monitoring_models import ChangeType, FileChange
        from app.services.incremental_graph_service import (
            PropagationResult,
            incremental_graph_service,
        )

        # Mock graph service as initialized
        mock_graph_service.initialized = True

        # Create test file changes
        changes = [
            FileChange(
                id="change_1",
                file_path="/test/project/file1.py",
                change_type=ChangeType.CREATED,
                timestamp=datetime.now(),
            )
        ]

        # Test with mocked graph service
        with patch.object(
            incremental_graph_service, "_build_basic_file_update", return_value=[]
        ):
            with patch.object(
                incremental_graph_service, "_apply_update_batch", return_value=True
            ):
                with patch.object(
                    incremental_graph_service, "_propagate_relationship_changes"
                ) as mock_propagate:
                    mock_propagate.return_value = PropagationResult(0, 0, 0, 0.0)

                    result = await incremental_graph_service.process_file_changes(
                        "/test/project", changes, None
                    )

                    # Should return None if no changes to apply
                    assert result is None

        print("✅ Process file changes basic test passed")
        return True

    except Exception as e:
        print(f"❌ Process file changes basic test failed: {e}")
        return False


def test_get_metrics():
    """Test get_metrics method"""
    try:
        from app.services.incremental_graph_service import incremental_graph_service

        metrics = incremental_graph_service.get_metrics()

        # Test that metrics is a dict
        assert isinstance(metrics, dict)

        # Test that all expected metrics are present
        expected_metrics = [
            "total_updates",
            "successful_updates",
            "failed_updates",
            "nodes_added",
            "nodes_updated",
            "nodes_deleted",
            "relationships_added",
            "relationships_updated",
            "relationships_deleted",
            "average_propagation_time_ms",
            "max_propagation_depth_reached",
        ]

        for metric in expected_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))

        # Test that it's a copy (not the original)
        metrics["test_key"] = "test_value"
        original_metrics = incremental_graph_service.get_metrics()
        assert "test_key" not in original_metrics

        print("✅ Get metrics test passed")
        return True

    except Exception as e:
        print(f"❌ Get metrics test failed: {e}")
        return False


def test_get_update_history():
    """Test get_update_history method"""
    try:
        from app.services.incremental_graph_service import incremental_graph_service

        # Test empty history
        history = incremental_graph_service.get_update_history()
        assert isinstance(history, list)
        assert len(history) == 0

        # Test with limit
        history_limited = incremental_graph_service.get_update_history(limit=5)
        assert isinstance(history_limited, list)

        print("✅ Get update history test passed")
        return True

    except Exception as e:
        print(f"❌ Get update history test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running Incremental Graph Service Tests...")
    print()

    # Sync tests
    sync_tests = [
        ("Incremental Graph Service Imports", test_incremental_graph_service_imports),
        ("Graph Change Creation", test_graph_change_creation),
        ("Graph Update Batch Creation", test_graph_update_batch_creation),
        ("Propagation Result Creation", test_propagation_result_creation),
        ("Service Initialization", test_service_initialization),
        ("Service Methods Exist", test_service_methods_exist),
        ("Get Metrics", test_get_metrics),
        ("Get Update History", test_get_update_history),
    ]

    # Async tests
    async_tests = [("Process File Changes Basic", test_process_file_changes_basic)]

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
        print("🎉 All incremental graph service tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed or had issues")
