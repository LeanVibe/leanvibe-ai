"""
Cache Persistence and Recovery Service

Provides robust cache persistence, recovery mechanisms, and fault tolerance
for the LeenVibe backend caching system.
"""

import asyncio
import logging
import json
import pickle
import gzip
import time
import hashlib
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
import os

import aiofiles

from ..models.ast_models import ProjectIndex, FileAnalysis
from ..models.cache_models import CacheEntry, CacheMetadata, CacheStatistics

logger = logging.getLogger(__name__)


class CacheFormat(str, Enum):
    """Cache persistence formats"""
    JSON = "json"
    PICKLE = "pickle"
    COMPRESSED_PICKLE = "compressed_pickle"


class RecoveryStrategy(str, Enum):
    """Cache recovery strategies"""
    FULL_RECOVERY = "full_recovery"
    PARTIAL_RECOVERY = "partial_recovery"
    REBUILD_ON_FAILURE = "rebuild_on_failure"
    SKIP_CORRUPTED = "skip_corrupted"


@dataclass
class CacheCheckpoint:
    """Represents a cache state checkpoint"""
    checkpoint_id: str
    timestamp: datetime
    cache_size: int
    cache_version: str
    format: CacheFormat
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryResult:
    """Result of cache recovery operation"""
    success: bool
    recovered_entries: int
    skipped_entries: int
    corrupted_entries: int
    total_entries: int
    recovery_time_ms: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class PersistenceMetrics:
    """Cache persistence performance metrics"""
    total_saves: int = 0
    total_loads: int = 0
    successful_saves: int = 0
    successful_loads: int = 0
    failed_saves: int = 0
    failed_loads: int = 0
    average_save_time_ms: float = 0.0
    average_load_time_ms: float = 0.0
    total_bytes_saved: int = 0
    total_bytes_loaded: int = 0
    compression_ratio: float = 0.0
    last_checkpoint: Optional[datetime] = None


