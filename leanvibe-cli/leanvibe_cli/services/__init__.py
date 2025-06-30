"""
Services package for LeanVibe CLI

Contains background services for notifications, monitoring, and real-time features.
"""

from .notification_service import NotificationService
from .desktop_notifications import DesktopNotificationService, NotificationTriggers

__all__ = ["NotificationService", "DesktopNotificationService", "NotificationTriggers"]