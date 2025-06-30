"""
Cross-platform Desktop Notification Service for LeanVibe CLI

Provides native desktop notifications on macOS, Linux, and Windows with
smart triggering and configuration options.
"""

import asyncio
import logging
import platform
import subprocess
import shutil
from typing import Dict, Any, Optional

from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


class DesktopNotificationService:
    """Cross-platform desktop notification service"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.notification_available = self._check_availability()
        
        if not self.notification_available:
            logger.warning(f"Desktop notifications not available on {self.platform}")
    
    def _check_availability(self) -> bool:
        """Check if desktop notifications are available"""
        if self.platform == "darwin":  # macOS
            return shutil.which("osascript") is not None
        elif self.platform == "linux":
            return shutil.which("notify-send") is not None
        elif self.platform == "windows":
            try:
                # Try importing Windows toast notification
                import win10toast
                return True
            except ImportError:
                try:
                    # Fallback to plyer
                    from plyer import notification
                    return True
                except ImportError:
                    return False
        else:
            # Try plyer for other platforms
            try:
                from plyer import notification
                return True
            except ImportError:
                return False
    
    async def send_notification(self, title: str, message: str, 
                              priority: str = "normal", sound: bool = False,
                              timeout: int = 5) -> bool:
        """Send desktop notification"""
        if not self.notification_available:
            logger.debug("Desktop notifications not available")
            return False
        
        try:
            if self.platform == "darwin":
                return await self._send_macos_notification(title, message, sound, timeout)
            elif self.platform == "linux":
                return await self._send_linux_notification(title, message, priority, timeout)
            elif self.platform == "windows":
                return await self._send_windows_notification(title, message, timeout)
            else:
                return await self._send_plyer_notification(title, message, timeout)
        
        except Exception as e:
            logger.error(f"Failed to send desktop notification: {e}")
            return False
    
    async def _send_macos_notification(self, title: str, message: str, 
                                     sound: bool, timeout: int) -> bool:
        """Send macOS notification using osascript"""
        try:
            # Escape special characters for AppleScript
            safe_title = title.replace('"', '\\"').replace('!', '').replace('$', '')
            safe_message = message.replace('"', '\\"').replace('!', '').replace('$', '')
            
            script_parts = [
                f'display notification "{safe_message}"',
                f'with title "LeanVibe"',
                f'subtitle "{safe_title}"'
            ]
            
            if sound:
                script_parts.append('sound name "Glass"')
            
            script = " ".join(script_parts)
            
            proc = await asyncio.create_subprocess_exec(
                "osascript", "-e", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                logger.debug("macOS notification sent successfully")
                return True
            else:
                logger.error(f"macOS notification failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"macOS notification error: {e}")
            return False
    
    async def _send_linux_notification(self, title: str, message: str, 
                                     priority: str, timeout: int) -> bool:
        """Send Linux notification using notify-send"""
        try:
            urgency_map = {
                'critical': 'critical',
                'high': 'normal',
                'medium': 'normal', 
                'low': 'low',
                'debug': 'low'
            }
            
            urgency = urgency_map.get(priority, 'normal')
            timeout_ms = timeout * 1000
            
            proc = await asyncio.create_subprocess_exec(
                "notify-send",
                "--app-name=LeanVibe",
                f"--urgency={urgency}",
                f"--expire-time={timeout_ms}",
                "--icon=terminal",
                title,
                message,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                logger.debug("Linux notification sent successfully")
                return True
            else:
                logger.error(f"Linux notification failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Linux notification error: {e}")
            return False
    
    async def _send_windows_notification(self, title: str, message: str, timeout: int) -> bool:
        """Send Windows notification"""
        try:
            # Try win10toast first (more reliable for Windows 10/11)
            try:
                import win10toast
                toaster = win10toast.ToastNotifier()
                
                # Run in thread to avoid blocking
                def show_toast():
                    toaster.show_toast(
                        title=f"LeanVibe - {title}",
                        msg=message,
                        duration=timeout,
                        threaded=True
                    )
                
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, show_toast)
                
                logger.debug("Windows notification sent successfully")
                return True
                
            except ImportError:
                # Fallback to plyer
                return await self._send_plyer_notification(title, message, timeout)
                
        except Exception as e:
            logger.error(f"Windows notification error: {e}")
            return False
    
    async def _send_plyer_notification(self, title: str, message: str, timeout: int) -> bool:
        """Send notification using plyer (fallback)"""
        try:
            from plyer import notification
            
            def show_notification():
                notification.notify(
                    title=f"LeanVibe - {title}",
                    message=message,
                    timeout=timeout,
                    app_name="LeanVibe"
                )
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, show_notification)
            
            logger.debug("Plyer notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Plyer notification error: {e}")
            return False


class NotificationTriggers:
    """Intelligent notification trigger system"""
    
    CRITICAL_TRIGGERS = {
        'architectural_violation': {
            'title': 'Architecture Violation Detected',
            'icon': '🚨',
            'sound': True,
            'priority': 'critical'
        },
        'build_failure': {
            'title': 'Build Failed',
            'icon': '❌',
            'sound': True,
            'priority': 'critical'
        },
        'security_issue': {
            'title': 'Security Issue Found', 
            'icon': '🔒',
            'sound': True,
            'priority': 'critical'
        },
        'test_failure': {
            'title': 'Tests Failed',
            'icon': '🔴',
            'sound': False,
            'priority': 'critical'
        }
    }
    
    HIGH_PRIORITY_TRIGGERS = {
        'complexity_spike': {
            'title': 'Code Complexity Alert',
            'icon': '📊',
            'sound': False,
            'priority': 'high'
        },
        'circular_dependency': {
            'title': 'Circular Dependency Detected',
            'icon': '🔄',
            'sound': False,
            'priority': 'high'
        },
        'performance_regression': {
            'title': 'Performance Regression',
            'icon': '⚡',
            'sound': False,
            'priority': 'high'
        }
    }
    
    MEDIUM_PRIORITY_TRIGGERS = {
        'code_quality_warning': {
            'title': 'Code Quality Warning',
            'icon': '⚠️',
            'sound': False,
            'priority': 'medium'
        },
        'dependency_update': {
            'title': 'Dependency Update Available',
            'icon': '📦',
            'sound': False,
            'priority': 'medium'
        }
    }
    
    @classmethod
    def should_send_desktop_notification(cls, event: Dict[str, Any], config) -> bool:
        """Determine if event warrants desktop notification"""
        if not getattr(config, 'desktop_notifications', True):
            return False
        
        event_type = event.get('type', '')
        priority = event.get('priority', 'medium')
        
        # Always send for critical events
        if priority == 'critical':
            return True
        
        # Send for specific high-priority event types if configured
        if priority == 'high' and event_type in cls.HIGH_PRIORITY_TRIGGERS:
            return True
        
        # Send for medium priority if specifically configured
        if priority == 'medium' and event_type in cls.MEDIUM_PRIORITY_TRIGGERS:
            enabled_types = getattr(config, 'enabled_event_types', [])
            return event_type in enabled_types
        
        return False
    
    @classmethod
    def format_desktop_notification(cls, event: Dict[str, Any]) -> Dict[str, Any]:
        """Format event for desktop notification"""
        event_type = event.get('type', 'unknown')
        priority = event.get('priority', 'medium')
        
        # Get trigger configuration
        trigger_config = None
        
        if priority == 'critical':
            trigger_config = cls.CRITICAL_TRIGGERS.get(event_type)
        elif priority == 'high':
            trigger_config = cls.HIGH_PRIORITY_TRIGGERS.get(event_type)
        elif priority == 'medium':
            trigger_config = cls.MEDIUM_PRIORITY_TRIGGERS.get(event_type)
        
        if trigger_config:
            title = trigger_config['title']
            icon = trigger_config['icon']
            sound = trigger_config['sound']
            notification_priority = trigger_config['priority']
        else:
            title = f"LeanVibe {priority.title()} Alert"
            icon = "🔔"
            sound = priority == 'critical'
            notification_priority = priority
        
        # Extract message from event
        message = cls._extract_notification_message(event)
        
        return {
            'title': f"{icon} {title}",
            'message': message,
            'priority': notification_priority,
            'sound': sound,
            'timeout': 10 if priority == 'critical' else 5
        }
    
    @classmethod
    def _extract_notification_message(cls, event: Dict[str, Any]) -> str:
        """Extract meaningful message from event"""
        # Try different message fields
        for field in ['message', 'description', 'content', 'summary']:
            if field in event and event[field]:
                message = str(event[field])
                # Limit length for desktop notifications
                return message[:100] + "..." if len(message) > 100 else message
        
        # Try data field
        data = event.get('data', {})
        if isinstance(data, dict):
            for field in ['message', 'description', 'error', 'warning']:
                if field in data and data[field]:
                    message = str(data[field])
                    return message[:100] + "..." if len(message) > 100 else message
        
        # Extract file path if available
        file_path = event.get('file_path') or data.get('file_path')
        if file_path:
            import os
            filename = os.path.basename(file_path)
            event_type = event.get('type', 'event')
            return f"{event_type.replace('_', ' ').title()} in {filename}"
        
        # Fallback to event type
        event_type = event.get('type', 'unknown')
        return f"{event_type.replace('_', ' ').title()} detected"