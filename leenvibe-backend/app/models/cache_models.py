"""
Cache Data Models

Data models for cache entries, metadata, and statistics used throughout
the LeenVibe caching system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional


class CacheStatus(str, Enum):
    """Cache entry status"""

    VALID = "valid"
    EXPIRED = "expired"
    STALE = "stale"
    CORRUPTED = "corrupted"
    PENDING = "pending"


class CachePriority(str, Enum):
    """Cache entry priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CacheMetadata:
    """Metadata for cache entries"""

    key: str
    created_at: datetime
    last_accessed: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    size_bytes: int = 0
    status: CacheStatus = CacheStatus.VALID
    priority: CachePriority = CachePriority.NORMAL
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    version: str = "1.0"
    checksum: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def is_stale(self, stale_threshold_minutes: int = 60) -> bool:
        """Check if cache entry is stale"""
        stale_threshold = datetime.now() - timedelta(minutes=stale_threshold_minutes)
        return self.last_accessed < stale_threshold

    def update_access(self):
        """Update access timestamp and count"""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class CacheEntry:
    """A cache entry with data and metadata"""

    key: str
    data: Any
    metadata: CacheMetadata

    def is_valid(self) -> bool:
        """Check if cache entry is valid"""
        return (
            self.metadata.status == CacheStatus.VALID and not self.metadata.is_expired()
        )

    def get_size_estimate(self) -> int:
        """Get estimated size of cache entry in bytes"""
        try:
            import sys

            return sys.getsizeof(self.data) + sys.getsizeof(self.metadata)
        except Exception:
            return self.metadata.size_bytes or 1024  # Default estimate


@dataclass
class CacheStatistics:
    """Cache performance and usage statistics"""

    total_entries: int = 0
    valid_entries: int = 0
    expired_entries: int = 0
    stale_entries: int = 0
    corrupted_entries: int = 0
    total_size_bytes: int = 0
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    average_access_time_ms: float = 0.0
    cache_hit_ratio: float = 0.0
    memory_usage_percentage: float = 0.0
    last_cleanup: Optional[datetime] = None

    def calculate_hit_ratio(self):
        """Calculate and update cache hit ratio"""
        total_requests = self.hit_count + self.miss_count
        if total_requests > 0:
            self.cache_hit_ratio = self.hit_count / total_requests
        else:
            self.cache_hit_ratio = 0.0

    def update_hit(self, access_time_ms: float):
        """Update statistics for cache hit"""
        self.hit_count += 1
        self._update_average_access_time(access_time_ms)
        self.calculate_hit_ratio()

    def update_miss(self, access_time_ms: float):
        """Update statistics for cache miss"""
        self.miss_count += 1
        self._update_average_access_time(access_time_ms)
        self.calculate_hit_ratio()

    def _update_average_access_time(self, access_time_ms: float):
        """Update average access time"""
        if self.average_access_time_ms == 0:
            self.average_access_time_ms = access_time_ms
        else:
            total_requests = self.hit_count + self.miss_count
            self.average_access_time_ms = (
                self.average_access_time_ms * (total_requests - 1) + access_time_ms
            ) / total_requests


@dataclass
class CacheConfiguration:
    """Cache configuration settings"""

    max_size_mb: int = 500
    max_entries: int = 10000
    default_ttl_minutes: int = 60
    stale_threshold_minutes: int = 30
    cleanup_interval_minutes: int = 15
    eviction_policy: str = "lru"  # lru, lfu, fifo
    compression_enabled: bool = True
    persistence_enabled: bool = True
    auto_backup_enabled: bool = True
    checkpoint_interval_minutes: int = 30
    max_checkpoints: int = 10

    def get_max_size_bytes(self) -> int:
        """Get maximum cache size in bytes"""
        return self.max_size_mb * 1024 * 1024


@dataclass
class EvictionCandidate:
    """Candidate for cache eviction"""

    key: str
    score: float
    reason: str
    metadata: CacheMetadata

    def __lt__(self, other):
        """For sorting by eviction score"""
        return self.score < other.score


@dataclass
class CacheWarming:
    """Cache warming configuration and state"""

    enabled: bool = True
    warming_strategy: str = "balanced"  # aggressive, balanced, conservative
    priority_patterns: List[str] = field(default_factory=list)
    max_concurrent_warmings: int = 3
    warming_interval_hours: int = 24
    min_access_count: int = 2
    min_session_time_seconds: int = 300
    last_warming: Optional[datetime] = None
    warming_in_progress: bool = False

    def should_warm(self) -> bool:
        """Check if cache warming should be triggered"""
        if not self.enabled or self.warming_in_progress:
            return False

        if self.last_warming is None:
            return True

        hours_since_warming = (
            datetime.now() - self.last_warming
        ).total_seconds() / 3600
        return hours_since_warming >= self.warming_interval_hours