class CachePersistenceService:
    """
    Cache Persistence and Recovery Service
    
    Handles saving and loading cache data with fault tolerance,
    corruption detection, and automatic recovery mechanisms.
    """
    
    def __init__(self, cache_dir: str = ".cache/leenvibe"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Persistence configuration
        self.default_format = CacheFormat.COMPRESSED_PICKLE
        self.checkpoint_interval_minutes = 30
        self.max_checkpoints = 10
        self.compression_level = 6
        self.backup_on_save = True
        
        # Recovery configuration  
        self.default_recovery_strategy = RecoveryStrategy.PARTIAL_RECOVERY
        self.max_recovery_attempts = 3
        self.corruption_threshold = 0.1  # 10% corruption tolerance
        
        # Internal state
        self.checkpoints: List[CacheCheckpoint] = []
        self.metrics = PersistenceMetrics()
        self.last_checkpoint_time = datetime.now()
        self.persistence_lock = threading.Lock()
        
        # Cache state
        self.cached_data: Dict[str, Any] = {}
        self.cache_metadata: Dict[str, CacheMetadata] = {}
        
        # Initialize persistence
        self._load_checkpoints()
    
    async def save_cache(
        self, 
        cache_data: Dict[str, Any], 
        metadata: Optional[Dict[str, CacheMetadata]] = None,
        format: Optional[CacheFormat] = None,
        create_checkpoint: bool = True
    ) -> bool:
        """Save cache data to persistent storage"""
        try:
            start_time = time.time()
            save_format = format or self.default_format
            
            logger.info(f"Saving cache with {len(cache_data)} entries using {save_format}")
            
            with self.persistence_lock:
                # Create backup if enabled
                if self.backup_on_save:
                    await self._create_backup()
                
                # Save main cache data
                cache_file = self.cache_dir / f"cache_data.{save_format}"
                success = await self._save_cache_file(cache_data, cache_file, save_format)
                
                if success and metadata:
                    # Save metadata separately
                    metadata_file = self.cache_dir / "cache_metadata.json"
                    success = await self._save_metadata(metadata, metadata_file)
                
                if success and create_checkpoint:
                    # Create checkpoint
                    checkpoint = await self._create_checkpoint(cache_data, save_format)
                    self.checkpoints.append(checkpoint)
                    await self._cleanup_old_checkpoints()
                
                # Update metrics
                self.metrics.total_saves += 1
                if success:
                    self.metrics.successful_saves += 1
                    self.metrics.last_checkpoint = datetime.now()
                else:
                    self.metrics.failed_saves += 1
                
                save_time = (time.time() - start_time) * 1000
                self._update_save_metrics(save_time, len(cache_data))
                
                return success
                
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
            self.metrics.failed_saves += 1
            return False
    
    async def load_cache(
        self, 
        format: Optional[CacheFormat] = None,
        recovery_strategy: Optional[RecoveryStrategy] = None
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, CacheMetadata]]]:
        """Load cache data from persistent storage"""
        try:
            start_time = time.time()
            load_format = format or self.default_format
            strategy = recovery_strategy or self.default_recovery_strategy
            
            logger.info(f"Loading cache using {load_format} with {strategy} recovery")
            
            with self.persistence_lock:
                # Try to load main cache file
                cache_file = self.cache_dir / f"cache_data.{load_format}"
                cache_data = await self._load_cache_file(cache_file, load_format)
                
                # Try to load metadata
                metadata_file = self.cache_dir / "cache_metadata.json"
                metadata = await self._load_metadata(metadata_file)
                
                # If main load failed, try recovery
                if cache_data is None:
                    recovery_result = await self.recover_cache(strategy)
                    if recovery_result.success:
                        cache_data = self.cached_data
                        metadata = self.cache_metadata
                    else:
                        cache_data = {}
                        metadata = {}
                
                # Update metrics
                self.metrics.total_loads += 1
                if cache_data is not None:
                    self.metrics.successful_loads += 1
                else:
                    self.metrics.failed_loads += 1
                
                load_time = (time.time() - start_time) * 1000
                self._update_load_metrics(load_time, len(cache_data) if cache_data else 0)
                
                return cache_data or {}, metadata
                
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self.metrics.failed_loads += 1
            return {}, {}
    
    async def recover_cache(
        self, 
        strategy: Optional[RecoveryStrategy] = None
    ) -> RecoveryResult:
        """Recover cache from checkpoints and backups"""
        try:
            start_time = time.time()
            strategy = strategy or self.default_recovery_strategy
            
            logger.info(f"Starting cache recovery with strategy: {strategy}")
            
            result = RecoveryResult(
                success=False,
                recovered_entries=0,
                skipped_entries=0,
                corrupted_entries=0,
                total_entries=0,
                recovery_time_ms=0.0
            )
            
            if strategy == RecoveryStrategy.FULL_RECOVERY:
                result = await self._full_recovery()
            elif strategy == RecoveryStrategy.PARTIAL_RECOVERY:
                result = await self._partial_recovery()
            elif strategy == RecoveryStrategy.REBUILD_ON_FAILURE:
                result = await self._rebuild_recovery()
            elif strategy == RecoveryStrategy.SKIP_CORRUPTED:
                result = await self._skip_corrupted_recovery()
            
            result.recovery_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Cache recovery completed: {result.recovered_entries}/{result.total_entries} entries recovered")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during cache recovery: {e}")
            return RecoveryResult(
                success=False,
                recovered_entries=0,
                skipped_entries=0,
                corrupted_entries=0,
                total_entries=0,
                recovery_time_ms=0.0,
                errors=[str(e)]
            )
    
    async def create_checkpoint(self, force: bool = False) -> Optional[CacheCheckpoint]:
        """Create a cache checkpoint"""
        try:
            current_time = datetime.now()
            time_since_last = (current_time - self.last_checkpoint_time).total_seconds() / 60
            
            if not force and time_since_last < self.checkpoint_interval_minutes:
                return None
            
            logger.info("Creating cache checkpoint")
            
            checkpoint = await self._create_checkpoint(
                self.cached_data, 
                self.default_format
            )
            
            self.checkpoints.append(checkpoint)
            self.last_checkpoint_time = current_time
            
            await self._cleanup_old_checkpoints()
            await self._save_checkpoint_index()
            
            return checkpoint
            
        except Exception as e:
            logger.error(f"Error creating checkpoint: {e}")
            return None
    
    async def list_checkpoints(self) -> List[CacheCheckpoint]:
        """List available cache checkpoints"""
        return self.checkpoints.copy()
    
    async def restore_from_checkpoint(self, checkpoint_id: str) -> bool:
        """Restore cache from a specific checkpoint"""
        try:
            checkpoint = next((cp for cp in self.checkpoints if cp.checkpoint_id == checkpoint_id), None)
            if not checkpoint:
                logger.error(f"Checkpoint {checkpoint_id} not found")
                return False
            
            logger.info(f"Restoring cache from checkpoint {checkpoint_id}")
            
            checkpoint_file = self.cache_dir / "checkpoints" / f"{checkpoint_id}.cache"
            if not checkpoint_file.exists():
                logger.error(f"Checkpoint file {checkpoint_file} not found")
                return False
            
            cache_data = await self._load_cache_file(checkpoint_file, checkpoint.format)
            if cache_data is None:
                return False
            
            # Verify checksum
            if not await self._verify_checksum(cache_data, checkpoint.checksum):
                logger.error(f"Checksum verification failed for checkpoint {checkpoint_id}")
                return False
            
            self.cached_data = cache_data
            return True
            
        except Exception as e:
            logger.error(f"Error restoring from checkpoint: {e}")
            return False
    
    async def verify_cache_integrity(self) -> Dict[str, Any]:
        """Verify integrity of cached data"""
        try:
            logger.info("Verifying cache integrity")
            
            integrity_report = {
                "total_entries": len(self.cached_data),
                "valid_entries": 0,
                "corrupted_entries": 0,
                "missing_metadata": 0,
                "checksum_failures": 0,
                "details": []
            }
            
            for key, data in self.cached_data.items():
                try:
                    # Basic structure validation
                    if not isinstance(data, dict):
                        integrity_report["corrupted_entries"] += 1
                        integrity_report["details"].append(f"Invalid data structure for key: {key}")
                        continue
                    
                    # Metadata validation
                    if key not in self.cache_metadata:
                        integrity_report["missing_metadata"] += 1
                        integrity_report["details"].append(f"Missing metadata for key: {key}")
                    
                    # Content validation (if applicable)
                    if "data" in data and isinstance(data["data"], dict):
                        # Additional validation can be added here
                        pass
                    
                    integrity_report["valid_entries"] += 1
                    
                except Exception as e:
                    integrity_report["corrupted_entries"] += 1
                    integrity_report["details"].append(f"Validation error for key {key}: {str(e)}")
            
            return integrity_report
            
        except Exception as e:
            logger.error(f"Error verifying cache integrity: {e}")
            return {"error": str(e)}
    
    async def cleanup_cache(self, max_age_days: int = 30) -> Dict[str, int]:
        """Clean up old cache entries and checkpoints"""
        try:
            logger.info(f"Cleaning up cache entries older than {max_age_days} days")
            
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            cleanup_stats = {
                "removed_entries": 0,
                "removed_checkpoints": 0,
                "freed_bytes": 0
            }
            
            # Clean up old cache entries
            keys_to_remove = []
            for key, metadata in self.cache_metadata.items():
                if metadata.created_at < cutoff_date:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                if key in self.cached_data:
                    del self.cached_data[key]
                if key in self.cache_metadata:
                    del self.cache_metadata[key]
                cleanup_stats["removed_entries"] += 1
            
            # Clean up old checkpoints
            checkpoints_to_remove = []
            for checkpoint in self.checkpoints:
                if checkpoint.timestamp < cutoff_date:
                    checkpoints_to_remove.append(checkpoint)
            
            for checkpoint in checkpoints_to_remove:
                checkpoint_file = self.cache_dir / "checkpoints" / f"{checkpoint.checkpoint_id}.cache"
                if checkpoint_file.exists():
                    cleanup_stats["freed_bytes"] += checkpoint_file.stat().st_size
                    checkpoint_file.unlink()
                self.checkpoints.remove(checkpoint)
                cleanup_stats["removed_checkpoints"] += 1
            
            await self._save_checkpoint_index()
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
            return {"error": str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache persistence metrics"""
        return asdict(self.metrics)
    
    async def _save_cache_file(
        self, 
        data: Any, 
        file_path: Path, 
        format: CacheFormat
    ) -> bool:
        """Save data to cache file in specified format"""
        try:
            if format == CacheFormat.JSON:
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(data, default=str, indent=2))
            
            elif format == CacheFormat.PICKLE:
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(pickle.dumps(data))
            
            elif format == CacheFormat.COMPRESSED_PICKLE:
                pickled_data = pickle.dumps(data)
                compressed_data = gzip.compress(pickled_data, compresslevel=self.compression_level)
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(compressed_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving cache file {file_path}: {e}")
            return False
    
    async def _load_cache_file(
        self, 
        file_path: Path, 
        format: CacheFormat
    ) -> Optional[Any]:
        """Load data from cache file in specified format"""
        try:
            if not file_path.exists():
                return None
            
            if format == CacheFormat.JSON:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    return json.loads(content)
            
            elif format == CacheFormat.PICKLE:
                async with aiofiles.open(file_path, 'rb') as f:
                    content = await f.read()
                    return pickle.loads(content)
            
            elif format == CacheFormat.COMPRESSED_PICKLE:
                async with aiofiles.open(file_path, 'rb') as f:
                    compressed_data = await f.read()
                    pickled_data = gzip.decompress(compressed_data)
                    return pickle.loads(pickled_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading cache file {file_path}: {e}")
            return None
    
    async def _save_metadata(
        self, 
        metadata: Dict[str, CacheMetadata], 
        file_path: Path
    ) -> bool:
        """Save cache metadata to JSON file"""
        try:
            metadata_dict = {
                key: asdict(meta) for key, meta in metadata.items()
            }
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(metadata_dict, default=str, indent=2))
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            return False
    
    async def _load_metadata(self, file_path: Path) -> Optional[Dict[str, CacheMetadata]]:
        """Load cache metadata from JSON file"""
        try:
            if not file_path.exists():
                return {}
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                metadata_dict = json.loads(content)
            
            # Convert back to CacheMetadata objects
            metadata = {}
            for key, meta_dict in metadata_dict.items():
                # Convert datetime strings back to datetime objects
                if 'created_at' in meta_dict:
                    meta_dict['created_at'] = datetime.fromisoformat(meta_dict['created_at'])
                if 'last_accessed' in meta_dict:
                    meta_dict['last_accessed'] = datetime.fromisoformat(meta_dict['last_accessed'])
                if 'expires_at' in meta_dict and meta_dict['expires_at']:
                    meta_dict['expires_at'] = datetime.fromisoformat(meta_dict['expires_at'])
                
                metadata[key] = CacheMetadata(**meta_dict)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return {}
    
    async def _create_checkpoint(
        self, 
        cache_data: Dict[str, Any], 
        format: CacheFormat
    ) -> CacheCheckpoint:
        """Create a new cache checkpoint"""
        checkpoint_id = f"checkpoint_{int(time.time())}_{hashlib.md5(str(cache_data).encode()).hexdigest()[:8]}"
        
        # Create checkpoints directory
        checkpoints_dir = self.cache_dir / "checkpoints"
        checkpoints_dir.mkdir(exist_ok=True)
        
        # Save checkpoint data
        checkpoint_file = checkpoints_dir / f"{checkpoint_id}.cache"
        await self._save_cache_file(cache_data, checkpoint_file, format)
        
        # Calculate checksum
        checksum = await self._calculate_checksum(cache_data)
        
        return CacheCheckpoint(
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now(),
            cache_size=len(cache_data),
            cache_version="1.0",
            format=format,
            checksum=checksum,
            metadata={
                "file_size": checkpoint_file.stat().st_size if checkpoint_file.exists() else 0
            }
        )
    
    async def _calculate_checksum(self, data: Any) -> str:
        """Calculate checksum for data"""
        try:
            data_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(data_str.encode()).hexdigest()
        except Exception:
            # Fallback for non-serializable data
            return hashlib.sha256(str(data).encode()).hexdigest()
    
    async def _verify_checksum(self, data: Any, expected_checksum: str) -> bool:
        """Verify data checksum"""
        try:
            actual_checksum = await self._calculate_checksum(data)
            return actual_checksum == expected_checksum
        except Exception as e:
            logger.error(f"Error verifying checksum: {e}")
            return False
    
    async def _cleanup_old_checkpoints(self):
        """Remove old checkpoints beyond max limit"""
        if len(self.checkpoints) <= self.max_checkpoints:
            return
        
        # Sort by timestamp and keep only the newest ones
        self.checkpoints.sort(key=lambda cp: cp.timestamp, reverse=True)
        checkpoints_to_remove = self.checkpoints[self.max_checkpoints:]
        self.checkpoints = self.checkpoints[:self.max_checkpoints]
        
        # Remove checkpoint files
        for checkpoint in checkpoints_to_remove:
            checkpoint_file = self.cache_dir / "checkpoints" / f"{checkpoint.checkpoint_id}.cache"
            if checkpoint_file.exists():
                checkpoint_file.unlink()
    
    async def _save_checkpoint_index(self):
        """Save checkpoint index to file"""
        try:
            index_file = self.cache_dir / "checkpoint_index.json"
            checkpoints_data = [asdict(cp) for cp in self.checkpoints]
            
            async with aiofiles.open(index_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(checkpoints_data, default=str, indent=2))
        
        except Exception as e:
            logger.error(f"Error saving checkpoint index: {e}")
    
    def _load_checkpoints(self):
        """Load checkpoint index from file"""
        try:
            index_file = self.cache_dir / "checkpoint_index.json"
            if not index_file.exists():
                return
            
            with open(index_file, 'r', encoding='utf-8') as f:
                checkpoints_data = json.load(f)
            
            self.checkpoints = []
            for cp_data in checkpoints_data:
                # Convert timestamp string back to datetime
                if 'timestamp' in cp_data:
                    cp_data['timestamp'] = datetime.fromisoformat(cp_data['timestamp'])
                
                self.checkpoints.append(CacheCheckpoint(**cp_data))
        
        except Exception as e:
            logger.error(f"Error loading checkpoint index: {e}")
            self.checkpoints = []
    
    async def _create_backup(self):
        """Create backup of current cache files"""
        try:
            backup_dir = self.cache_dir / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup main cache files
            for file_name in ["cache_data.json", "cache_data.pickle", "cache_data.compressed_pickle", "cache_metadata.json"]:
                source_file = self.cache_dir / file_name
                if source_file.exists():
                    backup_file = backup_dir / f"{timestamp}_{file_name}"
                    async with aiofiles.open(source_file, 'rb') as src:
                        content = await src.read()
                        async with aiofiles.open(backup_file, 'wb') as dst:
                            await dst.write(content)
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
    
    async def _full_recovery(self) -> RecoveryResult:
        """Attempt full cache recovery from all sources"""
        result = RecoveryResult(
            success=False,
            recovered_entries=0,
            skipped_entries=0,
            corrupted_entries=0,
            total_entries=0,
            recovery_time_ms=0.0
        )
        
        # Try checkpoints first (newest to oldest)
        for checkpoint in sorted(self.checkpoints, key=lambda cp: cp.timestamp, reverse=True):
            checkpoint_file = self.cache_dir / "checkpoints" / f"{checkpoint.checkpoint_id}.cache"
            if checkpoint_file.exists():
                cache_data = await self._load_cache_file(checkpoint_file, checkpoint.format)
                if cache_data and await self._verify_checksum(cache_data, checkpoint.checksum):
                    self.cached_data = cache_data
                    result.success = True
                    result.recovered_entries = len(cache_data)
                    result.total_entries = len(cache_data)
                    return result
        
        # Try backups
        backup_dir = self.cache_dir / "backups"
        if backup_dir.exists():
            for backup_file in sorted(backup_dir.glob("*_cache_data.*"), reverse=True):
                format_ext = backup_file.suffix.lstrip('.')
                if format_ext in [f.value for f in CacheFormat]:
                    cache_data = await self._load_cache_file(backup_file, CacheFormat(format_ext))
                    if cache_data:
                        self.cached_data = cache_data
                        result.success = True
                        result.recovered_entries = len(cache_data)
                        result.total_entries = len(cache_data)
                        return result
        
        return result
    
    async def _partial_recovery(self) -> RecoveryResult:
        """Attempt partial cache recovery, skipping corrupted entries"""
        result = RecoveryResult(
            success=False,
            recovered_entries=0,
            skipped_entries=0,
            corrupted_entries=0,
            total_entries=0,
            recovery_time_ms=0.0
        )
        
        recovered_data = {}
        
        # Try to recover from multiple checkpoints
        for checkpoint in sorted(self.checkpoints, key=lambda cp: cp.timestamp, reverse=True):
            checkpoint_file = self.cache_dir / "checkpoints" / f"{checkpoint.checkpoint_id}.cache"
            if checkpoint_file.exists():
                try:
                    cache_data = await self._load_cache_file(checkpoint_file, checkpoint.format)
                    if cache_data:
                        # Merge non-corrupted entries
                        for key, value in cache_data.items():
                            if key not in recovered_data:
                                try:
                                    # Basic validation
                                    if isinstance(value, dict) and 'data' in value:
                                        recovered_data[key] = value
                                        result.recovered_entries += 1
                                    else:
                                        result.corrupted_entries += 1
                                except Exception:
                                    result.corrupted_entries += 1
                        
                        result.total_entries = len(cache_data)
                except Exception as e:
                    result.errors.append(f"Error processing checkpoint {checkpoint.checkpoint_id}: {str(e)}")
        
        if recovered_data:
            self.cached_data = recovered_data
            result.success = True
        
        return result
    
    async def _rebuild_recovery(self) -> RecoveryResult:
        """Recovery by rebuilding cache from scratch"""
        result = RecoveryResult(
            success=True,
            recovered_entries=0,
            skipped_entries=0,
            corrupted_entries=0,
            total_entries=0,
            recovery_time_ms=0.0,
            warnings=["Cache rebuilt from scratch - all previous data lost"]
        )
        
        # Clear corrupted cache
        self.cached_data = {}
        self.cache_metadata = {}
        
        return result
    
    async def _skip_corrupted_recovery(self) -> RecoveryResult:
        """Recovery by skipping corrupted entries"""
        result = RecoveryResult(
            success=False,
            recovered_entries=0,
            skipped_entries=0,
            corrupted_entries=0,
            total_entries=0,
            recovery_time_ms=0.0
        )
        
        # Try to load and validate each cache entry individually
        recovered_data = {}
        
        # Check all available cache files
        for format in CacheFormat:
            cache_file = self.cache_dir / f"cache_data.{format}"
            if cache_file.exists():
                try:
                    cache_data = await self._load_cache_file(cache_file, format)
                    if cache_data:
                        for key, value in cache_data.items():
                            try:
                                # Validate entry
                                if self._validate_cache_entry(key, value):
                                    recovered_data[key] = value
                                    result.recovered_entries += 1
                                else:
                                    result.corrupted_entries += 1
                            except Exception:
                                result.corrupted_entries += 1
                        
                        result.total_entries = len(cache_data)
                        break  # Use first successful load
                        
                except Exception as e:
                    result.errors.append(f"Error loading cache file {cache_file}: {str(e)}")
        
        if recovered_data:
            self.cached_data = recovered_data
            result.success = True
        
        return result
    
    def _validate_cache_entry(self, key: str, value: Any) -> bool:
        """Validate a single cache entry"""
        try:
            # Basic structure validation
            if not isinstance(value, dict):
                return False
            
            # Check required fields
            if 'data' not in value:
                return False
            
            # Additional validation can be added here
            return True
            
        except Exception:
            return False
    
    def _update_save_metrics(self, save_time_ms: float, entry_count: int):
        """Update save operation metrics"""
        if self.metrics.average_save_time_ms == 0:
            self.metrics.average_save_time_ms = save_time_ms
        else:
            self.metrics.average_save_time_ms = (self.metrics.average_save_time_ms + save_time_ms) / 2
        
        self.metrics.total_bytes_saved += entry_count * 1024  # Rough estimate
    
    def _update_load_metrics(self, load_time_ms: float, entry_count: int):
        """Update load operation metrics"""
        if self.metrics.average_load_time_ms == 0:
            self.metrics.average_load_time_ms = load_time_ms
        else:
            self.metrics.average_load_time_ms = (self.metrics.average_load_time_ms + load_time_ms) / 2
        
        self.metrics.total_bytes_loaded += entry_count * 1024  # Rough estimate


# Global instance
cache_persistence_service = CachePersistenceService()