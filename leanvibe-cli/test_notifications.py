#!/usr/bin/env python3
"""
Test script for Sprint 2.3 notification system

Tests the background notification service and desktop notifications.
"""

import asyncio
import sys
from datetime import datetime

# Add the leanvibe_cli package to the path
sys.path.insert(0, '/Users/bogdan/work/leanvibe-ai/leanvibe-cli')

from leanvibe_cli.config import CLIConfig
from leanvibe_cli.services import NotificationService, DesktopNotificationService, NotificationTriggers
from leanvibe_cli.ui import NotificationOverlay, NotificationHistory


async def test_desktop_notifications():
    """Test desktop notification system"""
    print("🔔 Testing Desktop Notifications...")
    
    service = DesktopNotificationService()
    print(f"Platform: {service.platform}")
    print(f"Available: {service.notification_available}")
    
    if service.notification_available:
        # Test critical notification
        success = await service.send_notification(
            title="Test Critical Alert",
            message="This is a test critical notification from LeanVibe CLI",
            priority="critical",
            sound=False,
            timeout=3
        )
        print(f"Critical notification: {'✅ Success' if success else '❌ Failed'}")
        
        await asyncio.sleep(1)
        
        # Test normal notification
        success = await service.send_notification(
            title="Test Normal Alert", 
            message="This is a test normal notification",
            priority="normal",
            sound=False,
            timeout=3
        )
        print(f"Normal notification: {'✅ Success' if success else '❌ Failed'}")
    else:
        print("❌ Desktop notifications not available on this platform")


def test_notification_triggers():
    """Test notification trigger system"""
    print("\n🎯 Testing Notification Triggers...")
    
    # Test critical event
    critical_event = {
        'type': 'architectural_violation',
        'priority': 'critical',
        'message': 'Test architectural violation detected',
        'file_path': '/test/file.py'
    }
    
    config = CLIConfig()
    should_notify = NotificationTriggers.should_send_desktop_notification(critical_event, config)
    print(f"Critical event should notify: {'✅ Yes' if should_notify else '❌ No'}")
    
    if should_notify:
        notification_data = NotificationTriggers.format_desktop_notification(critical_event)
        print(f"Formatted notification: {notification_data}")
    
    # Test medium priority event
    medium_event = {
        'type': 'code_quality_warning',
        'priority': 'medium',
        'message': 'Test code quality warning',
        'file_path': '/test/quality.py'
    }
    
    should_notify = NotificationTriggers.should_send_desktop_notification(medium_event, config)
    print(f"Medium event should notify: {'✅ Yes' if should_notify else '❌ No'}")


def test_notification_overlay():
    """Test notification overlay system"""
    print("\n📱 Testing Notification Overlay...")
    
    overlay = NotificationOverlay()
    
    # Test formatting
    test_event = {
        'type': 'test_event',
        'priority': 'high',
        'message': 'This is a test overlay notification',
        'timestamp': datetime.now().isoformat()
    }
    
    notification = overlay._format_notification(test_event)
    print(f"Formatted overlay notification: {notification}")
    
    # Test notification history
    history = NotificationHistory()
    history.add_notification(test_event, datetime.now())
    
    stats = history.get_stats()
    print(f"History stats: {stats}")


def test_config():
    """Test configuration with notification settings"""
    print("\n⚙️ Testing Configuration...")
    
    config = CLIConfig()
    print(f"Desktop notifications: {config.desktop_notifications}")
    print(f"Terminal notifications: {config.terminal_notifications}")
    print(f"Notification level: {config.notification_level}")
    print(f"Throttle seconds: {config.notification_throttle_seconds}")
    print(f"Max per minute: {config.max_notifications_per_minute}")
    print(f"Enabled event types: {config.enabled_event_types}")


async def main():
    """Run all tests"""
    print("🧪 LeanVibe CLI Notification System Tests")
    print("=" * 50)
    
    test_config()
    test_notification_triggers()
    test_notification_overlay()
    
    # Test desktop notifications (requires user interaction)
    await test_desktop_notifications()
    
    print("\n✅ All tests completed!")
    print("\nNote: Desktop notifications should have appeared if supported on your platform.")


if __name__ == "__main__":
    asyncio.run(main())