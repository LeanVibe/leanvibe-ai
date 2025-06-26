"""
Real-time File Monitoring Service

Provides real-time file system monitoring with change detection, debouncing,
and intelligent analysis of code changes with impact assessment.
"""

import logging
import asyncio
import hashlib
import time
import os
from typing import Dict, List, Optional, Set, Callable, Any
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import aiofiles

from ..models.monitoring_models import (
    FileChange, ChangeType, MonitoringSession, MonitoringConfiguration,
    MonitoringStatus, ChangeNotification, MonitoringMetrics, MonitoringAlert,
    ImpactAssessment, RiskLevel, ChangeScope, MonitoringError
)
from ..models.ast_models import LanguageType
from ..services.ast_service import ast_service
from ..services.project_indexer import project_indexer
from ..services.graph_query_service import graph_query_service
from ..services.incremental_indexer import incremental_indexer
from ..services.cache_invalidation_service import cache_invalidation_service

logger = logging.getLogger(__name__)


class FileMonitorEventHandler(FileSystemEventHandler):
    """Event handler for file system changes"""
    
    def __init__(self, monitor_service: 'FileMonitorService', session_id: str):
        self.monitor_service = monitor_service
        self.session_id = session_id
        self.last_events: Dict[str, float] = {}
        
    def on_any_event(self, event: FileSystemEvent):
        """Handle any file system event"""
        try:
            # Skip directory events
            if event.is_directory:
                return
            
            # Get the session
            session = self.monitor_service.sessions.get(self.session_id)
            if not session or not session.is_active():
                return
            
            # Check if file matches watch patterns and doesn't match ignore patterns
            if not self._should_monitor_file(event.src_path, session.configuration):
                return
            
            # Debounce rapid events for the same file
            current_time = time.time()
            last_time = self.last_events.get(event.src_path, 0)
            debounce_delay = session.configuration.debounce_delay_ms / 1000.0
            
            if current_time - last_time < debounce_delay:
                return
            
            self.last_events[event.src_path] = current_time
            
            # Convert to our change type
            change_type = self._convert_event_type(event.event_type)
            
            # Create file change
            change = FileChange(
                id=f"change_{int(current_time * 1000)}_{hash(event.src_path)}",
                file_path=event.src_path,
                change_type=change_type,
                timestamp=datetime.now()
            )
            
            # Handle moved events
            if hasattr(event, 'dest_path'):
                change.old_path = event.src_path
                change.file_path = event.dest_path
            
            # Queue for processing
            asyncio.create_task(self.monitor_service._process_change(session.session_id, change))
            
        except Exception as e:
            logger.error(f"Error handling file system event: {e}")
    
    def _should_monitor_file(self, file_path: str, config: MonitoringConfiguration) -> bool:
        """Check if file should be monitored based on patterns"""
        path = Path(file_path)
        
        # Check ignore patterns first
        for pattern in config.ignore_patterns:
            if path.match(pattern):
                return False
        
        # Check watch patterns
        for pattern in config.watch_patterns:
            if path.match(pattern):
                return True
        
        return False
    
    def _convert_event_type(self, event_type: str) -> ChangeType:
        """Convert watchdog event type to our ChangeType"""
        mapping = {
            'created': ChangeType.CREATED,
            'modified': ChangeType.MODIFIED,
            'deleted': ChangeType.DELETED,
            'moved': ChangeType.MOVED
        }
        return mapping.get(event_type, ChangeType.MODIFIED)


