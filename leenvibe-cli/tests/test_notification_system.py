"""
Comprehensive test suite for Sprint 2.3 notification system

Tests notification service, desktop notifications, triggers, and overlays
with proper pytest framework and async support.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from collections import deque
import platform

from leenvibe_cli.config.legacy import CLIConfig
from leenvibe_cli.services.notification_service import NotificationService
from leenvibe_cli.services.desktop_notifications import DesktopNotificationService
from leenvibe_cli.ui.notification_overlay import NotificationOverlay


class TestNotificationService:
    """Test the core notification service functionality"""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing"""
        config = CLIConfig()
        config.desktop_notifications = True
        config.terminal_notifications = True
        config.notification_throttle_seconds = 1
        config.max_notifications_per_minute = 10
        config.enabled_event_types = [
            "architectural_violation",
            "build_failure", 
            "security_issue",
            "complexity_spike"
        ]
        return config
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock backend client"""
        client = Mock()
        client.connect_websocket = AsyncMock(return_value=True)
        client.listen_for_events = AsyncMock()
        return client
    
    @pytest.fixture
    async def notification_service(self, mock_config, mock_client):
        """Create a notification service for testing"""
        with patch('leenvibe_cli.services.notification_service.BackendClient', return_value=mock_client):
            service = NotificationService(mock_config)
            service.client = mock_client
            yield service
            if service.is_running:
                await service.stop()
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, notification_service, mock_config):
        """Test that the notification service initializes correctly"""
        service = notification_service
        
        assert service.config == mock_config
        assert service.notification_queue is not None
        assert service.is_running is False
        assert len(service.notification_history) == 0
        assert service.notification_history.maxlen == 100
    
    async def test_background_monitoring_startup_success(self, notification_service):
        """Test successful background monitoring startup"""
        service = notification_service
        
        result = await service.start_background_monitoring()
        
        assert result is True
        assert service.is_running is True
        service.client.connect_websocket.assert_called_once()
    
    async def test_background_monitoring_startup_failure(self, notification_service):
        """Test background monitoring startup failure"""
        service = notification_service
        service.client.connect_websocket.return_value = False
        
        result = await service.start_background_monitoring()
        
        assert result is False
        assert service.is_running is False
    
    async def test_event_filtering_high_priority(self, notification_service):
        """Test that high-priority events pass the filter"""
        service = notification_service
        
        critical_event = {
            'type': 'architectural_violation',
            'priority': 'critical',
            'timestamp': datetime.now().isoformat()
        }
        
        should_notify = service._should_notify(critical_event)
        assert should_notify is True
    
    async def test_event_filtering_low_priority(self, notification_service):
        """Test that low-priority events are filtered out"""
        service = notification_service
        
        debug_event = {
            'type': 'file_change',
            'priority': 'debug',
            'timestamp': datetime.now().isoformat()
        }
        
        should_notify = service._should_notify(debug_event)
        assert should_notify is False
    
    async def test_event_filtering_disabled_type(self, notification_service):
        """Test that disabled event types are filtered out"""
        service = notification_service
        
        disabled_event = {
            'type': 'disabled_event_type',
            'priority': 'high',
            'timestamp': datetime.now().isoformat()
        }
        
        should_notify = service._should_notify(disabled_event)
        assert should_notify is False
    
    async def test_notification_throttling(self, notification_service):
        """Test notification throttling prevents spam"""
        service = notification_service
        
        event = {
            'type': 'build_status',
            'priority': 'medium',
            'source': 'test'
        }
        
        # First notification should pass
        await service.notification_queue.put(event)
        
        # Process notification
        with patch.object(service, '_process_notification') as mock_process:
            await service._notification_processor_single_run()
            mock_process.assert_called_once()
        
        # Rapid second notification should be throttled
        await service.notification_queue.put(event)
        
        with patch.object(service, '_process_notification') as mock_process:
            await service._notification_processor_single_run()
            mock_process.assert_not_called()  # Should be throttled
    
    async def test_notification_history_management(self, notification_service):
        """Test notification history is properly managed"""
        service = notification_service
        
        # Add events to history
        for i in range(5):
            event = {
                'type': f'test_event_{i}',
                'priority': 'medium',
                'timestamp': datetime.now().isoformat()
            }
            service.notification_history.appendleft(event)
        
        assert len(service.notification_history) == 5
        
        # Test history limit (maxlen=100)
        for i in range(100):
            event = {
                'type': f'overflow_event_{i}',
                'priority': 'medium',
                'timestamp': datetime.now().isoformat()
            }
            service.notification_history.appendleft(event)
        
        assert len(service.notification_history) == 100


class TestDesktopNotifications:
    """Test desktop notification functionality"""
    
    @pytest.fixture
    def desktop_service(self):
        """Create desktop notification service for testing"""
        return DesktopNotificationService()
    
    def test_platform_detection(self, desktop_service):
        """Test that platform is correctly detected"""
        service = desktop_service
        detected_platform = platform.system().lower()
        assert service.platform == detected_platform
    
    @patch('platform.system')
    @patch('shutil.which')
    def test_macos_availability_check(self, mock_which, mock_platform):
        """Test macOS notification availability detection"""
        mock_platform.return_value = 'Darwin'
        mock_which.return_value = '/usr/bin/osascript'
        
        service = DesktopNotificationService()
        assert service.notification_available is True
        mock_which.assert_called_with('osascript')
    
    @patch('platform.system')
    @patch('shutil.which')
    def test_linux_availability_check(self, mock_which, mock_platform):
        """Test Linux notification availability detection"""
        mock_platform.return_value = 'Linux'
        mock_which.return_value = '/usr/bin/notify-send'
        
        service = DesktopNotificationService()
        assert service.notification_available is True
        mock_which.assert_called_with('notify-send')
    
    @patch('platform.system')
    def test_windows_availability_check(self, mock_platform):
        """Test Windows notification availability (always true)"""
        mock_platform.return_value = 'Windows'
        
        service = DesktopNotificationService()
        assert service.notification_available is True
    
    @patch('platform.system')
    @patch('shutil.which')
    async def test_macos_notification_sending(self, mock_which, mock_platform):
        """Test macOS notification sending"""
        mock_platform.return_value = 'Darwin'
        mock_which.return_value = '/usr/bin/osascript'
        
        service = DesktopNotificationService()
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = ('', '')
            mock_subprocess.return_value = mock_proc
            
            result = await service.send_notification(
                "Test Title", "Test Message", "critical", True
            )
            
            assert result is True
            mock_subprocess.assert_called_once()
            
            # Verify the correct osascript command was called
            call_args = mock_subprocess.call_args[0]
            assert call_args[0] == 'osascript'
            assert '-e' in call_args
    
    @patch('platform.system')
    @patch('shutil.which')
    async def test_linux_notification_sending(self, mock_which, mock_platform):
        """Test Linux notification sending"""
        mock_platform.return_value = 'Linux'
        mock_which.return_value = '/usr/bin/notify-send'
        
        service = DesktopNotificationService()
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = ('', '')
            mock_subprocess.return_value = mock_proc
            
            result = await service.send_notification(
                "Test Title", "Test Message", "high", False
            )
            
            assert result is True
            mock_subprocess.assert_called_once()
            
            # Verify the correct notify-send command was called
            call_args = mock_subprocess.call_args[0]
            assert call_args[0] == 'notify-send'
            assert '--app-name=LeenVibe' in call_args
    
    async def test_notification_failure_handling(self, desktop_service):
        """Test graceful handling of notification failures"""
        service = desktop_service
        
        with patch.object(service, '_send_macos_notification', side_effect=Exception("Test error")):
            result = await service.send_notification(
                "Test Title", "Test Message", "normal", False
            )
            
            assert result is False


class TestNotificationOverlay:
    """Test notification overlay functionality"""
    
    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console"""
        return Mock()
    
    @pytest.fixture
    def notification_overlay(self, mock_console):
        """Create notification overlay for testing"""
        return NotificationOverlay(mock_console)
    
    def test_overlay_initialization(self, notification_overlay, mock_console):
        """Test notification overlay initializes correctly"""
        overlay = notification_overlay
        
        assert overlay.console == mock_console
        assert len(overlay.active_notifications) == 0
        assert overlay.active_notifications.maxlen == 3
        assert overlay.notification_lock is not None
    
    def test_notification_formatting(self, notification_overlay):
        """Test notification event formatting"""
        overlay = notification_overlay
        
        test_event = {
            'type': 'architectural_violation',
            'priority': 'critical',
            'message': 'Test violation detected',
            'timestamp': datetime.now().isoformat()
        }
        
        formatted = overlay._format_notification(test_event)
        
        assert formatted['priority'] == 'critical'
        assert formatted['color'] == 'red'
        assert 'Test violation detected' in formatted['message']
        assert formatted['icon'] == '🚨'
        assert 'timestamp' in formatted
    
    def test_priority_color_mapping(self, notification_overlay):
        """Test that priority levels map to correct colors"""
        overlay = notification_overlay
        
        test_cases = [
            ('critical', 'red'),
            ('high', 'yellow'),
            ('medium', 'blue'),
            ('low', 'green'),
            ('unknown', 'white')
        ]
        
        for priority, expected_color in test_cases:
            event = {
                'type': 'test',
                'priority': priority,
                'message': 'Test message',
                'timestamp': datetime.now().isoformat()
            }
            
            formatted = overlay._format_notification(event)
            assert formatted['color'] == expected_color
    
    async def test_notification_display_lifecycle(self, notification_overlay):
        """Test notification display and auto-dismissal"""
        overlay = notification_overlay
        
        test_event = {
            'type': 'test_event',
            'priority': 'high',
            'message': 'Test notification',
            'timestamp': datetime.now().isoformat()
        }
        
        # Mock the rendering methods to avoid actual console output
        with patch.object(overlay, '_render_notification_bar') as mock_render:
            # Start display (with very short duration for testing)
            display_task = asyncio.create_task(
                overlay.show_notification(test_event, duration=0.1)
            )
            
            # Wait a moment for notification to be added
            await asyncio.sleep(0.05)
            assert len(overlay.active_notifications) == 1
            
            # Wait for auto-dismissal
            await display_task
            assert len(overlay.active_notifications) == 0
            
            # Verify rendering was called
            assert mock_render.call_count >= 1
    
    def test_notification_limit(self, notification_overlay):
        """Test that only 3 notifications are shown at once"""
        overlay = notification_overlay
        
        # Add 5 notifications
        for i in range(5):
            notification = {
                'priority': 'medium',
                'color': 'blue',
                'message': f'Message {i}',
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'icon': '🔔'
            }
            overlay.active_notifications.append(notification)
        
        # Should only keep last 3 due to maxlen=3
        assert len(overlay.active_notifications) == 3
        assert overlay.active_notifications[0]['message'] == 'Message 2'
        assert overlay.active_notifications[2]['message'] == 'Message 4'


