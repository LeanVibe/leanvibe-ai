"""
Notification Overlay System for LeenVibe CLI

Provides non-intrusive terminal notification overlays that don't interrupt
current CLI command execution.
"""

import asyncio
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align

console = Console()


class NotificationOverlay:
    """Non-intrusive terminal notification overlay"""
    
    def __init__(self, console_instance: Optional[Console] = None):
        self.console = console_instance or console
        self.active_notifications = deque(maxlen=3)  # Show max 3 notifications
        self.notification_lock = asyncio.Lock()
        self.is_displaying = False
    
    async def show_notification(self, event: Dict[str, Any], duration: int = 5):
        """Show notification overlay without interrupting current command"""
        async with self.notification_lock:
            notification = self._format_notification(event)
            self.active_notifications.append(notification)
            
            # Display notification bar
            await self._render_notification_bar()
            
            # Auto-dismiss after duration
            asyncio.create_task(self._auto_dismiss(notification, duration))
    
    async def _auto_dismiss(self, notification: Dict[str, str], duration: int):
        """Auto-dismiss notification after specified duration"""
        await asyncio.sleep(duration)
        
        async with self.notification_lock:
            if notification in self.active_notifications:
                self.active_notifications.remove(notification)
                await self._render_notification_bar()
    
    def _format_notification(self, event: Dict[str, Any]) -> Dict[str, str]:
        """Format event as notification"""
        priority = event.get('priority', 'medium')
        event_type = event.get('type', 'unknown')
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Extract meaningful message
        message = self._extract_message(event)
        
        # Color coding by priority
        colors = {
            'critical': 'red',
            'high': 'yellow', 
            'medium': 'blue',
            'low': 'green',
            'debug': 'dim'
        }
        
        # Priority icons
        icons = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': 'ℹ️',
            'low': '✓',
            'debug': '🔍'
        }
        
        return {
            'priority': priority,
            'color': colors.get(priority, 'white'),
            'message': message,
            'timestamp': timestamp,
            'icon': icons.get(priority, '🔔'),
            'event_type': event_type
        }
    
    def _extract_message(self, event: Dict[str, Any]) -> str:
        """Extract meaningful message from event"""
        # Try different message fields
        for field in ['message', 'description', 'content', 'summary']:
            if field in event and event[field]:
                return str(event[field])[:80]  # Limit length for overlay
        
        # Try data field
        data = event.get('data', {})
        if isinstance(data, dict):
            for field in ['message', 'description', 'error', 'warning']:
                if field in data and data[field]:
                    return str(data[field])[:80]
        
        # Fallback to event type
        event_type = event.get('type', 'unknown')
        return f"{event_type.replace('_', ' ').title()}"
    
    async def _render_notification_bar(self):
        """Render notification bar at top of terminal"""
        if not self.active_notifications:
            # Clear any existing notification display
            if self.is_displaying:
                self.console.print()  # Add line break to separate from notifications
                self.is_displaying = False
            return
        
        # Create notification content
        notifications_text = Text()
        
        for i, notification in enumerate(list(self.active_notifications)[-3:]):  # Last 3
            if i > 0:
                notifications_text.append(" | ", style="dim")
            
            # Add icon and message
            notifications_text.append(f"{notification['icon']} ", style=notification['color'])
            notifications_text.append(f"{notification['message']}", style=notification['color'])
            notifications_text.append(f" ({notification['timestamp']})", style="dim")
        
        # Create panel with notification bar styling
        panel = Panel(
            Align.center(notifications_text),
            style="dim",
            border_style="dim",
            height=1,
            padding=(0, 1)
        )
        
        # Non-blocking display
        self.console.print(panel)
        self.is_displaying = True
    
    def clear_notifications(self):
        """Clear all active notifications"""
        self.active_notifications.clear()
        if self.is_displaying:
            self.console.print()
            self.is_displaying = False
    
    def get_active_notifications(self) -> List[Dict[str, str]]:
        """Get list of currently active notifications"""
        return list(self.active_notifications)


class NotificationHistory:
    """Manages notification history and replay functionality"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history = deque(maxlen=max_history)
    
    def add_notification(self, event: Dict[str, Any], processed_at: datetime):
        """Add notification to history"""
        history_entry = {
            'event': event,
            'processed_at': processed_at,
            'priority': event.get('priority', 'medium'),
            'event_type': event.get('type', 'unknown'),
            'message': self._extract_message(event)
        }
        self.history.appendleft(history_entry)
    
    def get_history(self, limit: int = 20, priority_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get notification history with optional filtering"""
        history_list = list(self.history)
        
        # Apply priority filter if specified
        if priority_filter:
            history_list = [
                entry for entry in history_list 
                if entry['priority'] == priority_filter
            ]
        
        return history_list[:limit]
    
    def get_recent_critical(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent critical notifications"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            entry for entry in self.history
            if (entry['priority'] == 'critical' and 
                entry['processed_at'] > cutoff_time)
        ]
    
    def display_history(self, console_instance: Console, limit: int = 10):
        """Display notification history in formatted table"""
        history_list = self.get_history(limit)
        
        if not history_list:
            console_instance.print("[dim]No notification history available[/dim]")
            return
        
        table = Table(title="Notification History", show_header=True, header_style="bold cyan")
        table.add_column("Time", style="dim", width=10)
        table.add_column("Priority", style="bold", width=10)
        table.add_column("Type", style="cyan", width=20)
        table.add_column("Message", style="white")
        
        for entry in history_list:
            # Format timestamp
            time_str = entry['processed_at'].strftime("%H:%M:%S")
            
            # Color code priority
            priority = entry['priority']
            priority_colors = {
                'critical': 'red',
                'high': 'yellow',
                'medium': 'blue',
                'low': 'green',
                'debug': 'dim'
            }
            priority_color = priority_colors.get(priority, 'white')
            
            table.add_row(
                time_str,
                f"[{priority_color}]{priority.upper()}[/{priority_color}]",
                entry['event_type'].replace('_', ' ').title(),
                entry['message'][:60] + "..." if len(entry['message']) > 60 else entry['message']
            )
        
        console_instance.print(table)
    
    def _extract_message(self, event: Dict[str, Any]) -> str:
        """Extract meaningful message from event (same as overlay)"""
        for field in ['message', 'description', 'content', 'summary']:
            if field in event and event[field]:
                return str(event[field])
        
        data = event.get('data', {})
        if isinstance(data, dict):
            for field in ['message', 'description', 'error', 'warning']:
                if field in data and data[field]:
                    return str(data[field])
        
        event_type = event.get('type', 'unknown')
        return f"{event_type.replace('_', ' ').title()}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get history statistics"""
        if not self.history:
            return {
                'total_notifications': 0,
                'by_priority': {},
                'by_type': {},
                'oldest_entry': None,
                'newest_entry': None
            }
        
        # Count by priority
        priority_counts = {}
        type_counts = {}
        
        for entry in self.history:
            priority = entry['priority']
            event_type = entry['event_type']
            
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
        
        return {
            'total_notifications': len(self.history),
            'by_priority': priority_counts,
            'by_type': type_counts,
            'oldest_entry': self.history[-1]['processed_at'].isoformat() if self.history else None,
            'newest_entry': self.history[0]['processed_at'].isoformat() if self.history else None
        }