class FileMonitorService:
    """
    Real-time file monitoring service
    
    Monitors file changes, performs impact analysis, and provides
    real-time notifications about code changes.
    """
    
    def __init__(self):
        self.sessions: Dict[str, MonitoringSession] = {}
        self.observers: Dict[str, Observer] = {}
        self.change_processors: Dict[str, asyncio.Task] = {}
        self.notification_callbacks: Dict[str, List[Callable]] = {}
        
        # Processing queues
        self.change_queues: Dict[str, asyncio.Queue] = {}
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        
        # Thread pool for blocking operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Performance tracking
        self.metrics: Dict[str, MonitoringMetrics] = {}
        self.last_metrics_update: Dict[str, datetime] = {}
        
    async def start_monitoring(
        self, 
        session_id: str, 
        project_id: str, 
        client_id: str, 
        config: MonitoringConfiguration
    ) -> bool:
        """Start monitoring a project"""
        try:
            logger.info(f"Starting monitoring for session {session_id}")
            
            # Validate workspace path
            if not os.path.exists(config.workspace_path):
                raise MonitoringError(f"Workspace path does not exist: {config.workspace_path}")
            
            # Create monitoring session
            session = MonitoringSession(
                session_id=session_id,
                project_id=project_id,
                client_id=client_id,
                configuration=config,
                status=MonitoringStatus.STARTING,
                started_at=datetime.now()
            )
            
            self.sessions[session_id] = session
            
            # Create change queue
            self.change_queues[session_id] = asyncio.Queue(maxsize=1000)
            
            # Start change processor
            self.processing_tasks[session_id] = asyncio.create_task(
                self._process_changes_worker(session_id)
            )
            
            # Create and start file system observer
            event_handler = FileMonitorEventHandler(self, session_id)
            observer = Observer()
            observer.schedule(event_handler, config.workspace_path, recursive=True)
            observer.start()
            
            self.observers[session_id] = observer
            
            # Update session status
            session.status = MonitoringStatus.ACTIVE
            session.last_activity = datetime.now()
            
            # Initialize metrics
            self.metrics[session_id] = MonitoringMetrics(session_id=session_id)
            self.last_metrics_update[session_id] = datetime.now()
            
            logger.info(f"Monitoring started for session {session_id} on {config.workspace_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start monitoring for session {session_id}: {e}")
            await self._cleanup_session(session_id)
            raise MonitoringError(f"Failed to start monitoring: {str(e)}", session_id=session_id)
    
    async def stop_monitoring(self, session_id: str) -> bool:
        """Stop monitoring for a session"""
        try:
            logger.info(f"Stopping monitoring for session {session_id}")
            
            # Update session status
            if session_id in self.sessions:
                self.sessions[session_id].status = MonitoringStatus.STOPPED
            
            # Cleanup resources
            await self._cleanup_session(session_id)
            
            logger.info(f"Monitoring stopped for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping monitoring for session {session_id}: {e}")
            return False
    
    async def pause_monitoring(self, session_id: str) -> bool:
        """Pause monitoring for a session"""
        try:
            if session_id in self.sessions:
                self.sessions[session_id].status = MonitoringStatus.PAUSED
                logger.info(f"Monitoring paused for session {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error pausing monitoring: {e}")
            return False
    
    async def resume_monitoring(self, session_id: str) -> bool:
        """Resume monitoring for a session"""
        try:
            if session_id in self.sessions:
                self.sessions[session_id].status = MonitoringStatus.ACTIVE
                self.sessions[session_id].last_activity = datetime.now()
                logger.info(f"Monitoring resumed for session {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error resuming monitoring: {e}")
            return False
    
    async def _cleanup_session(self, session_id: str):
        """Clean up resources for a session"""
        try:
            # Stop file system observer
            if session_id in self.observers:
                observer = self.observers[session_id]
                observer.stop()
                observer.join(timeout=5.0)  # Wait max 5 seconds
                del self.observers[session_id]
            
            # Cancel processing task
            if session_id in self.processing_tasks:
                task = self.processing_tasks[session_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.processing_tasks[session_id]
            
            # Clear change queue
            if session_id in self.change_queues:
                del self.change_queues[session_id]
            
            # Clear metrics
            if session_id in self.metrics:
                del self.metrics[session_id]
            
            if session_id in self.last_metrics_update:
                del self.last_metrics_update[session_id]
            
            # Clear notification callbacks
            if session_id in self.notification_callbacks:
                del self.notification_callbacks[session_id]
            
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
    
    async def _process_change(self, session_id: str, change: FileChange):
        """Queue a change for processing"""
        try:
            if session_id not in self.change_queues:
                return
            
            queue = self.change_queues[session_id]
            
            # Add to queue (non-blocking)
            try:
                queue.put_nowait(change)
            except asyncio.QueueFull:
                logger.warning(f"Change queue full for session {session_id}, dropping change")
                
        except Exception as e:
            logger.error(f"Error queuing change: {e}")
    
    async def _process_changes_worker(self, session_id: str):
        """Worker process for handling change queue"""
        try:
            queue = self.change_queues[session_id]
            
            while True:
                try:
                    # Wait for change with timeout
                    change = await asyncio.wait_for(queue.get(), timeout=1.0)
                    
                    # Process the change
                    await self._analyze_change(session_id, change)
                    
                    # Mark task done
                    queue.task_done()
                    
                except asyncio.TimeoutError:
                    # Check if session is still active
                    session = self.sessions.get(session_id)
                    if not session or session.status == MonitoringStatus.STOPPED:
                        break
                    continue
                    
                except Exception as e:
                    logger.error(f"Error processing change: {e}")
                    
        except asyncio.CancelledError:
            logger.debug(f"Change processor cancelled for session {session_id}")
        except Exception as e:
            logger.error(f"Change processor error for session {session_id}: {e}")
    
    async def _analyze_change(self, session_id: str, change: FileChange):
        """Analyze a file change and generate notifications"""
        try:
            session = self.sessions.get(session_id)
            if not session or not session.is_active():
                return
            
            start_time = time.time()
            
            # Add change to session
            session.add_change(change)
            
            # Skip analysis for binary files or if disabled
            if not session.configuration.enable_content_analysis or change.is_binary:
                return
            
            # Skip large files
            if change.file_size and change.file_size > session.configuration.max_file_size_mb * 1024 * 1024:
                logger.debug(f"Skipping large file: {change.file_path}")
                return
            
            # Perform content analysis
            await self._analyze_file_content(change)
            
            # Perform impact analysis if enabled
            impact_assessment = None
            if session.configuration.enable_impact_analysis:
                impact_assessment = await self._analyze_impact(session_id, change)
            
            # Create notification
            notification = ChangeNotification.from_change(change, session_id, impact_assessment)
            
            # Send notification
            await self._send_notification(session_id, notification)
            
            # Update metrics
            analysis_time = (time.time() - start_time) * 1000
            await self._update_metrics(session_id, analysis_time)
            
            # Check for alerts
            await self._check_for_alerts(session_id, change, impact_assessment)
            
            # Trigger incremental index update for code files
            if change.is_code_file() and session.configuration.enable_content_analysis:
                await self._trigger_incremental_index_update(session_id, change)
                
                # Trigger cache invalidation for the changed file
                await cache_invalidation_service.invalidate_file_cache(
                    change.file_path, change.change_type, propagate=True
                )
            
        except Exception as e:
            logger.error(f"Error analyzing change: {e}")
            session.total_errors += 1
    
    async def _analyze_file_content(self, change: FileChange):
        """Analyze file content changes"""
        try:
            if change.change_type == ChangeType.DELETED:
                return
            
            # Get file info
            file_path = Path(change.file_path)
            if file_path.exists():
                stat = file_path.stat()
                change.file_size = stat.st_size
                
                # Check if binary
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        # Try to read first 1024 bytes to check if text
                        content_sample = await f.read(1024)
                        change.is_binary = False
                        change.encoding = 'utf-8'
                except UnicodeDecodeError:
                    change.is_binary = True
                    return
                
                # Detect language
                change.language = self._detect_language(str(file_path))
                
                # For modified files, try to get line changes
                if change.change_type == ChangeType.MODIFIED:
                    await self._calculate_line_changes(change)
            
        except Exception as e:
            logger.error(f"Error analyzing file content: {e}")
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.swift': 'swift',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c'
        }
        
        ext = Path(file_path).suffix.lower()
        return extension_map.get(ext)
    
    async def _calculate_line_changes(self, change: FileChange):
        """Calculate line changes for modified files (simplified version)"""
        try:
            # This is a simplified implementation
            # In a full implementation, you'd use git diff or similar
            file_path = Path(change.file_path)
            if file_path.exists():
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    lines = content.split('\n')
                    change.lines_modified = len(lines)
                    # For now, assume all lines are modified
                    # Real implementation would compare with previous version
                    
        except Exception as e:
            logger.debug(f"Could not calculate line changes: {e}")
    
    async def _analyze_impact(self, session_id: str, change: FileChange) -> Optional[ImpactAssessment]:
        """Analyze the impact of a file change"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return None
            
            # Create basic impact assessment
            assessment = ImpactAssessment(
                change_id=change.id,
                risk_level=RiskLevel.LOW,
                scope=ChangeScope.FILE_ONLY
            )
            
            # Check if this is a code file
            if not change.is_code_file():
                return assessment
            
            # Determine risk level based on file characteristics
            file_path = change.file_path
            
            # Higher risk for core files
            if any(keyword in file_path.lower() for keyword in ['main', 'index', 'app', 'core', 'base']):
                assessment.risk_level = RiskLevel.MEDIUM
                assessment.scope = ChangeScope.MODULE_LOCAL
            
            # Higher risk for configuration or build files
            if any(keyword in file_path.lower() for keyword in ['config', 'setup', 'build', 'deploy']):
                assessment.risk_level = RiskLevel.HIGH
                assessment.scope = ChangeScope.PROJECT_WIDE
            
            # Add basic recommendations
            if assessment.risk_level == RiskLevel.HIGH:
                assessment.suggested_actions.extend([
                    "Run comprehensive tests",
                    "Review changes carefully",
                    "Consider impact on dependent systems"
                ])
            elif assessment.risk_level == RiskLevel.MEDIUM:
                assessment.suggested_actions.extend([
                    "Run relevant unit tests",
                    "Check for breaking changes"
                ])
            else:
                assessment.suggested_actions.append("Standard testing recommended")
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error analyzing impact: {e}")
            return None
    
    async def _send_notification(self, session_id: str, notification: ChangeNotification):
        """Send notification to registered callbacks"""
        try:
            callbacks = self.notification_callbacks.get(session_id, [])
            
            for callback in callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(notification)
                    else:
                        callback(notification)
                except Exception as e:
                    logger.error(f"Error in notification callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def _update_metrics(self, session_id: str, analysis_time_ms: float):
        """Update performance metrics"""
        try:
            if session_id not in self.metrics:
                return
            
            metrics = self.metrics[session_id]
            
            # Update analysis time (moving average)
            if metrics.average_analysis_time_ms == 0:
                metrics.average_analysis_time_ms = analysis_time_ms
            else:
                metrics.average_analysis_time_ms = (metrics.average_analysis_time_ms * 0.9) + (analysis_time_ms * 0.1)
            
            # Update measurement time
            metrics.measurement_time = datetime.now()
            
            # Calculate changes per minute
            session = self.sessions.get(session_id)
            if session and session.started_at:
                elapsed_minutes = (datetime.now() - session.started_at).total_seconds() / 60
                if elapsed_minutes > 0:
                    metrics.changes_per_minute = session.total_changes_detected / elapsed_minutes
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    async def _check_for_alerts(self, session_id: str, change: FileChange, impact: Optional[ImpactAssessment]):
        """Check if change should trigger alerts"""
        try:
            # Generate alert for high-risk changes
            if impact and impact.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                alert = MonitoringAlert(
                    id=f"alert_{change.id}",
                    session_id=session_id,
                    alert_type="high_risk_change",
                    severity="high",
                    title=f"High-risk change detected",
                    description=f"File {Path(change.file_path).name} has been modified with {impact.risk_level} risk",
                    affected_files=[change.file_path],
                    risk_factors=[f"Risk level: {impact.risk_level}", f"Scope: {impact.scope}"],
                    recommended_actions=impact.suggested_actions
                )
                
                # Send alert notification (would integrate with alerting system)
                logger.warning(f"High-risk change alert for session {session_id}: {alert.title}")
                
        except Exception as e:
            logger.error(f"Error checking for alerts: {e}")
    
    async def _trigger_incremental_index_update(self, session_id: str, change: FileChange):
        """Trigger incremental index update for changed file"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return
            
            workspace_path = session.configuration.workspace_path
            
            # Batch changes for better performance
            recent_changes = [c for c in session.recent_changes[:10] 
                             if c.is_code_file() and 
                             (datetime.now() - c.timestamp).total_seconds() < 60]  # Last minute
            
            if len(recent_changes) >= 5:  # Batch threshold
                logger.debug(f"Batching {len(recent_changes)} changes for incremental index update")
                updated_index = await incremental_indexer.update_from_file_changes(
                    workspace_path, recent_changes
                )
                
                if updated_index:
                    # Store updated index in session for agent access
                    session.configuration.workspace_path = workspace_path
                    logger.info(f"Updated project index: {updated_index.supported_files} files, "
                               f"{len(updated_index.symbols)} symbols")
            else:
                # Single file update
                logger.debug(f"Queuing single file change for incremental index: {change.file_path}")
                updated_index = await incremental_indexer.update_from_file_changes(
                    workspace_path, [change]
                )
                
                if updated_index:
                    logger.debug(f"Updated project index for single file change")
        
        except Exception as e:
            logger.error(f"Error triggering incremental index update: {e}")
    
    def register_notification_callback(self, session_id: str, callback: Callable):
        """Register a callback for change notifications"""
        if session_id not in self.notification_callbacks:
            self.notification_callbacks[session_id] = []
        self.notification_callbacks[session_id].append(callback)
    
    def get_session(self, session_id: str) -> Optional[MonitoringSession]:
        """Get monitoring session by ID"""
        return self.sessions.get(session_id)
    
    def get_sessions(self) -> List[MonitoringSession]:
        """Get all monitoring sessions"""
        return list(self.sessions.values())
    
    def get_metrics(self, session_id: str) -> Optional[MonitoringMetrics]:
        """Get metrics for a session"""
        return self.metrics.get(session_id)
    
    async def get_recent_changes(self, session_id: str, limit: int = 50) -> List[FileChange]:
        """Get recent changes for a session"""
        session = self.sessions.get(session_id)
        if session:
            return session.recent_changes[:limit]
        return []
    
    async def shutdown(self):
        """Shutdown the monitoring service"""
        try:
            logger.info("Shutting down file monitoring service")
            
            # Stop all sessions
            session_ids = list(self.sessions.keys())
            for session_id in session_ids:
                await self.stop_monitoring(session_id)
            
            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True)
            
            logger.info("File monitoring service shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during monitoring service shutdown: {e}")


# Global instance
file_monitor_service = FileMonitorService()