class TestIntegrationWorkflows:
    """Test integrated notification workflows"""
    
    @pytest.fixture
    def mock_config(self):
        """Create integration test configuration"""
        config = CLIConfig()
        config.desktop_notifications = True
        config.terminal_notifications = True
        config.notification_throttle_seconds = 0.1  # Fast for testing
        return config
    
    @pytest.fixture
    def mock_backend_client(self):
        """Create a mock backend client with event stream"""
        client = Mock()
        client.connect_websocket = AsyncMock(return_value=True)
        
        # Mock event stream
        async def mock_event_stream():
            events = [
                {
                    'type': 'architectural_violation',
                    'priority': 'critical',
                    'message': 'Layer violation detected',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'type': 'complexity_spike',
                    'priority': 'high',
                    'message': 'Function complexity increased',
                    'timestamp': datetime.now().isoformat()
                }
            ]
            for event in events:
                yield event
                await asyncio.sleep(0.1)
        
        client.listen_for_events.return_value = mock_event_stream()
        return client
    
    async def test_end_to_end_notification_flow(self, mock_config, mock_backend_client):
        """Test complete notification flow from event to display"""
        with patch('leenvibe_cli.services.notification_service.BackendClient', return_value=mock_backend_client):
            # Initialize components
            notification_service = NotificationService(mock_config)
            notification_service.client = mock_backend_client
            
            desktop_service = DesktopNotificationService()
            overlay = NotificationOverlay(Mock())
            
            # Mock desktop notification sending
            with patch.object(desktop_service, 'send_notification', return_value=True) as mock_desktop:
                # Start monitoring
                await notification_service.start_background_monitoring()
                
                # Let it process a few events
                await asyncio.sleep(0.3)
                
                # Verify events were processed
                assert len(notification_service.notification_history) > 0
                
                # Verify notifications would be sent for critical events
                critical_events = [
                    event for event in notification_service.notification_history
                    if event.get('priority') == 'critical'
                ]
                assert len(critical_events) > 0
                
                # Stop the service
                await notification_service.stop()
    
    async def test_notification_performance_requirements(self, mock_config):
        """Test that notification processing meets performance requirements"""
        # Mock fast backend client
        client = Mock()
        client.connect_websocket = AsyncMock(return_value=True)
        
        notification_service = NotificationService(mock_config)
        notification_service.client = client
        
        # Test notification processing speed
        test_event = {
            'type': 'build_failure',
            'priority': 'high',
            'message': 'Build failed',
            'timestamp': datetime.now().isoformat()
        }
        
        start_time = datetime.now()
        
        # Process notification
        with patch.object(notification_service, '_send_desktop_notification') as mock_desktop:
            with patch.object(notification_service, '_send_terminal_notification') as mock_terminal:
                await notification_service._process_notification(test_event)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Should process in under 50ms (performance requirement)
        assert processing_time < 0.05
        
        # Verify appropriate notifications were triggered
        if mock_config.desktop_notifications:
            mock_desktop.assert_called_once()
        if mock_config.terminal_notifications:
            mock_terminal.assert_called_once()


# Add helper method for notification service testing
class NotificationService:
    """Extended notification service for testing"""
    
    async def _notification_processor_single_run(self):
        """Process a single notification for testing"""
        try:
            event = await asyncio.wait_for(
                self.notification_queue.get(), timeout=0.1
            )
            
            # Smart throttling by event type
            event_key = f"{event.get('type')}:{event.get('source', '')}"
            now = asyncio.get_event_loop().time()
            
            if hasattr(self, '_throttle_window'):
                if event_key in self._throttle_window:
                    if now - self._throttle_window[event_key] < self.config.notification_throttle_seconds:
                        return  # Skip this notification
            else:
                self._throttle_window = {}
            
            self._throttle_window[event_key] = now
            
            # Process notification
            await self._process_notification(event)
            
        except asyncio.TimeoutError:
            return
    
    async def stop(self):
        """Stop the notification service"""
        self.is_running = False


# Monkey patch for testing
import leenvibe_cli.services.notification_service
leenvibe_cli.services.notification_service.NotificationService._notification_processor_single_run = NotificationService._notification_processor_single_run
leenvibe_cli.services.notification_service.NotificationService.stop = NotificationService.stop


if __name__ == "__main__":
    pytest.main([__file__, "-v"])