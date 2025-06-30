"""
UI package for LeanVibe CLI

Contains user interface components for notifications, overlays, and live displays.
"""

from .notification_overlay import NotificationOverlay, NotificationHistory
from .live_dashboard import LiveMetricsDashboard

__all__ = ["NotificationOverlay", "NotificationHistory", "LiveMetricsDashboard"]