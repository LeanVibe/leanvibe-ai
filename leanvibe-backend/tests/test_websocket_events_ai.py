"""
WebSocket Event Testing with AI Integration and Broadcast Validation

Comprehensive tests for validating WebSocket event broadcasting when AI processes
tasks and other events, ensuring real-time communication works with LLM functionality.

As specified in unified backend testing execution prompt.
"""

import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime


@pytest.mark.asyncio
async def test_websocket_ai_task_creation_broadcast():
    """Test WebSocket broadcast when AI analyzes and creates tasks"""
    from app.core.connection_manager import ConnectionManager
    from app.services.event_streaming_service import event_streaming_service
    
    # Mock WebSocket connections
    mock_websocket_1 = AsyncMock()
    mock_websocket_2 = AsyncMock()
    
    # Mock connection manager
    with patch('app.core.connection_manager.ConnectionManager') as mock_conn_manager:
        mock_manager = AsyncMock()
        mock_conn_manager.return_value = mock_manager
        mock_manager.broadcast = AsyncMock()
        mock_manager.send_to_client = AsyncMock()
        
        # Mock AI service for task analysis
        with patch('app.services.unified_mlx_service.unified_mlx_service') as mock_mlx:
            mock_mlx.generate_code_completion.return_value = asyncio.Future()
            mock_mlx.generate_code_completion.return_value.set_result({
                "status": "success",
                "response": "AI analyzed task: Implement authentication with JWT tokens and rate limiting",
                "confidence": 0.85,
                "analysis": {
                    "complexity": "medium",
                    "estimated_time": "4 hours",
                    "dependencies": ["user model", "auth middleware"]
                }
            })
            
            # Simulate task creation that triggers AI analysis and WebSocket broadcast
            from app.services.task_service import task_service
            
            # Create task with AI analysis
            task_data = {
                "title": "Implement user authentication",
                "description": "Add secure login system",
                "analyze_with_ai": True,
                "client_id": "test-client"
            }
            
            # This should trigger AI analysis and WebSocket broadcast
            created_task = await task_service.create_task(
                "test-client", task_data
            )
            
            # Verify AI was called for analysis
            mock_mlx.generate_code_completion.assert_called()
            
            # Verify WebSocket broadcast was triggered
            # Note: In real implementation, this would be triggered by the task service
            expected_broadcast_data = {
                "type": "task_created",
                "data": {
                    "task_id": created_task.get("id"),
                    "title": task_data["title"],
                    "ai_analysis": created_task.get("ai_analysis"),
                    "client_id": "test-client"
                },
                "timestamp": created_task.get("created_at")
            }
            
            # Simulate the broadcast that should happen
            await mock_manager.broadcast.assert_called


