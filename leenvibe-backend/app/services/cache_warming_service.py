"""
Smart Cache Warming Service

Provides intelligent cache warming for frequently accessed projects based on
usage patterns, access frequency, and performance optimization strategies.
"""

import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import aiofiles

from ..models.ast_models import LanguageType, ProjectIndex
from ..models.cache_models import CacheEntry, CacheMetadata, CachePriority, CacheStatus
from ..models.monitoring_models import ChangeType, FileChange
from .cache_persistence_service import CacheFormat, cache_persistence_service

logger = logging.getLogger(__name__)


@dataclass
class ProjectUsageStats:
    """Statistics for project usage patterns"""

    project_path: str
    first_access: datetime
    last_access: datetime
    access_count: int
    total_session_time: float  # Total time spent in sessions (seconds)
    average_session_duration: float  # Average session duration (seconds)
    files_accessed: int
    symbols_queried: int
    analysis_requests: int
    warming_score: float  # Calculated warming priority score
    last_warmed: Optional[datetime] = None
    warming_success_rate: float = 0.0


@dataclass
class CacheWarmingStrategy:
    """Configuration for cache warming strategy"""

    strategy_name: str
    min_access_count: int = 3
    min_total_session_time: int = 300  # 5 minutes
    recency_weight: float = 0.4
    frequency_weight: float = 0.3
    session_quality_weight: float = 0.3
    warming_interval_hours: int = 24
    max_concurrent_warming: int = 3
    warming_timeout_minutes: int = 15


@dataclass
class WarmingTask:
    """Represents a cache warming task"""

    task_id: str
    project_path: str
    strategy: str
    priority_score: float
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success: bool = False
    error_message: Optional[str] = None
    warming_time_seconds: float = 0.0
    files_warmed: int = 0


