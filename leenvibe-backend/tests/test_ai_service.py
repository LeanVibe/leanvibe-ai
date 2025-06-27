"""
Unit tests for AI Service functionality.
"""
import pytest
import asyncio

@pytest.mark.asyncio
async def test_ai_service_initialization(ai_service):
    """Test AI service can be initialized"""
    await ai_service.initialize()
    assert ai_service.is_initialized is True

@pytest.mark.asyncio
async def test_ai_service_commands(initialized_ai_service):
    """Test AI service command processing"""
    # Test status command
    result = await initialized_ai_service.process_command({
        "type": "command",
        "content": "/status"
    })
    assert result["status"] == "success"
    assert "message" in result
    
    # Test help command
    result = await initialized_ai_service.process_command({
        "type": "command", 
        "content": "/help"
    })
    assert result["status"] == "success"
    assert "Available Commands" in result["message"]

@pytest.mark.asyncio
async def test_ai_service_invalid_command(initialized_ai_service):
    """Test AI service handles invalid commands gracefully"""
    result = await initialized_ai_service.process_command({
        "type": "command",
        "content": "/invalid-command"
    })
    assert result["status"] == "error"
    assert "Unknown command" in result["message"]

@pytest.mark.asyncio
async def test_ai_service_natural_language(initialized_ai_service):
    """Test AI service handles natural language messages"""
    result = await initialized_ai_service.process_command({
        "type": "message",
        "content": "Hello, how are you?"
    })
    assert result["status"] == "success"
    assert "message" in result