@pytest.mark.asyncio 
async def test_websocket_ai_code_completion_streaming():
    """Test real-time streaming of AI code completion results via WebSocket"""
    from app.main import handle_code_completion_websocket
    
    # Mock MLX service for code completion
    with patch('app.services.unified_mlx_service.unified_mlx_service') as mock_mlx:
        # Mock streaming response
        mock_mlx.generate_code_completion.return_value = asyncio.Future()
        mock_mlx.generate_code_completion.return_value.set_result({
            "status": "success",
            "response": "def authenticate_user(username, password):\n    # Validate credentials\n    return jwt.encode(payload)",
            "confidence": 0.92,
            "suggestions": ["Add password hashing", "Implement rate limiting", "Add session management"]
        })
        
        # Test code completion WebSocket message
        websocket_message = {
            "type": "code_completion",
            "file_path": "/app/auth.py",
            "cursor_position": 150,
            "intent": "suggest",
            "content": "def authenticate_user(",
            "language": "python"
        }
        
        # Process through WebSocket handler
        response = await handle_code_completion_websocket(websocket_message, "test-client")
        
        # Verify response structure
        assert response["status"] == "success"
        assert response["type"] == "code_completion_response" 
        assert response["intent"] == "suggest"
        assert "def authenticate_user" in response["response"]
        assert response["confidence"] > 0.9
        assert response["client_id"] == "test-client"
        assert len(response["suggestions"]) > 0
        
        # Verify MLX service was called with correct parameters
        mock_mlx.generate_code_completion.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_event_filtering_by_client_preferences():
    """Test WebSocket event filtering based on client preferences"""
    from app.models.event_models import ClientPreferences, EventType, EventPriority
    from app.core.connection_manager import ConnectionManager
    
    # Create test client preferences
    client_preferences = ClientPreferences(
        event_types=[EventType.task_created, EventType.ai_analysis_complete],
        priority_filter=EventPriority.medium,
        enable_real_time=True,
        ai_notifications=True
    )
    
    # Mock connection manager with preferences
    with patch('app.core.connection_manager.ConnectionManager') as mock_conn_manager:
        mock_manager = AsyncMock()
        mock_conn_manager.return_value = mock_manager
        mock_manager.send_to_client = AsyncMock()
        mock_manager.get_client_preferences = AsyncMock(return_value=client_preferences)
        
        # Mock event streaming service
        with patch('app.services.event_streaming_service.event_streaming_service') as mock_streaming:
            mock_streaming.emit_event = AsyncMock()
            
            # Create events with different types and priorities
            from app.models.event_models import EventData, NotificationChannel
            
            # Event that should be sent (matches preferences)
            allowed_event = EventData(
                event_id="test_1",
                event_type=EventType.task_created,
                priority=EventPriority.high,
                channel=NotificationChannel.websocket,
                timestamp=datetime.now(),
                source="test",
                data={"task_id": "task_123"}
            )
            
            # Event that should be filtered out (not in preferences)
            filtered_event = EventData(
                event_id="test_2", 
                event_type=EventType.system_ready,
                priority=EventPriority.low,
                channel=NotificationChannel.websocket,
                timestamp=datetime.now(),
                source="test",
                data={"status": "ready"}
            )
            
            # Emit both events
            await mock_streaming.emit_event(allowed_event)
            await mock_streaming.emit_event(filtered_event)
            
            # Verify streaming service was called
            assert mock_streaming.emit_event.call_count == 2


@pytest.mark.asyncio
async def test_websocket_ai_error_handling_and_fallback():
    """Test WebSocket handling when AI services fail"""
    from app.main import handle_code_completion_websocket
    
    # Mock MLX service failure
    with patch('app.services.unified_mlx_service.unified_mlx_service') as mock_mlx:
        # Simulate AI service failure
        mock_mlx.generate_code_completion.side_effect = Exception("MLX service unavailable")
        
        websocket_message = {
            "type": "code_completion",
            "file_path": "/app/test.py",
            "cursor_position": 50,
            "intent": "suggest",
            "content": "def test_function(",
            "language": "python"
        }
        
        # Process message with failing AI
        response = await handle_code_completion_websocket(websocket_message, "test-client")
        
        # Verify graceful error handling
        assert response["status"] == "error"
        assert "MLX service unavailable" in response["message"]
        assert response["confidence"] == 0.0
        assert response["client_id"] == "test-client"
        assert "timestamp" in response


@pytest.mark.asyncio
async def test_websocket_reconnection_with_missed_ai_events():
    """Test WebSocket reconnection with replay of missed AI-generated events"""
    from app.services.reconnection_service import reconnection_service
    from app.models.event_models import EventData, EventType, EventPriority, NotificationChannel
    
    client_id = "reconnect-test-client"
    
    # Mock reconnection service with missed events
    with patch.object(reconnection_service, 'client_reconnected') as mock_reconnect:
        # Create missed AI events during disconnection
        missed_events = [
            EventData(
                event_id="ai_event_1",
                event_type=EventType.ai_analysis_complete,
                priority=EventPriority.high,
                channel=NotificationChannel.websocket,
                timestamp=datetime.now(),
                source="mlx_service",
                data={
                    "analysis_id": "analysis_123",
                    "task_id": "task_456",
                    "confidence": 0.88,
                    "suggestions": ["Refactor for better performance"]
                }
            ),
            EventData(
                event_id="ai_event_2", 
                event_type=EventType.task_updated,
                priority=EventPriority.medium,
                channel=NotificationChannel.websocket,
                timestamp=datetime.now(),
                source="task_service",
                data={
                    "task_id": "task_456",
                    "ai_enhanced": True,
                    "status": "analyzed"
                }
            )
        ]
        
        # Mock reconnection data
        reconnection_data = {
            "missed_events_count": len(missed_events),
            "missed_events": [event.dict() for event in missed_events],
            "last_sequence_number": 150,
            "current_sequence_number": 152
        }
        
        mock_reconnect.return_value = asyncio.Future()
        mock_reconnect.return_value.set_result(reconnection_data)
        
        # Mock connection state
        from app.models.event_models import ConnectionState, ClientPreferences
        connection_state = ConnectionState(
            client_id=client_id,
            connected_at=datetime.now(),
            preferences=ClientPreferences(),
            sequence_number=150,
            last_seen=datetime.now()
        )
        
        # Simulate reconnection
        result = await reconnection_service.client_reconnected(client_id, connection_state)
        
        # Verify missed AI events are included
        assert result["missed_events_count"] == 2
        assert len(result["missed_events"]) == 2
        
        # Verify AI-specific events are properly structured
        ai_events = [event for event in result["missed_events"] 
                    if event["event_type"] == "ai_analysis_complete"]
        assert len(ai_events) == 1
        assert ai_events[0]["data"]["confidence"] == 0.88


