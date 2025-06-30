"""
Test Cache Persistence Service

Tests for cache persistence, recovery mechanisms, and fault tolerance.
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_cache_persistence_service_imports():
    """Test that cache persistence service imports correctly"""
    try:
        from app.services.cache_persistence_service import (
            CacheFormat,
            CachePersistenceService,
            RecoveryStrategy,
            cache_persistence_service,
        )

        # Test service exists
        assert cache_persistence_service is not None
        assert isinstance(cache_persistence_service, CachePersistenceService)

        # Test enums
        assert hasattr(CacheFormat, "JSON")
        assert hasattr(CacheFormat, "PICKLE")
        assert hasattr(CacheFormat, "COMPRESSED_PICKLE")

        assert hasattr(RecoveryStrategy, "FULL_RECOVERY")
        assert hasattr(RecoveryStrategy, "PARTIAL_RECOVERY")
        assert hasattr(RecoveryStrategy, "REBUILD_ON_FAILURE")
        assert hasattr(RecoveryStrategy, "SKIP_CORRUPTED")

        print("✅ Cache persistence service imports test passed")
        return True

    except Exception as e:
        print(f"❌ Cache persistence service imports test failed: {e}")
        return False


def test_cache_models_imports():
    """Test that cache models import correctly"""
    try:
        from app.models.cache_models import (
            CachePriority,
            CacheStatus,
        )

        # Test enums
        assert hasattr(CacheStatus, "VALID")
        assert hasattr(CacheStatus, "EXPIRED")
        assert hasattr(CacheStatus, "STALE")
        assert hasattr(CacheStatus, "CORRUPTED")

        assert hasattr(CachePriority, "LOW")
        assert hasattr(CachePriority, "NORMAL")
        assert hasattr(CachePriority, "HIGH")
        assert hasattr(CachePriority, "CRITICAL")

        print("✅ Cache models imports test passed")
        return True

    except Exception as e:
        print(f"❌ Cache models imports test failed: {e}")
        return False


def test_cache_metadata_creation():
    """Test CacheMetadata creation and methods"""
    try:
        from app.models.cache_models import CacheMetadata, CachePriority, CacheStatus

        # Test basic creation
        now = datetime.now()
        metadata = CacheMetadata(
            key="test_key",
            created_at=now,
            last_accessed=now,
            expires_at=now + timedelta(hours=1),
            access_count=5,
            size_bytes=1024,
            status=CacheStatus.VALID,
            priority=CachePriority.HIGH,
        )

        assert metadata.key == "test_key"
        assert metadata.access_count == 5
        assert metadata.size_bytes == 1024
        assert metadata.status == CacheStatus.VALID
        assert metadata.priority == CachePriority.HIGH

        # Test expiration check
        assert not metadata.is_expired()

        # Test expired metadata
        expired_metadata = CacheMetadata(
            key="expired_key",
            created_at=now,
            last_accessed=now,
            expires_at=now - timedelta(hours=1),
        )
        assert expired_metadata.is_expired()

        # Test stale check
        stale_metadata = CacheMetadata(
            key="stale_key",
            created_at=now - timedelta(hours=2),
            last_accessed=now - timedelta(hours=2),
        )
        assert stale_metadata.is_stale(stale_threshold_minutes=60)

        # Test access update
        original_count = metadata.access_count
        metadata.update_access()
        assert metadata.access_count == original_count + 1

        print("✅ Cache metadata creation test passed")
        return True

    except Exception as e:
        print(f"❌ Cache metadata creation test failed: {e}")
        return False


def test_cache_entry_creation():
    """Test CacheEntry creation and methods"""
    try:
        from app.models.cache_models import CacheEntry, CacheMetadata, CacheStatus

        now = datetime.now()
        metadata = CacheMetadata(
            key="test_entry",
            created_at=now,
            last_accessed=now,
            status=CacheStatus.VALID,
        )

        # Test cache entry creation
        test_data = {"message": "hello world", "count": 42}
        entry = CacheEntry(key="test_entry", data=test_data, metadata=metadata)

        assert entry.key == "test_entry"
        assert entry.data == test_data
        assert entry.metadata == metadata

        # Test validity check
        assert entry.is_valid()

        # Test invalid entry
        metadata.status = CacheStatus.EXPIRED
        assert not entry.is_valid()

        # Test size estimate
        size = entry.get_size_estimate()
        assert isinstance(size, int)
        assert size > 0

        print("✅ Cache entry creation test passed")
        return True

    except Exception as e:
        print(f"❌ Cache entry creation test failed: {e}")
        return False


def test_cache_statistics():
    """Test CacheStatistics calculations"""
    try:
        from app.models.cache_models import CacheStatistics

        stats = CacheStatistics()

        # Test initial state
        assert stats.hit_count == 0
        assert stats.miss_count == 0
        assert stats.cache_hit_ratio == 0.0

        # Test hit updates
        stats.update_hit(10.0)
        stats.update_hit(20.0)
        stats.update_miss(15.0)

        assert stats.hit_count == 2
        assert stats.miss_count == 1
        assert stats.cache_hit_ratio == 2 / 3  # 2 hits out of 3 total
        assert stats.average_access_time_ms == 15.0  # (10 + 20 + 15) / 3

        print("✅ Cache statistics test passed")
        return True

    except Exception as e:
        print(f"❌ Cache statistics test failed: {e}")
        return False


def test_cache_format_enums():
    """Test CacheFormat enum values"""
    try:
        from app.services.cache_persistence_service import CacheFormat

        # Test enum values
        assert CacheFormat.JSON == "json"
        assert CacheFormat.PICKLE == "pickle"
        assert CacheFormat.COMPRESSED_PICKLE == "compressed_pickle"

        # Test enum iteration
        formats = list(CacheFormat)
        assert len(formats) == 3
        assert CacheFormat.JSON in formats
        assert CacheFormat.PICKLE in formats
        assert CacheFormat.COMPRESSED_PICKLE in formats

        print("✅ Cache format enums test passed")
        return True

    except Exception as e:
        print(f"❌ Cache format enums test failed: {e}")
        return False


def test_recovery_strategy_enums():
    """Test RecoveryStrategy enum values"""
    try:
        from app.services.cache_persistence_service import RecoveryStrategy

        # Test enum values
        assert RecoveryStrategy.FULL_RECOVERY == "full_recovery"
        assert RecoveryStrategy.PARTIAL_RECOVERY == "partial_recovery"
        assert RecoveryStrategy.REBUILD_ON_FAILURE == "rebuild_on_failure"
        assert RecoveryStrategy.SKIP_CORRUPTED == "skip_corrupted"

        # Test enum iteration
        strategies = list(RecoveryStrategy)
        assert len(strategies) == 4

        print("✅ Recovery strategy enums test passed")
        return True

    except Exception as e:
        print(f"❌ Recovery strategy enums test failed: {e}")
        return False


def test_service_initialization():
    """Test cache persistence service initialization"""
    try:
        from app.services.cache_persistence_service import (
            CacheFormat,
            CachePersistenceService,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            service = CachePersistenceService(cache_dir=temp_dir)

            # Test initialization
            assert service.cache_dir.exists()
            assert service.default_format == CacheFormat.COMPRESSED_PICKLE
            assert service.checkpoint_interval_minutes == 30
            assert service.max_checkpoints == 10
            assert service.compression_level == 6
            assert service.backup_on_save is True

            # Test empty state
            assert len(service.checkpoints) == 0
            assert len(service.cached_data) == 0
            assert len(service.cache_metadata) == 0

            # Test metrics initialization
            metrics = service.get_metrics()
            assert isinstance(metrics, dict)
            assert metrics["total_saves"] == 0
            assert metrics["total_loads"] == 0
            assert metrics["successful_saves"] == 0
            assert metrics["successful_loads"] == 0

        print("✅ Service initialization test passed")
        return True

    except Exception as e:
        print(f"❌ Service initialization test failed: {e}")
        return False


async def test_cache_save_load_basic():
    """Test basic cache save and load operations"""
    try:
        from app.models.cache_models import CacheMetadata, CacheStatus
        from app.services.cache_persistence_service import (
            CacheFormat,
            CachePersistenceService,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            service = CachePersistenceService(cache_dir=temp_dir)

            # Test data
            test_data = {
                "key1": {"data": "value1", "timestamp": "2023-01-01"},
                "key2": {"data": "value2", "timestamp": "2023-01-02"},
            }

            test_metadata = {
                "key1": CacheMetadata(
                    key="key1",
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    status=CacheStatus.VALID,
                ),
                "key2": CacheMetadata(
                    key="key2",
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    status=CacheStatus.VALID,
                ),
            }

            # Test save
            success = await service.save_cache(
                test_data, test_metadata, CacheFormat.JSON
            )
            assert success is True

            # Test load
            loaded_data, loaded_metadata = await service.load_cache(CacheFormat.JSON)
            assert loaded_data == test_data
            assert len(loaded_metadata) == 2
            assert "key1" in loaded_metadata
            assert "key2" in loaded_metadata

            # Verify metrics
            metrics = service.get_metrics()
            assert metrics["total_saves"] == 1
            assert metrics["successful_saves"] == 1
            assert metrics["total_loads"] == 1
            assert metrics["successful_loads"] == 1

        print("✅ Cache save/load basic test passed")
        return True

    except Exception as e:
        print(f"❌ Cache save/load basic test failed: {e}")
        return False


async def test_checkpoint_creation():
    """Test cache checkpoint creation"""
    try:
        from app.services.cache_persistence_service import CachePersistenceService

        with tempfile.TemporaryDirectory() as temp_dir:
            service = CachePersistenceService(cache_dir=temp_dir)

            # Add some test data
            test_data = {
                "checkpoint_key": {
                    "data": "checkpoint_value",
                    "timestamp": "2023-01-01",
                }
            }
            service.cached_data = test_data

            # Create checkpoint
            checkpoint = await service.create_checkpoint(force=True)

            assert checkpoint is not None
            assert checkpoint.checkpoint_id.startswith("checkpoint_")
            assert checkpoint.cache_size == 1
            assert checkpoint.cache_version == "1.0"
            assert len(checkpoint.checksum) == 64  # SHA256 hex length

            # Verify checkpoint was added
            assert len(service.checkpoints) == 1
            assert service.checkpoints[0] == checkpoint

            # Verify checkpoint file exists
            checkpoint_file = (
                service.cache_dir / "checkpoints" / f"{checkpoint.checkpoint_id}.cache"
            )
            assert checkpoint_file.exists()

        print("✅ Checkpoint creation test passed")
        return True

    except Exception as e:
        print(f"❌ Checkpoint creation test failed: {e}")
        return False


async def test_cache_recovery():
    """Test cache recovery mechanisms"""
    try:
        from app.services.cache_persistence_service import (
            CachePersistenceService,
            RecoveryStrategy,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            service = CachePersistenceService(cache_dir=temp_dir)

            # Create test data and checkpoint
            test_data = {
                "recovery_key": {"data": "recovery_value", "timestamp": "2023-01-01"}
            }
            service.cached_data = test_data
            await service.create_checkpoint(force=True)

            # Clear cache to simulate data loss
            service.cached_data = {}

            # Test recovery
            result = await service.recover_cache(RecoveryStrategy.FULL_RECOVERY)

            assert result.success is True
            assert result.recovered_entries == 1
            assert result.corrupted_entries == 0
            assert len(result.errors) == 0

            # Verify data was recovered
            assert len(service.cached_data) == 1
            assert "recovery_key" in service.cached_data
            assert service.cached_data["recovery_key"]["data"] == "recovery_value"

        print("✅ Cache recovery test passed")
        return True

    except Exception as e:
        print(f"❌ Cache recovery test failed: {e}")
        return False


async def test_cache_integrity_verification():
    """Test cache integrity verification"""
    try:
        from app.models.cache_models import CacheMetadata, CacheStatus
        from app.services.cache_persistence_service import CachePersistenceService

        with tempfile.TemporaryDirectory() as temp_dir:
            service = CachePersistenceService(cache_dir=temp_dir)

            # Add valid data
            service.cached_data = {
                "valid_key": {"data": "valid_value"},
                "invalid_key": "not_a_dict",  # Invalid structure
                "missing_data_key": {"timestamp": "2023-01-01"},  # Missing 'data' field
            }

            service.cache_metadata = {
                "valid_key": CacheMetadata(
                    key="valid_key",
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    status=CacheStatus.VALID,
                )
                # Note: missing metadata for other keys
            }

            # Verify integrity
            report = await service.verify_cache_integrity()

            assert isinstance(report, dict)
            assert "total_entries" in report
            assert "valid_entries" in report
            assert "corrupted_entries" in report
            assert "missing_metadata" in report
            assert "details" in report

            # Check that some corruption was detected
            assert report["total_entries"] > 0
            assert report["corrupted_entries"] > 0 or report["missing_metadata"] > 0

        print("✅ Cache integrity verification test passed")
        return True

    except Exception as e:
        print(f"❌ Cache integrity verification test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Running Cache Persistence Service Tests...")
    print()

    # Sync tests
    sync_tests = [
        ("Cache Persistence Service Imports", test_cache_persistence_service_imports),
        ("Cache Models Imports", test_cache_models_imports),
        ("Cache Metadata Creation", test_cache_metadata_creation),
        ("Cache Entry Creation", test_cache_entry_creation),
        ("Cache Statistics", test_cache_statistics),
        ("Cache Format Enums", test_cache_format_enums),
        ("Recovery Strategy Enums", test_recovery_strategy_enums),
        ("Service Initialization", test_service_initialization),
    ]

    # Async tests
    async_tests = [
        ("Cache Save/Load Basic", test_cache_save_load_basic),
        ("Checkpoint Creation", test_checkpoint_creation),
        ("Cache Recovery", test_cache_recovery),
        ("Cache Integrity Verification", test_cache_integrity_verification),
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
        print("🎉 All cache persistence service tests passed!")
    else:
        print(f"⚠️ {total - passed} tests failed or had issues")
