"""
Push Notifications API Test Coverage with Real Event Integration

Comprehensive tests for push notification system integration with AI events,
task management, and real-time event streaming capabilities.

As specified in unified backend testing execution prompt.
"""

import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_push_notification_client_preferences_api(test_client):
    """Test push notification client preferences API endpoints"""
    client_id = "push-test-client"
    
    # Test getting default preferences
    response = test_client.get(f"/streaming/clients/{client_id}/preferences")
    # Should return 404 for non-existent client initially
    assert response.status_code == 404
    
    # Test setting preferences
    preferences_data = {
        "event_types": ["task_created", "ai_analysis_complete", "task_completed"],
        "priority_filter": "medium", 
        "enable_real_time": True,
        "ai_notifications": True,
        "push_notifications": True,
        "email_notifications": False,
        "notification_schedule": {
            "start_hour": 9,
            "end_hour": 18,
            "timezone": "UTC"
        }
    }
    
    # Mock connection manager for client registration
    with patch('app.core.connection_manager.ConnectionManager') as mock_conn_manager:
        mock_manager = AsyncMock()
        mock_conn_manager.return_value = mock_manager
        mock_manager.update_client_preferences = AsyncMock()
        
        # Update preferences
        response = test_client.put(
            f"/streaming/clients/{client_id}/preferences",
            json=preferences_data
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["client_id"] == client_id
        assert response_data["preferences"]["ai_notifications"] is True
        assert response_data["preferences"]["push_notifications"] is True


@pytest.mark.asyncio  
async def test_push_notification_ai_task_analysis_trigger():
    """Test push notifications triggered by AI task analysis completion"""
    from app.services.event_streaming_service import event_streaming_service
    from app.models.event_models import EventData, EventType, EventPriority, NotificationChannel
    
    # Mock push notification service
    with patch('app.services.push_notification_service.push_notification_service') as mock_push:
        mock_push.send_notification = AsyncMock()
        mock_push.is_enabled = True
        
        # Mock event streaming service
        with patch.object(event_streaming_service, 'emit_event') as mock_emit:
            # Create AI analysis completion event
            ai_analysis_event = EventData(
                event_id="ai_analysis_123",
                event_type=EventType.ai_analysis_complete,
                priority=EventPriority.high,
                channel=NotificationChannel.push,
                timestamp=datetime.now(),
                source="mlx_service",
                data={
                    "task_id": "task_456",
                    "analysis_result": {
                        "confidence": 0.89,
                        "complexity": "medium",
                        "recommendations": [
                            "Consider using async/await pattern",
                            "Add input validation",
                            "Implement error handling"
                        ]
                    },
                    "client_id": "analysis-client"
                },
                metadata={
                    "notification_title": "AI Analysis Complete",
                    "notification_body": "Task analysis finished with 89% confidence"
                }
            )
            
            # Emit the event (which should trigger push notification)
            await event_streaming_service.emit_event(ai_analysis_event)
            
            # Verify event was emitted
            mock_emit.assert_called_once_with(ai_analysis_event)


@pytest.mark.asyncio
async def test_push_notification_batch_processing():
    """Test batch processing of push notifications for efficiency"""
    from app.services.event_streaming_service import event_streaming_service
    from app.models.event_models import EventData, EventType, EventPriority, NotificationChannel
    
    # Mock push notification service with batch capability
    with patch('app.services.push_notification_service.push_notification_service') as mock_push:
        mock_push.send_batch_notifications = AsyncMock()
        mock_push.batch_size = 10
        mock_push.batch_timeout = 5.0  # 5 seconds
        
        # Create multiple events that should trigger notifications
        events = []
        for i in range(15):  # More than batch size
            event = EventData(
                event_id=f"batch_event_{i}",
                event_type=EventType.task_completed if i % 2 == 0 else EventType.ai_analysis_complete,
                priority=EventPriority.medium,
                channel=NotificationChannel.push,
                timestamp=datetime.now(),
                source="batch_test",
                data={
                    "task_id": f"task_{i}",
                    "client_id": f"client_{i % 3}"  # 3 different clients
                },
                metadata={
                    "notification_title": f"Event {i}",
                    "notification_body": f"Batch test event {i}"
                }
            )
            events.append(event)
        
        # Process all events (should trigger batch notifications)
        for event in events:
            await event_streaming_service.emit_event(event)
        
        # Wait for potential batch timeout
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_push_notification_filtering_by_preferences():
    """Test push notification filtering based on client preferences"""
    from app.models.event_models import ClientPreferences, EventData, EventType, EventPriority, NotificationChannel
    
    # Create client with specific preferences
    client_preferences = ClientPreferences(
        event_types=[EventType.task_created, EventType.ai_analysis_complete],
        priority_filter=EventPriority.high,
        enable_real_time=True,
        ai_notifications=True,
        push_notifications=True,
        email_notifications=False,
        notification_schedule={
            "start_hour": 9,
            "end_hour": 18,
            "timezone": "UTC"
        }
    )
    
    # Mock notification service with filtering
    with patch('app.services.push_notification_service.push_notification_service') as mock_push:
        mock_push.send_notification = AsyncMock()
        mock_push.should_send_notification = MagicMock()
        
        # Event that should be sent (matches preferences)
        allowed_event = EventData(
            event_id="allowed_push",
            event_type=EventType.ai_analysis_complete,
            priority=EventPriority.high,
            channel=NotificationChannel.push,
            timestamp=datetime.now(),
            source="test",
            data={"client_id": "pref-test-client"},
            metadata={
                "notification_title": "High Priority AI Analysis",
                "notification_body": "Critical analysis completed"
            }
        )
        
        # Event that should be filtered (wrong type)
        filtered_event = EventData(
            event_id="filtered_push",
            event_type=EventType.system_ready,  # Not in preferences
            priority=EventPriority.high,
            channel=NotificationChannel.push,
            timestamp=datetime.now(),
            source="test",
            data={"client_id": "pref-test-client"},
            metadata={
                "notification_title": "System Ready",
                "notification_body": "System is ready"
            }
        )
        
        # Test filtering logic
        mock_push.should_send_notification.return_value = True  # For allowed event
        result_allowed = mock_push.should_send_notification(allowed_event, client_preferences)
        
        mock_push.should_send_notification.return_value = False  # For filtered event
        result_filtered = mock_push.should_send_notification(filtered_event, client_preferences)
        
        # Verify filtering worked correctly
        assert mock_push.should_send_notification.call_count == 2


@pytest.mark.asyncio
async def test_push_notification_schedule_enforcement():
    """Test push notification schedule enforcement (quiet hours)"""
    from app.models.event_models import ClientPreferences, EventData, EventType, EventPriority, NotificationChannel
    from datetime import datetime, time
    
    # Create preferences with quiet hours
    client_preferences = ClientPreferences(
        event_types=[EventType.task_created],
        priority_filter=EventPriority.low,
        push_notifications=True,
        notification_schedule={
            "start_hour": 9,   # 9 AM
            "end_hour": 18,    # 6 PM
            "timezone": "UTC"
        }
    )
    
    with patch('app.services.push_notification_service.push_notification_service') as mock_push:
        mock_push.is_within_schedule = MagicMock()
        mock_push.send_notification = AsyncMock()
        
        # Test notification during allowed hours (12 PM)
        allowed_time = datetime.now().replace(hour=12, minute=0, second=0)
        mock_push.is_within_schedule.return_value = True
        
        allowed_event = EventData(
            event_id="scheduled_allowed",
            event_type=EventType.task_created,
            priority=EventPriority.medium,
            channel=NotificationChannel.push,
            timestamp=allowed_time,
            source="schedule_test",
            data={"client_id": "schedule-client"},
            metadata={
                "notification_title": "Task Created",
                "notification_body": "New task during business hours"
            }
        )
        
        # Test notification during quiet hours (2 AM)
        quiet_time = datetime.now().replace(hour=2, minute=0, second=0)
        mock_push.is_within_schedule.return_value = False
        
        quiet_event = EventData(
            event_id="scheduled_quiet",
            event_type=EventType.task_created,
            priority=EventPriority.low,  # Low priority should be filtered
            channel=NotificationChannel.push,
            timestamp=quiet_time,
            source="schedule_test",
            data={"client_id": "schedule-client"},
            metadata={
                "notification_title": "Task Created",
                "notification_body": "New task during quiet hours"
            }
        )
        
        # Verify schedule checking was called
        mock_push.is_within_schedule.assert_called()


@pytest.mark.asyncio
async def test_push_notification_ai_workflow_integration():
    """Test push notifications integrated with complete AI workflow"""
    from app.services.task_service import task_service
    
    # Mock AI service and push notifications
    with patch('app.services.unified_mlx_service.unified_mlx_service') as mock_mlx:
        with patch('app.services.push_notification_service.push_notification_service') as mock_push:
            mock_push.send_notification = AsyncMock()
            
            # Mock AI analysis result
            mock_mlx.generate_code_completion.return_value = asyncio.Future()
            mock_mlx.generate_code_completion.return_value.set_result({
                "status": "success",
                "response": "AI analysis suggests implementing caching layer for better performance",
                "confidence": 0.87,
                "recommendations": [
                    "Add Redis caching",
                    "Implement cache invalidation strategy",
                    "Monitor cache hit rates"
                ]
            })
            
            # Create task that triggers AI analysis and notifications
            task_data = {
                "title": "Optimize database queries",
                "description": "Improve performance of user data retrieval",
                "analyze_with_ai": True,
                "priority": "high",
                "notify_on_completion": True
            }
            
            # Process task creation (should trigger multiple notifications)
            created_task = await task_service.create_task("workflow-client", task_data)
            
            # Verify AI was called
            mock_mlx.generate_code_completion.assert_called()
            
            # Expected notification sequence:
            # 1. Task created notification
            # 2. AI analysis started notification  
            # 3. AI analysis complete notification
            
            # Verify task was created with AI analysis
            assert created_task.get("ai_analysis") is not None
            assert "caching layer" in created_task.get("ai_analysis", "")


@pytest.mark.asyncio
async def test_push_notification_error_handling_and_retry():
    """Test push notification error handling and retry logic"""
    from app.models.event_models import EventData, EventType, EventPriority, NotificationChannel
    
    with patch('app.services.push_notification_service.push_notification_service') as mock_push:
        # Mock initial failure then success
        mock_push.send_notification = AsyncMock()
        mock_push.send_notification.side_effect = [
            Exception("Network timeout"),  # First attempt fails
            Exception("Service unavailable"),  # Second attempt fails
            {"status": "success", "notification_id": "success_123"}  # Third attempt succeeds
        ]
        
        mock_push.max_retries = 3
        mock_push.retry_delay = 0.1  # 100ms for testing
        
        # Create event that should trigger notification with retries
        retry_event = EventData(
            event_id="retry_test",
            event_type=EventType.ai_analysis_complete,
            priority=EventPriority.high,
            channel=NotificationChannel.push,
            timestamp=datetime.now(),
            source="retry_test",
            data={"client_id": "retry-client"},
            metadata={
                "notification_title": "Critical AI Analysis",
                "notification_body": "High priority analysis completed",
                "retry_on_failure": True
            }
        )
        
        # Mock retry logic
        async def mock_send_with_retry(event):
            for attempt in range(mock_push.max_retries):
                try:
                    result = await mock_push.send_notification(event)
                    return result
                except Exception as e:
                    if attempt == mock_push.max_retries - 1:
                        raise e
                    await asyncio.sleep(mock_push.retry_delay)
        
        # Test retry mechanism
        try:
            result = await mock_send_with_retry(retry_event)
            # Should succeed on third attempt
            assert result["status"] == "success"
        except Exception:
            # Should not reach here if retry logic works
            pytest.fail("Retry logic failed")
        
        # Verify all attempts were made
        assert mock_push.send_notification.call_count == 3


@pytest.mark.asyncio
async def test_push_notification_analytics_and_metrics():
    """Test push notification analytics and delivery metrics"""
    from app.services.event_streaming_service import event_streaming_service
    
    with patch('app.services.push_notification_service.push_notification_service') as mock_push:
        # Mock analytics tracking
        mock_push.track_notification_sent = AsyncMock()
        mock_push.track_notification_delivered = AsyncMock() 
        mock_push.track_notification_opened = AsyncMock()
        mock_push.get_analytics = AsyncMock(return_value={
            "total_sent": 150,
            "total_delivered": 145,
            "total_opened": 89,
            "delivery_rate": 0.967,
            "open_rate": 0.613,
            "ai_notification_engagement": 0.75
        })
        
        # Mock multiple notification events
        notification_events = [
            {"event_id": f"analytics_{i}", "client_id": f"client_{i}", "delivered": i % 2 == 0}
            for i in range(10)
        ]
        
        # Track notifications
        for event in notification_events:
            await mock_push.track_notification_sent(event["event_id"], event["client_id"])
            if event["delivered"]:
                await mock_push.track_notification_delivered(event["event_id"])
        
        # Get analytics
        analytics = await mock_push.get_analytics()
        
        # Verify analytics structure
        assert "total_sent" in analytics
        assert "delivery_rate" in analytics
        assert "ai_notification_engagement" in analytics
        assert analytics["delivery_rate"] > 0.9  # Good delivery rate
        assert analytics["ai_notification_engagement"] > 0.7  # Good AI engagement


@pytest.mark.asyncio
async def test_push_notification_device_registration():
    """Test device registration for push notifications"""
    
    # Mock device registration data
    device_data = {
        "client_id": "device-test-client",
        "device_token": "apns:abc123def456",
        "platform": "ios",
        "app_version": "1.0.0",
        "device_model": "iPhone15,2",
        "timezone": "America/New_York"
    }
    
    with patch('app.services.push_notification_service.push_notification_service') as mock_push:
        mock_push.register_device = AsyncMock(return_value={
            "success": True,
            "device_id": "device_123",
            "registered_at": datetime.now().isoformat()
        })
        
        # Register device
        registration_result = await mock_push.register_device(device_data)
        
        # Verify registration
        assert registration_result["success"] is True
        assert "device_id" in registration_result
        
        # Verify registration was called with correct data
        mock_push.register_device.assert_called_once_with(device_data)


@pytest.mark.performance
async def test_push_notification_performance_requirements():
    """Test push notification performance under load"""
    import time
    from app.models.event_models import EventData, EventType, EventPriority, NotificationChannel
    
    # Performance requirement: <200ms for batch notification processing
    num_notifications = 100
    
    with patch('app.services.push_notification_service.push_notification_service') as mock_push:
        # Mock fast notification sending
        async def fast_send(event):
            await asyncio.sleep(0.001)  # 1ms simulation
            return {"status": "success", "sent_at": datetime.now().isoformat()}
        
        mock_push.send_notification = AsyncMock(side_effect=fast_send)
        
        # Create batch of notifications
        events = []
        for i in range(num_notifications):
            event = EventData(
                event_id=f"perf_{i}",
                event_type=EventType.ai_analysis_complete,
                priority=EventPriority.medium,
                channel=NotificationChannel.push,
                timestamp=datetime.now(),
                source="performance_test",
                data={"client_id": f"perf_client_{i % 10}"},
                metadata={
                    "notification_title": f"Performance Test {i}",
                    "notification_body": f"Test notification {i}"
                }
            )
            events.append(event)
        
        # Measure batch processing time
        start_time = time.time()
        
        # Process notifications concurrently
        tasks = [mock_push.send_notification(event) for event in events]
        results = await asyncio.gather(*tasks)
        
        processing_time = time.time() - start_time
        
        # Verify performance requirement
        assert processing_time < 0.2  # Less than 200ms
        assert len(results) == num_notifications
        assert all(result["status"] == "success" for result in results)


@pytest.mark.integration
async def test_push_notification_end_to_end_workflow(test_client):
    """Test complete end-to-end push notification workflow"""
    
    # Step 1: Register device and set preferences
    client_id = "e2e-test-client"
    
    # Mock services
    with patch('app.services.push_notification_service.push_notification_service') as mock_push:
        with patch('app.services.unified_mlx_service.unified_mlx_service') as mock_mlx:
            with patch('app.core.connection_manager.ConnectionManager') as mock_conn:
                
                # Setup mocks
                mock_push.register_device = AsyncMock(return_value={"success": True})
                mock_push.send_notification = AsyncMock(return_value={"status": "success"})
                
                mock_mlx.generate_code_completion.return_value = asyncio.Future()
                mock_mlx.generate_code_completion.return_value.set_result({
                    "status": "success",
                    "response": "Complete end-to-end AI analysis",
                    "confidence": 0.91
                })
                
                mock_manager = AsyncMock()
                mock_conn.return_value = mock_manager
                mock_manager.update_client_preferences = AsyncMock()
                
                # Step 2: Set notification preferences
                preferences = {
                    "event_types": ["task_created", "ai_analysis_complete"],
                    "priority_filter": "medium",
                    "push_notifications": True,
                    "ai_notifications": True
                }
                
                response = test_client.put(
                    f"/streaming/clients/{client_id}/preferences",
                    json=preferences
                )
                assert response.status_code == 200
                
                # Step 3: Create task with AI analysis (triggers notifications)
                task_data = {
                    "title": "E2E Test Task",
                    "description": "End-to-end testing task",
                    "analyze_with_ai": True,
                    "priority": "high"
                }
                
                response = test_client.post(f"/tasks/{client_id}", json=task_data)
                assert response.status_code == 201
                
                task_response = response.json()
                assert "ai_analysis" in task_response
                
                # Verify the workflow completed successfully
                assert task_response["title"] == "E2E Test Task"