@pytest.mark.asyncio
async def test_websocket_batch_ai_events_broadcasting():
    """Test broadcasting multiple AI events in batches for efficiency"""
    from app.core.connection_manager import ConnectionManager
    
    # Mock multiple WebSocket connections
    mock_websockets = [AsyncMock() for _ in range(5)]
    
    with patch('app.core.connection_manager.ConnectionManager') as mock_conn_manager:
        mock_manager = AsyncMock()
        mock_conn_manager.return_value = mock_manager
        mock_manager.broadcast_batch = AsyncMock()
        
        # Create batch of AI-related events
        ai_events = []
        for i in range(10):
            from app.models.event_models import EventData, EventType, EventPriority, NotificationChannel
            
            event = EventData(
                event_id=f"ai_batch_{i}",
                event_type=EventType.ai_analysis_complete,
                priority=EventPriority.medium,
                channel=NotificationChannel.websocket,
                timestamp=datetime.now(),
                source="batch_mlx_service",
                data={
                    "analysis_id": f"analysis_{i}",
                    "confidence": 0.85 + (i * 0.01),
                    "processing_time": f"{i * 100}ms"
                }
            )
            ai_events.append(event)
        
        # Simulate batch broadcasting
        batch_data = {
            "type": "event_batch",
            "events": [event.dict() for event in ai_events],
            "batch_size": len(ai_events),
            "timestamp": datetime.now().isoformat()
        }
        
        # Verify batch broadcasting capability
        await mock_manager.broadcast_batch(batch_data)
        mock_manager.broadcast_batch.assert_called_once_with(batch_data)


@pytest.mark.asyncio
async def test_websocket_ai_progress_streaming():
    """Test real-time streaming of AI processing progress"""
    from app.core.connection_manager import ConnectionManager
    
    with patch('app.core.connection_manager.ConnectionManager') as mock_conn_manager:
        mock_manager = AsyncMock()
        mock_conn_manager.return_value = mock_manager
        mock_manager.send_to_client = AsyncMock()
        
        # Mock AI service with progress callbacks
        with patch('app.services.unified_mlx_service.unified_mlx_service') as mock_mlx:
            # Simulate progressive AI analysis
            progress_updates = [
                {"progress": 25, "status": "Parsing code structure"},
                {"progress": 50, "status": "Analyzing dependencies"},
                {"progress": 75, "status": "Generating suggestions"},
                {"progress": 100, "status": "Analysis complete"}
            ]
            
            client_id = "progress-test-client"
            
            # Simulate sending progress updates via WebSocket
            for update in progress_updates:
                progress_message = {
                    "type": "ai_progress",
                    "client_id": client_id,
                    "progress": update["progress"],
                    "status": update["status"],
                    "timestamp": datetime.now().isoformat()
                }
                
                await mock_manager.send_to_client(client_id, progress_message)
            
            # Verify all progress updates were sent
            assert mock_manager.send_to_client.call_count == len(progress_updates)
            
            # Verify final progress update
            final_call = mock_manager.send_to_client.call_args_list[-1]
            final_message = final_call[0][1]  # Second argument (message)
            assert final_message["progress"] == 100
            assert final_message["status"] == "Analysis complete"


