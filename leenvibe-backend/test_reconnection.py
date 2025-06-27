#!/usr/bin/env python3
"""
Simple test script to validate reconnection functionality
"""

import asyncio
import json
from datetime import datetime

# Import the services to test
from app.services.reconnection_service import ReconnectionService, ReconnectionConfig
from app.models.event_models import ConnectionState, ClientPreferences, EventData, EventType, EventPriority, NotificationChannel

async def test_reconnection_flow():
    """Test the complete reconnection flow"""
    print("🧪 Testing Reconnection Service...")
    
    # Create reconnection service with test config
    config = ReconnectionConfig(
        max_retry_attempts=3,
        initial_delay_ms=500,
        heartbeat_interval_ms=10000
    )
    service = ReconnectionService(config)
    
    # Start the service
    await service.start()
    print("✅ Reconnection service started")
    
    # Create test client preferences
    preferences = ClientPreferences(
        client_id="test-client-1",
        enabled_channels=[NotificationChannel.ALL],
        min_priority=EventPriority.MEDIUM,
        max_events_per_second=10,
        enable_batching=True,
        batch_interval_ms=1000
    )
    
    # Create connection state
    connection_state = ConnectionState(
        client_id="test-client-1",
        connected_at=datetime.now(),
        preferences=preferences,
        sequence_number=0,
        last_activity=datetime.now()
    )
    
    # Test 1: Register new client session
    print("\n📝 Test 1: Registering client session...")
    service.register_client_session("test-client-1", connection_state)
    
    session_info = service.get_client_session_info("test-client-1")
    assert session_info is not None, "Session should be registered"
    print(f"✅ Session registered: {session_info['client_id']}")
    
    # Test 2: Simulate missed events
    print("\n📝 Test 2: Adding missed events...")
    test_events = [
        EventData(
            event_id="test-1",
            event_type=EventType.FILE_CHANGED,
            priority=EventPriority.HIGH,
            channel=NotificationChannel.SYSTEM,
            timestamp=datetime.now(),
            source="test",
            data={"file": "test.py", "change": "modified"}
        ),
        EventData(
            event_id="test-2",
            event_type=EventType.AST_ANALYSIS_COMPLETED,
            priority=EventPriority.MEDIUM,
            channel=NotificationChannel.ANALYSIS,
            timestamp=datetime.now(),
            source="test",
            data={"analysis": "completed"}
        )
    ]
    
    for event in test_events:
        service.add_missed_event("test-client-1", event)
    
    session_info = service.get_client_session_info("test-client-1")
    assert session_info["missed_events_count"] == 2, f"Expected 2 missed events, got {session_info['missed_events_count']}"
    print(f"✅ Added {session_info['missed_events_count']} missed events")
    
    # Test 3: Simulate client disconnection
    print("\n📝 Test 3: Simulating client disconnection...")
    service.client_disconnected("test-client-1")
    print("✅ Client marked as disconnected")
    
    # Test 4: Simulate client reconnection
    print("\n📝 Test 4: Simulating client reconnection...")
    reconnection_info = await service.client_reconnected("test-client-1", connection_state)
    
    assert reconnection_info["status"] == "reconnected", "Should return reconnected status"
    assert reconnection_info["missed_events_count"] == 2, "Should return missed events count"
    assert len(reconnection_info["missed_events"]) == 2, "Should return missed events data"
    
    print(f"✅ Reconnection successful:")
    print(f"   - Status: {reconnection_info['status']}")
    print(f"   - Missed events: {reconnection_info['missed_events_count']}")
    print(f"   - Duration: {reconnection_info['disconnection_duration_ms']}ms")
    
    # Test 5: Test heartbeat
    print("\n📝 Test 5: Testing heartbeat...")
    service.update_client_heartbeat("test-client-1")
    session_info = service.get_client_session_info("test-client-1")
    assert session_info["last_heartbeat"] is not None, "Heartbeat should be recorded"
    print("✅ Heartbeat updated")
    
    # Test 6: Test service stats
    print("\n📝 Test 6: Testing service statistics...")
    all_sessions = service.get_all_sessions_info()
    assert all_sessions["total_sessions"] == 1, "Should have 1 session"
    assert "test-client-1" in all_sessions["sessions"], "Should contain test client"
    print(f"✅ Service stats: {all_sessions['total_sessions']} sessions")
    
    # Cleanup
    await service.stop()
    print("\n✅ Reconnection service stopped")
    print("🎉 All reconnection tests passed!")

if __name__ == "__main__":
    asyncio.run(test_reconnection_flow())