class SmartCacheWarmingService:
    """
    Smart Cache Warming Service

    Intelligently warms caches for frequently accessed projects based on
    usage patterns, access frequency, and performance optimization.
    """

    def __init__(self, storage_dir: str = "./.leanvibe_cache"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

        # Usage tracking
        self.project_stats: Dict[str, ProjectUsageStats] = {}
        self.active_sessions: Dict[str, datetime] = {}  # client_id -> session_start

        # Warming configuration
        self.strategies = {
            "aggressive": CacheWarmingStrategy(
                strategy_name="aggressive",
                min_access_count=2,
                min_total_session_time=180,  # 3 minutes
                warming_interval_hours=12,
                max_concurrent_warming=5,
            ),
            "balanced": CacheWarmingStrategy(
                strategy_name="balanced",
                min_access_count=3,
                min_total_session_time=300,  # 5 minutes
                warming_interval_hours=24,
                max_concurrent_warming=3,
            ),
            "conservative": CacheWarmingStrategy(
                strategy_name="conservative",
                min_access_count=5,
                min_total_session_time=600,  # 10 minutes
                warming_interval_hours=48,
                max_concurrent_warming=2,
            ),
        }
        self.current_strategy = "balanced"

        # Warming state
        self.warming_queue: deque[WarmingTask] = deque()
        self.active_warming_tasks: Dict[str, WarmingTask] = {}
        self.completed_tasks: List[WarmingTask] = []
        self.max_completed_history = 100

        # Performance metrics
        self.metrics = {
            "total_warming_tasks": 0,
            "successful_warmings": 0,
            "failed_warmings": 0,
            "average_warming_time": 0.0,
            "total_projects_tracked": 0,
            "cache_hit_improvement": 0.0,
            "background_warming_active": False,
        }

        # Background tasks
        self.warming_background_task: Optional[asyncio.Task] = None
        self.stats_cleanup_task: Optional[asyncio.Task] = None

        # Cache persistence
        self.persistence_enabled = True
        self.auto_persistence_interval_minutes = 15
        self.last_persistence_save = datetime.now()

    async def initialize(self):
        """Initialize the cache warming service"""
        try:
            logger.info("Initializing Smart Cache Warming Service...")

            # Load existing usage statistics
            await self._load_project_stats()

            # Start background tasks
            await self._start_background_tasks()

            logger.info(
                f"Cache warming service initialized with {len(self.project_stats)} tracked projects"
            )
            return True

        except Exception as e:
            logger.error(f"Error initializing cache warming service: {e}")
            return False

    async def shutdown(self):
        """Shutdown the cache warming service"""
        try:
            logger.info("Shutting down cache warming service...")

            # Cancel background tasks
            if self.warming_background_task:
                self.warming_background_task.cancel()
                try:
                    await self.warming_background_task
                except asyncio.CancelledError:
                    pass

            if self.stats_cleanup_task:
                self.stats_cleanup_task.cancel()
                try:
                    await self.stats_cleanup_task
                except asyncio.CancelledError:
                    pass

            # Save final statistics
            await self._save_project_stats()

            logger.info("Cache warming service shutdown complete")

        except Exception as e:
            logger.error(f"Error during cache warming service shutdown: {e}")

    def track_project_access(
        self,
        project_path: str,
        client_id: str,
        session_data: Optional[Dict[str, Any]] = None,
    ):
        """Track project access for warming analysis"""
        try:
            project_path = str(Path(project_path).absolute())
            current_time = datetime.now()

            # Update or create project statistics
            if project_path not in self.project_stats:
                self.project_stats[project_path] = ProjectUsageStats(
                    project_path=project_path,
                    first_access=current_time,
                    last_access=current_time,
                    access_count=1,
                    total_session_time=0.0,
                    average_session_duration=0.0,
                    files_accessed=0,
                    symbols_queried=0,
                    analysis_requests=0,
                    warming_score=0.0,
                )
                self.metrics["total_projects_tracked"] += 1
            else:
                stats = self.project_stats[project_path]
                stats.access_count += 1
                stats.last_access = current_time

            # Track session start
            self.active_sessions[client_id] = current_time

            # Update session-specific data if provided
            if session_data:
                stats = self.project_stats[project_path]
                stats.files_accessed += session_data.get("files_accessed", 0)
                stats.symbols_queried += session_data.get("symbols_queried", 0)
                stats.analysis_requests += session_data.get("analysis_requests", 0)

            # Recalculate warming score
            self._update_warming_score(project_path)

            logger.debug(f"Tracked access to {project_path} for client {client_id}")

        except Exception as e:
            logger.error(f"Error tracking project access: {e}")

    def track_session_end(self, client_id: str, project_path: str):
        """Track the end of a project session"""
        try:
            if client_id not in self.active_sessions:
                return

            project_path = str(Path(project_path).absolute())
            session_start = self.active_sessions.pop(client_id)
            session_duration = (datetime.now() - session_start).total_seconds()

            if project_path in self.project_stats:
                stats = self.project_stats[project_path]
                stats.total_session_time += session_duration

                # Update average session duration
                if stats.access_count > 0:
                    stats.average_session_duration = (
                        stats.total_session_time / stats.access_count
                    )

                # Recalculate warming score
                self._update_warming_score(project_path)

            logger.debug(
                f"Tracked session end for {project_path}: {session_duration:.1f}s"
            )

        except Exception as e:
            logger.error(f"Error tracking session end: {e}")

    def _update_warming_score(self, project_path: str):
        """Update the warming priority score for a project"""
        try:
            if project_path not in self.project_stats:
                return

            stats = self.project_stats[project_path]
            strategy = self.strategies[self.current_strategy]
            current_time = datetime.now()

            # Recency score (0-1): Higher for more recently accessed projects
            days_since_access = (current_time - stats.last_access).days
            recency_score = max(0, 1.0 - (days_since_access / 30))  # Decay over 30 days

            # Frequency score (0-1): Based on access count
            frequency_score = min(1.0, stats.access_count / 10)  # Cap at 10 accesses

            # Session quality score (0-1): Based on session duration and activity
            min_quality_time = strategy.min_total_session_time
            session_quality_score = min(
                1.0, stats.total_session_time / min_quality_time
            )

            # Activity score bonus for files/symbols/analysis
            activity_bonus = min(
                0.2,
                (stats.files_accessed + stats.symbols_queried + stats.analysis_requests)
                / 100,
            )

            # Calculate weighted warming score
            warming_score = (
                recency_score * strategy.recency_weight
                + frequency_score * strategy.frequency_weight
                + session_quality_score * strategy.session_quality_weight
                + activity_bonus
            )

            stats.warming_score = warming_score

            logger.debug(
                f"Updated warming score for {project_path}: {warming_score:.3f}"
            )

        except Exception as e:
            logger.error(f"Error updating warming score: {e}")

    async def queue_warming_task(
        self, project_path: str, priority_override: Optional[float] = None
    ):
        """Queue a project for cache warming"""
        try:
            project_path = str(Path(project_path).absolute())

            # Check if project is eligible for warming
            if not self._is_eligible_for_warming(project_path):
                logger.debug(f"Project {project_path} not eligible for warming")
                return False

            # Check if already warming or recently warmed
            if self._is_recently_warmed(project_path):
                logger.debug(f"Project {project_path} recently warmed, skipping")
                return False

            # Check if already in queue
            for task in self.warming_queue:
                if task.project_path == project_path:
                    logger.debug(f"Project {project_path} already in warming queue")
                    return False

            # Create warming task
            task_id = self._generate_task_id(project_path)
            priority_score = (
                priority_override or self.project_stats[project_path].warming_score
            )

            task = WarmingTask(
                task_id=task_id,
                project_path=project_path,
                strategy=self.current_strategy,
                priority_score=priority_score,
                created_at=datetime.now(),
            )

            # Insert in priority order
            self._insert_task_by_priority(task)

            logger.info(
                f"Queued warming task for {project_path} with priority {priority_score:.3f}"
            )
            return True

        except Exception as e:
            logger.error(f"Error queueing warming task: {e}")
            return False

    def _is_eligible_for_warming(self, project_path: str) -> bool:
        """Check if a project is eligible for cache warming"""
        try:
            if project_path not in self.project_stats:
                return False

            stats = self.project_stats[project_path]
            strategy = self.strategies[self.current_strategy]

            # Check minimum requirements
            return (
                stats.access_count >= strategy.min_access_count
                and stats.total_session_time >= strategy.min_total_session_time
                and stats.warming_score > 0.3  # Minimum warming score threshold
            )

        except Exception as e:
            logger.error(f"Error checking warming eligibility: {e}")
            return False

    def _is_recently_warmed(self, project_path: str) -> bool:
        """Check if a project was recently warmed"""
        try:
            if project_path not in self.project_stats:
                return False

            stats = self.project_stats[project_path]
            if not stats.last_warmed:
                return False

            strategy = self.strategies[self.current_strategy]
            warming_interval = timedelta(hours=strategy.warming_interval_hours)

            return (datetime.now() - stats.last_warmed) < warming_interval

        except Exception as e:
            logger.error(f"Error checking recent warming: {e}")
            return False

    def _insert_task_by_priority(self, task: WarmingTask):
        """Insert task in queue maintaining priority order"""
        try:
            # Insert in descending priority order
            inserted = False
            for i, queued_task in enumerate(self.warming_queue):
                if task.priority_score > queued_task.priority_score:
                    self.warming_queue.insert(i, task)
                    inserted = True
                    break

            if not inserted:
                self.warming_queue.append(task)

        except Exception as e:
            logger.error(f"Error inserting task by priority: {e}")
            self.warming_queue.append(task)  # Fallback

    async def _start_background_tasks(self):
        """Start background warming and cleanup tasks"""
        try:
            # Start warming processor
            self.warming_background_task = asyncio.create_task(
                self._warming_processor()
            )

            # Start periodic cleanup
            self.stats_cleanup_task = asyncio.create_task(self._periodic_cleanup())

            self.metrics["background_warming_active"] = True
            logger.info("Started background warming tasks")

        except Exception as e:
            logger.error(f"Error starting background tasks: {e}")

    async def _warming_processor(self):
        """Background task to process warming queue"""
        try:
            while True:
                await self._process_warming_queue()

                # Wait before next processing cycle
                await asyncio.sleep(30)  # Process every 30 seconds

        except asyncio.CancelledError:
            logger.info("Warming processor cancelled")
        except Exception as e:
            logger.error(f"Error in warming processor: {e}")

    async def _process_warming_queue(self):
        """Process items in the warming queue"""
        try:
            strategy = self.strategies[self.current_strategy]

            # Check if we can start new warming tasks
            active_count = len(self.active_warming_tasks)
            if active_count >= strategy.max_concurrent_warming:
                return

            # Start warming tasks up to the limit
            tasks_to_start = min(
                len(self.warming_queue), strategy.max_concurrent_warming - active_count
            )

            for _ in range(tasks_to_start):
                if not self.warming_queue:
                    break

                task = self.warming_queue.popleft()
                await self._start_warming_task(task)

        except Exception as e:
            logger.error(f"Error processing warming queue: {e}")

    async def _start_warming_task(self, task: WarmingTask):
        """Start a cache warming task"""
        try:
            task.started_at = datetime.now()
            self.active_warming_tasks[task.task_id] = task

            logger.info(f"Starting cache warming for {task.project_path}")

            # Create warming task
            warming_task = asyncio.create_task(self._execute_warming(task))

            # Don't await here - let it run in background
            warming_task.add_done_callback(
                lambda t: asyncio.create_task(self._warming_task_completed(task, t))
            )

        except Exception as e:
            logger.error(f"Error starting warming task {task.task_id}: {e}")
            await self._mark_task_failed(task, str(e))

    async def _execute_warming(self, task: WarmingTask):
        """Execute the actual cache warming for a project"""
        try:
            start_time = time.time()

            # Import here to avoid circular imports
            from .incremental_indexer import incremental_indexer

            # Warm the project cache
            project_index = await incremental_indexer.get_or_create_project_index(
                task.project_path, force_full_reindex=False
            )

            if project_index:
                task.files_warmed = project_index.supported_files
                task.success = True

                # Update project statistics
                if task.project_path in self.project_stats:
                    self.project_stats[task.project_path].last_warmed = datetime.now()
                    self.project_stats[task.project_path].warming_success_rate = min(
                        1.0,
                        self.project_stats[task.project_path].warming_success_rate
                        + 0.1,
                    )

                logger.info(
                    f"Successfully warmed cache for {task.project_path}: {task.files_warmed} files"
                )
            else:
                raise Exception("Failed to generate project index")

            task.warming_time_seconds = time.time() - start_time

        except Exception as e:
            task.success = False
            task.error_message = str(e)
            task.warming_time_seconds = time.time() - start_time
            logger.error(f"Error warming cache for {task.project_path}: {e}")

    async def _warming_task_completed(
        self, task: WarmingTask, async_task: asyncio.Task
    ):
        """Handle completion of a warming task"""
        try:
            task.completed_at = datetime.now()

            # Remove from active tasks
            if task.task_id in self.active_warming_tasks:
                del self.active_warming_tasks[task.task_id]

            # Update metrics
            self.metrics["total_warming_tasks"] += 1
            if task.success:
                self.metrics["successful_warmings"] += 1

                # Update average warming time
                current_avg = self.metrics["average_warming_time"]
                new_avg = (current_avg + task.warming_time_seconds) / 2
                self.metrics["average_warming_time"] = new_avg
            else:
                self.metrics["failed_warmings"] += 1

            # Add to completed tasks history
            self.completed_tasks.append(task)
            if len(self.completed_tasks) > self.max_completed_history:
                self.completed_tasks = self.completed_tasks[
                    -self.max_completed_history :
                ]

            logger.info(
                f"Warming task completed for {task.project_path}: "
                f"{'success' if task.success else 'failed'} in {task.warming_time_seconds:.1f}s"
            )

        except Exception as e:
            logger.error(f"Error handling warming task completion: {e}")

    async def _mark_task_failed(self, task: WarmingTask, error: str):
        """Mark a warming task as failed"""
        try:
            task.success = False
            task.error_message = error
            task.completed_at = datetime.now()

            await self._warming_task_completed(task, None)

        except Exception as e:
            logger.error(f"Error marking task as failed: {e}")

    async def _periodic_cleanup(self):
        """Periodic cleanup of old statistics and tasks"""
        try:
            while True:
                await asyncio.sleep(3600)  # Run every hour

                await self._cleanup_old_statistics()
                await self._save_project_stats()

        except asyncio.CancelledError:
            logger.info("Periodic cleanup cancelled")
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

    async def _cleanup_old_statistics(self):
        """Clean up old project statistics"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(days=90)  # Keep 90 days

            projects_to_remove = []
            for project_path, stats in self.project_stats.items():
                if stats.last_access < cutoff_time and stats.access_count < 5:
                    projects_to_remove.append(project_path)

            for project_path in projects_to_remove:
                del self.project_stats[project_path]
                self.metrics["total_projects_tracked"] -= 1

            if projects_to_remove:
                logger.info(
                    f"Cleaned up {len(projects_to_remove)} old project statistics"
                )

        except Exception as e:
            logger.error(f"Error cleaning up statistics: {e}")

    def _generate_task_id(self, project_path: str) -> str:
        """Generate a unique task ID"""
        timestamp = int(time.time() * 1000)
        path_hash = hashlib.md5(project_path.encode()).hexdigest()[:8]
        return f"warm_{timestamp}_{path_hash}"

    async def _load_project_stats(self):
        """Load project statistics from storage"""
        try:
            stats_file = self.storage_dir / "project_usage_stats.json"

            if not stats_file.exists():
                logger.debug("No existing project statistics found")
                return

            async with aiofiles.open(stats_file, "r") as f:
                data = json.loads(await f.read())

            for project_path, stats_data in data.items():
                # Convert datetime strings back to datetime objects
                stats_data["first_access"] = datetime.fromisoformat(
                    stats_data["first_access"]
                )
                stats_data["last_access"] = datetime.fromisoformat(
                    stats_data["last_access"]
                )

                if stats_data.get("last_warmed"):
                    stats_data["last_warmed"] = datetime.fromisoformat(
                        stats_data["last_warmed"]
                    )

                self.project_stats[project_path] = ProjectUsageStats(**stats_data)

            logger.info(f"Loaded statistics for {len(self.project_stats)} projects")

        except Exception as e:
            logger.error(f"Error loading project statistics: {e}")

    async def _save_project_stats(self):
        """Save project statistics to storage"""
        try:
            stats_file = self.storage_dir / "project_usage_stats.json"

            # Convert to serializable format
            data = {}
            for project_path, stats in self.project_stats.items():
                stats_dict = asdict(stats)
                # Convert datetime objects to strings
                stats_dict["first_access"] = stats.first_access.isoformat()
                stats_dict["last_access"] = stats.last_access.isoformat()

                if stats.last_warmed:
                    stats_dict["last_warmed"] = stats.last_warmed.isoformat()

                data[project_path] = stats_dict

            async with aiofiles.open(stats_file, "w") as f:
                await f.write(json.dumps(data, indent=2))

            logger.debug(f"Saved statistics for {len(self.project_stats)} projects")

        except Exception as e:
            logger.error(f"Error saving project statistics: {e}")

    def get_warming_candidates(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top candidates for cache warming"""
        try:
            candidates = []

            for project_path, stats in self.project_stats.items():
                if self._is_eligible_for_warming(
                    project_path
                ) and not self._is_recently_warmed(project_path):

                    candidates.append(
                        {
                            "project_path": project_path,
                            "warming_score": stats.warming_score,
                            "access_count": stats.access_count,
                            "last_access": stats.last_access.isoformat(),
                            "total_session_time": stats.total_session_time,
                            "files_accessed": stats.files_accessed,
                        }
                    )

            # Sort by warming score descending
            candidates.sort(key=lambda x: x["warming_score"], reverse=True)

            return candidates[:limit]

        except Exception as e:
            logger.error(f"Error getting warming candidates: {e}")
            return []

    def get_metrics(self) -> Dict[str, Any]:
        """Get cache warming metrics"""
        try:
            strategy = self.strategies[self.current_strategy]

            return {
                **self.metrics,
                "current_strategy": self.current_strategy,
                "queue_size": len(self.warming_queue),
                "active_tasks": len(self.active_warming_tasks),
                "completed_tasks": len(self.completed_tasks),
                "strategy_config": asdict(strategy),
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}

    def set_warming_strategy(self, strategy_name: str) -> bool:
        """Set the cache warming strategy"""
        try:
            if strategy_name not in self.strategies:
                logger.error(f"Unknown warming strategy: {strategy_name}")
                return False

            self.current_strategy = strategy_name
            logger.info(f"Set cache warming strategy to: {strategy_name}")

            return True

        except Exception as e:
            logger.error(f"Error setting warming strategy: {e}")
            return False

    async def save_cache_with_persistence(
        self, cache_data: Dict[str, Any], cache_key: str = "warming_cache"
    ) -> bool:
        """Save cache data using persistence service"""
        try:
            if not self.persistence_enabled:
                return True

            # Create cache metadata
            metadata = {
                cache_key: CacheMetadata(
                    key=cache_key,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    status=CacheStatus.VALID,
                    priority=CachePriority.HIGH,
                    tags=["cache_warming", "project_stats"],
                    version="1.0",
                )
            }

            # Save using persistence service
            success = await cache_persistence_service.save_cache(
                {cache_key: cache_data}, metadata, CacheFormat.COMPRESSED_PICKLE
            )

            if success:
                self.last_persistence_save = datetime.now()
                logger.debug(f"Cache data saved for key: {cache_key}")

            return success

        except Exception as e:
            logger.error(f"Error saving cache with persistence: {e}")
            return False

    async def load_cache_with_persistence(
        self, cache_key: str = "warming_cache"
    ) -> Optional[Dict[str, Any]]:
        """Load cache data using persistence service"""
        try:
            if not self.persistence_enabled:
                return None

            # Load using persistence service
            cache_data, metadata = await cache_persistence_service.load_cache(
                CacheFormat.COMPRESSED_PICKLE
            )

            if cache_data and cache_key in cache_data:
                logger.debug(f"Cache data loaded for key: {cache_key}")
                return cache_data[cache_key]

            return None

        except Exception as e:
            logger.error(f"Error loading cache with persistence: {e}")
            return None

    async def create_persistence_checkpoint(self) -> bool:
        """Create a persistence checkpoint for current cache state"""
        try:
            if not self.persistence_enabled:
                return True

            # Prepare current state for persistence
            cache_data = {
                "project_stats": {
                    path: asdict(stats) for path, stats in self.project_stats.items()
                },
                "metrics": self.metrics.copy(),
                "current_strategy": self.current_strategy,
                "warming_queue": [asdict(task) for task in self.warming_queue],
                "completed_tasks": [
                    asdict(task) for task in self.completed_tasks[-50:]
                ],  # Last 50 tasks
            }

            # Save with checkpoint
            success = await self.save_cache_with_persistence(
                cache_data, "warming_state"
            )

            if success:
                # Create checkpoint
                checkpoint = await cache_persistence_service.create_checkpoint(
                    force=True
                )
                if checkpoint:
                    logger.info(
                        f"Created persistence checkpoint: {checkpoint.checkpoint_id}"
                    )
                    return True

            return success

        except Exception as e:
            logger.error(f"Error creating persistence checkpoint: {e}")
            return False

    async def recover_from_persistence(self) -> bool:
        """Recover cache warming state from persistence"""
        try:
            if not self.persistence_enabled:
                return True

            logger.info("Attempting to recover cache warming state from persistence")

            # Try to load saved state
            cache_data = await self.load_cache_with_persistence("warming_state")

            if cache_data:
                # Restore project stats
                if "project_stats" in cache_data:
                    for path, stats_dict in cache_data["project_stats"].items():
                        # Convert dict back to ProjectUsageStats
                        stats_dict["first_access"] = datetime.fromisoformat(
                            stats_dict["first_access"]
                        )
                        stats_dict["last_access"] = datetime.fromisoformat(
                            stats_dict["last_access"]
                        )
                        if stats_dict.get("last_warmed"):
                            stats_dict["last_warmed"] = datetime.fromisoformat(
                                stats_dict["last_warmed"]
                            )

                        self.project_stats[path] = ProjectUsageStats(**stats_dict)

                # Restore metrics
                if "metrics" in cache_data:
                    self.metrics.update(cache_data["metrics"])

                # Restore strategy
                if "current_strategy" in cache_data:
                    self.current_strategy = cache_data["current_strategy"]

                # Restore completed tasks (for metrics)
                if "completed_tasks" in cache_data:
                    for task_dict in cache_data["completed_tasks"]:
                        task_dict["created_at"] = datetime.fromisoformat(
                            task_dict["created_at"]
                        )
                        if task_dict.get("completed_at"):
                            task_dict["completed_at"] = datetime.fromisoformat(
                                task_dict["completed_at"]
                            )
                        self.completed_tasks.append(WarmingTask(**task_dict))

                logger.info(
                    f"Recovered cache warming state: {len(self.project_stats)} projects, strategy: {self.current_strategy}"
                )
                return True

            else:
                # Try recovery from checkpoints
                recovery_result = await cache_persistence_service.recover_cache()
                if recovery_result.success:
                    logger.info(
                        f"Recovered from checkpoint: {recovery_result.recovered_entries} entries"
                    )
                    return await self.recover_from_persistence()  # Try loading again

            return False

        except Exception as e:
            logger.error(f"Error recovering from persistence: {e}")
            return False

    async def auto_persist_if_needed(self) -> bool:
        """Automatically persist cache if enough time has passed"""
        try:
            if not self.persistence_enabled:
                return True

            current_time = datetime.now()
            time_since_save = (
                current_time - self.last_persistence_save
            ).total_seconds() / 60

            if time_since_save >= self.auto_persistence_interval_minutes:
                logger.debug("Auto-persisting cache warming state")
                return await self.create_persistence_checkpoint()

            return True

        except Exception as e:
            logger.error(f"Error in auto-persist: {e}")
            return False

    def get_persistence_metrics(self) -> Dict[str, Any]:
        """Get cache persistence metrics"""
        try:
            base_metrics = cache_persistence_service.get_metrics()

            # Add cache warming specific metrics
            warming_metrics = {
                "persistence_enabled": self.persistence_enabled,
                "last_persistence_save": (
                    self.last_persistence_save.isoformat()
                    if self.last_persistence_save
                    else None
                ),
                "auto_persistence_interval_minutes": self.auto_persistence_interval_minutes,
                "warming_project_count": len(self.project_stats),
                "warming_queue_size": len(self.warming_queue),
                "completed_task_count": len(self.completed_tasks),
            }

            return {**base_metrics, **warming_metrics}

        except Exception as e:
            logger.error(f"Error getting persistence metrics: {e}")
            return {"error": str(e)}


# Global instance
cache_warming_service = SmartCacheWarmingService()