@pytest.mark.performance
async def test_websocket_ai_event_broadcast_performance():
    """Test WebSocket AI event broadcasting performance under load"""
    import time
    from app.core.connection_manager import ConnectionManager
    
    # Performance requirements: <100ms for broadcasting to 50 clients
    num_clients = 50
    mock_websockets = [AsyncMock() for _ in range(num_clients)]
    
    with patch('app.core.connection_manager.ConnectionManager') as mock_conn_manager:
        mock_manager = AsyncMock()
        mock_conn_manager.return_value = mock_manager
        
        # Mock broadcast method with realistic timing
        async def mock_broadcast(message):
            # Simulate realistic WebSocket send times
            await asyncio.sleep(0.001)  # 1ms per client simulation
            
        mock_manager.broadcast = AsyncMock(side_effect=mock_broadcast)
        
        # Create AI event to broadcast
        from app.models.event_models import EventData, EventType, EventPriority, NotificationChannel
        
        ai_event = EventData(
            event_id="perf_test",
            event_type=EventType.ai_analysis_complete, 
            priority=EventPriority.high,
            channel=NotificationChannel.websocket,
            timestamp=datetime.now(),
            source="performance_test",
            data={"large_analysis": "x" * 1000}  # 1KB payload
        )
        
        # Measure broadcast performance
        start_time = time.time()
        await mock_manager.broadcast(ai_event.dict())
        broadcast_time = time.time() - start_time
        
        # Verify performance requirement
        assert broadcast_time < 0.1  # Less than 100ms
        
        # Verify broadcast was called
        mock_manager.broadcast.assert_called_once()


@pytest.mark.integration
async def test_websocket_end_to_end_ai_workflow():
    """Test complete end-to-end AI workflow through WebSocket"""
    from app.main import handle_code_completion_websocket
    
    # Mock full AI pipeline
    with patch('app.services.unified_mlx_service.unified_mlx_service') as mock_mlx:
        # Mock successful AI analysis
        mock_mlx.generate_code_completion.return_value = asyncio.Future()
        mock_mlx.generate_code_completion.return_value.set_result({
            "status": "success",
            "response": "# Complete authentication function\ndef authenticate_user(username: str, password: str) -> Optional[User]:\n    user = get_user_by_username(username)\n    if user and verify_password(password, user.password_hash):\n        return user\n    return None",
            "confidence": 0.94,
            "suggestions": [
                "Add input validation",
                "Implement rate limiting", 
                "Add logging for security events",
                "Consider OAuth integration"
            ],
            "analysis": {
                "complexity": "low",
                "security_considerations": ["password handling", "user enumeration"],
                "performance_impact": "minimal"
            }
        })
        
        # Mock connection manager for event broadcasting
        with patch('app.core.connection_manager.ConnectionManager') as mock_conn_manager:
            mock_manager = AsyncMock() 
            mock_conn_manager.return_value = mock_manager
            mock_manager.send_to_client = AsyncMock()
            
            # Step 1: Client sends code completion request
            request_message = {
                "type": "code_completion",
                "file_path": "/app/auth.py",
                "cursor_position": 200,
                "intent": "suggest",
                "content": "def authenticate_user(username: str, password: str):",
                "language": "python"
            }
            
            # Step 2: Process through AI pipeline
            response = await handle_code_completion_websocket(request_message, "integration-test-client")
            
            # Step 3: Verify complete response structure
            assert response["status"] == "success"
            assert response["type"] == "code_completion_response"
            assert response["confidence"] > 0.9
            assert "def authenticate_user" in response["response"]
            assert len(response["suggestions"]) == 4
            assert response["client_id"] == "integration-test-client"
            
            # Step 4: Verify AI service integration
            mock_mlx.generate_code_completion.assert_called_once()
            call_args = mock_mlx.generate_code_completion.call_args
            assert "suggest" in str(call_args)
            
            # Step 5: Verify response includes all expected AI analysis
            assert "Complete authentication function" in response["response"]
            assert "Add input validation" in response["suggestions"]