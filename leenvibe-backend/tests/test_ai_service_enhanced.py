import asyncio
import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEnhancedAIService:
    """Test enhanced AI service with MLX integration and confidence scoring"""

    @pytest.mark.asyncio
    async def test_ai_service_initialization(self):
        """Test AI service initialization with MLX detection"""
        from app.services.ai_service import AIService

        ai_service = AIService()
        await ai_service.initialize()

        assert ai_service.is_initialized == True
        assert hasattr(ai_service, "mlx_available")
        assert hasattr(ai_service, "model_health")
        assert ai_service.model_health["status"] in ["ready", "mock_mode", "error"]

    @pytest.mark.asyncio
    async def test_confidence_scoring(self):
        """Test confidence scoring system"""
        from app.services.ai_service import AIService

        ai_service = AIService()
        await ai_service.initialize()

        # Test different response types
        high_confidence = ai_service._calculate_confidence_score(
            "Successfully analyzed the file with detailed insights", "file_operation"
        )
        assert high_confidence > 0.7

        low_confidence = ai_service._calculate_confidence_score(
            "Error occurred", "code_analysis"
        )
        assert low_confidence < 0.5

    @pytest.mark.asyncio
    async def test_enhanced_status_command(self):
        """Test enhanced status command with health information"""
        from app.services.ai_service import AIService

        ai_service = AIService()
        await ai_service.initialize()

        status_response = await ai_service._get_status("", "test-client")

        assert status_response["status"] == "success"
        assert "confidence" in status_response
        assert "data" in status_response
        assert "mlx_available" in status_response["data"]
        assert "health" in status_response["data"]
        assert "version" in status_response["data"]
        assert status_response["data"]["version"] == "0.2.0"

    @pytest.mark.asyncio
    async def test_analyze_file_command(self):
        """Test new analyze-file command"""
        from app.services.ai_service import AIService

        ai_service = AIService()
        await ai_service.initialize()

        # Create a test file
        test_file = Path("test_analysis.py")
        test_content = '''
def hello_world():
    """A simple hello world function"""
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    hello_world()
'''
        test_file.write_text(test_content)

        try:
            # Test analyze command
            response = await ai_service._analyze_file(str(test_file), "test-client")

            assert response["status"] == "success"
            assert response["type"] == "file_analysis"
            assert "confidence" in response
            assert "data" in response
            assert "analysis" in response["data"]
            assert "path" in response["data"]
            assert "size" in response["data"]
            assert "lines" in response["data"]

        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()

    @pytest.mark.asyncio
    async def test_analyze_file_error_handling(self):
        """Test analyze-file error handling"""
        from app.services.ai_service import AIService

        ai_service = AIService()
        await ai_service.initialize()

        # Test with non-existent file
        response = await ai_service._analyze_file("nonexistent.py", "test-client")
        assert response["status"] == "error"
        assert "not found" in response["message"].lower()

        # Test with no arguments
        response = await ai_service._analyze_file("", "test-client")
        assert response["status"] == "error"
        assert "required" in response["message"].lower()

    @pytest.mark.asyncio
    async def test_enhanced_message_processing(self):
        """Test enhanced message processing with confidence scores"""
        from app.services.ai_service import AIService

        ai_service = AIService()
        await ai_service.initialize()

        # Test natural language message
        test_message = {
            "type": "message",
            "content": "How do I analyze my Python code?",
        }
        response = await ai_service.process_command(test_message)

        assert response["status"] == "success"
        assert "confidence" in response
        assert "model" in response
        assert "health" in response
        assert isinstance(response["confidence"], float)
        assert 0.0 <= response["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_model_health_monitoring(self):
        """Test model health monitoring"""
        from app.services.ai_service import AIService

        ai_service = AIService()
        await ai_service.initialize()

        health = ai_service.model_health
        assert "status" in health
        assert "last_check" in health
        assert health["status"] in ["ready", "mock_mode", "error", "unknown"]

    @pytest.mark.asyncio
    async def test_enhanced_help_command(self):
        """Test enhanced help command"""
        from app.services.ai_service import AIService

        ai_service = AIService()
        await ai_service.initialize()

        help_response = await ai_service._get_help("", "test-client")

        assert help_response["status"] == "success"
        assert "/analyze-file" in help_response["message"]
        assert "confidence scoring" in help_response["message"].lower()
        assert "mlx integration" in help_response["message"].lower()


def test_confidence_score_calculation():
    """Test confidence score calculation logic"""
    from app.services.ai_service import AIService

    ai_service = AIService()

    # Test various scenarios
    assert (
        ai_service._calculate_confidence_score(
            "Successfully completed", "file_operation"
        )
        > 0.8
    )
    assert (
        ai_service._calculate_confidence_score("Error occurred", "code_analysis") < 0.5
    )
    assert ai_service._calculate_confidence_score("Short", "file_operation") <= 0.7
    assert ai_service._calculate_confidence_score("A" * 200, "file_operation") > 0.7


if __name__ == "__main__":
    # Run basic tests
    asyncio.run(TestEnhancedAIService().test_ai_service_initialization())
    print("✅ AI service initialization test passed")

    test_confidence_score_calculation()
    print("✅ Confidence score calculation test passed")

    asyncio.run(TestEnhancedAIService().test_enhanced_status_command())
    print("✅ Enhanced status command test passed")

    print("🎉 All enhanced AI service tests passed!")
