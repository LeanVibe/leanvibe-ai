"""
Background Notification Service for LeenVibe CLI

Provides real-time notification handling with smart filtering, throttling,
and non-intrusive background operation.
"""

import asyncio
import logging
import time
from collections import deque
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List

from rich.console import Console

from ..config import CLIConfig
from ..client import BackendClient

logger = logging.getLogger(__name__)
console = Console()


class NotificationService:
    """Background service for real-time notifications"""
    
    def __init__(self, config: CLIConfig):
        self.config = config
        self.client = BackendClient(config)
        self.notification_queue = asyncio.Queue()
        self.is_running = False
        self.notification_history = deque(maxlen=100)
        self._event_handlers: List[Callable[[Dict[str, Any]], None]] = []
        self._background_tasks: List[asyncio.Task] = []
        
        # Throttling state
        self._throttle_window: Dict[str, float] = {}
        self._notification_count = 0
        self._last_minute_reset = time.time()
        
    async def start_background_monitoring(self) -> bool:
        """Start background monitoring with minimal UI impact"""
        try:
            if not await self.client.connect_websocket():
                logger.error("Failed to establish WebSocket connection for notifications")
                return False
                
            self.is_running = True
            
            # Start background tasks
            listener_task = asyncio.create_task(self._event_listener())
            processor_task = asyncio.create_task(self._notification_processor())
            
            self._background_tasks = [listener_task, processor_task]
            
            if self.config.verbose:
                console.print("[dim]Background notification service started[/dim]")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start background monitoring: {e}")
            return False
    
    async def stop(self):
        """Stop background monitoring and cleanup"""
        self.is_running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
                
        # Wait for tasks to complete cancellation
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Close client connection
        await self.client.close()
        
        if self.config.verbose:
            console.print("[dim]Background notification service stopped[/dim]")
    
    def add_event_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Add event handler for custom notification processing"""
        self._event_handlers.append(handler)
    
    def remove_event_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Remove event handler"""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)
    
    async def _event_listener(self):
        """Listen for events and queue notifications"""
        try:
            async for event in self.client.listen_for_events():
                if not self.is_running:
                    break
                    
                # Apply smart filtering
                if self._should_notify(event):
                    await self.notification_queue.put(event)
                    self.notification_history.appendleft({
                        'event': event,
                        'timestamp': datetime.now(),
                        'processed': False
                    })
                
                # Call custom event handlers
                for handler in self._event_handlers:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Event handler error: {e}")
                        
        except asyncio.CancelledError:
            logger.debug("Event listener cancelled")
        except Exception as e:
            logger.error(f"Event listener error: {e}")
            if self.is_running:
                # Try to reconnect after a delay
                await asyncio.sleep(5)
                if self.is_running:
                    asyncio.create_task(self._event_listener())
    
    async def _notification_processor(self):
        """Process notifications with throttling and deduplication"""
        try:
            while self.is_running:
                try:
                    event = await asyncio.wait_for(
                        self.notification_queue.get(), timeout=1.0
                    )
                    
                    # Check rate limiting
                    if not self._check_rate_limit():
                        continue
                    
                    # Smart throttling by event type
                    if not self._check_throttling(event):
                        continue
                    
                    # Process notification
                    await self._process_notification(event)
                    
                    # Mark as processed in history
                    self._mark_processed(event)
                    
                except asyncio.TimeoutError:
                    continue
                    
        except asyncio.CancelledError:
            logger.debug("Notification processor cancelled")
        except Exception as e:
            logger.error(f"Notification processor error: {e}")
    
    def _should_notify(self, event: Dict[str, Any]) -> bool:
        """Determine if an event should generate a notification"""
        # Extract event priority
        priority = event.get('priority', 'medium')
        event_type = event.get('type', 'unknown')
        
        # Check minimum priority threshold
        priority_levels = {
            'debug': 0,
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        
        min_level = getattr(self.config, 'notification_level', 'medium')
        if priority_levels.get(priority, 2) < priority_levels.get(min_level, 2):
            return False
        
        # Check if notifications are enabled
        if not getattr(self.config, 'show_notifications', True):
            return False
        
        # Check event type filtering (if configured)
        enabled_types = getattr(self.config, 'enabled_event_types', None)
        if enabled_types and event_type not in enabled_types:
            return False
        
        # Check file pattern exclusions
        file_path = event.get('file_path') or event.get('data', {}).get('file_path')
        if file_path and self._is_excluded_file(file_path):
            return False
        
        return True
    
    def _is_excluded_file(self, file_path: str) -> bool:
        """Check if file path matches exclusion patterns"""
        exclude_patterns = getattr(self.config, 'exclude_patterns', [])
        import fnmatch
        
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_time = time.time()
        max_per_minute = getattr(self.config, 'max_notifications_per_minute', 10)
        
        # Reset counter every minute
        if current_time - self._last_minute_reset >= 60:
            self._notification_count = 0
            self._last_minute_reset = current_time
        
        # Check if we're at the limit
        if self._notification_count >= max_per_minute:
            return False
        
        self._notification_count += 1
        return True
    
    def _check_throttling(self, event: Dict[str, Any]) -> bool:
        """Check if event should be throttled"""
        event_type = event.get('type', 'unknown')
        source = event.get('source', '')
        
        # Create throttling key
        throttle_key = f"{event_type}:{source}"
        current_time = time.time()
        throttle_seconds = getattr(self.config, 'notification_throttle_seconds', 30)
        
        # Check if we're in throttle window
        if throttle_key in self._throttle_window:
            if current_time - self._throttle_window[throttle_key] < throttle_seconds:
                return False
        
        # Update throttle window
        self._throttle_window[throttle_key] = current_time
        return True
    
    async def _process_notification(self, event: Dict[str, Any]):
        """Process individual notification"""
        try:
            priority = event.get('priority', 'medium')
            event_type = event.get('type', 'unknown')
            
            # Determine notification methods based on priority and preferences
            if priority == 'critical' and getattr(self.config, 'desktop_notifications', True):
                await self._send_desktop_notification(event)
            
            if getattr(self.config, 'terminal_notifications', True):
                await self._send_terminal_notification(event)
            
            # Log notification
            self._log_notification(event)
            
        except Exception as e:
            logger.error(f"Failed to process notification: {e}")
    
    async def _send_desktop_notification(self, event: Dict[str, Any]):
        """Send desktop notification"""
        try:
            from .desktop_notifications import DesktopNotificationService, NotificationTriggers
            
            # Check if desktop notifications should be sent for this event
            if not NotificationTriggers.should_send_desktop_notification(event, self.config):
                return
            
            # Format notification
            notification_data = NotificationTriggers.format_desktop_notification(event)
            
            # Send notification
            desktop_service = DesktopNotificationService()
            success = await desktop_service.send_notification(
                title=notification_data['title'],
                message=notification_data['message'],
                priority=notification_data['priority'],
                sound=notification_data['sound'],
                timeout=notification_data['timeout']
            )
            
            if self.config.verbose:
                status = "sent" if success else "failed"
                console.print(f"[dim]Desktop notification {status}: {event.get('type', 'event')}[/dim]")
                
        except Exception as e:
            logger.error(f"Failed to send desktop notification: {e}")
            if self.config.verbose:
                console.print(f"[dim]Desktop notification failed: {e}[/dim]")
    
    async def _send_terminal_notification(self, event: Dict[str, Any]):
        """Send terminal notification (placeholder for now)"""
        # This will be enhanced in Task 2.3.3
        if self.config.verbose:
            priority = event.get('priority', 'medium')
            event_type = event.get('type', 'unknown')
            message = self._extract_message(event)
            
            priority_colors = {
                'critical': 'red',
                'high': 'yellow',
                'medium': 'blue',
                'low': 'green'
            }
            color = priority_colors.get(priority, 'white')
            
            console.print(f"[{color}]🔔 {event_type}: {message}[/{color}]")
    
    def _extract_message(self, event: Dict[str, Any]) -> str:
        """Extract meaningful message from event"""
        # Try different message fields
        for field in ['message', 'description', 'content', 'summary']:
            if field in event and event[field]:
                return str(event[field])[:100]  # Limit length
        
        # Try data field
        data = event.get('data', {})
        if isinstance(data, dict):
            for field in ['message', 'description', 'error', 'warning']:
                if field in data and data[field]:
                    return str(data[field])[:100]
        
        # Fallback to event type
        event_type = event.get('type', 'unknown')
        return f"{event_type.replace('_', ' ').title()} detected"
    
    def _log_notification(self, event: Dict[str, Any]):
        """Log notification for debugging"""
        logger.debug(f"Notification processed: {event.get('type')} - {event.get('priority')}")
    
    def _mark_processed(self, event: Dict[str, Any]):
        """Mark event as processed in history"""
        for item in self.notification_history:
            if item['event'] == event:
                item['processed'] = True
                break
    
    def get_notification_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent notification history"""
        return list(self.notification_history)[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification service statistics"""
        return {
            'is_running': self.is_running,
            'notifications_sent': self._notification_count,
            'history_size': len(self.notification_history),
            'active_handlers': len(self._event_handlers),
            'throttle_entries': len(self._throttle_window)
        }