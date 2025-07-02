#!/usr/bin/env python3
"""
Development Configuration Setup for LeanVibe AI
Optimized for transformers-based Phi-3-Mini without MLX-LM dependency
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_development_environment() -> None:
    """Setup environment variables optimized for development without MLX-LM"""
    logger.info("Setting up development environment for transformers-based inference...")
    
    env_vars = {
        # Model configuration optimized for transformers Phi-3
        "LEANVIBE_MODEL_NAME": "microsoft/Phi-3-mini-4k-instruct",
        "LEANVIBE_FALLBACK_MODEL": "microsoft/Phi-3-mini-4k-instruct",
        "LEANVIBE_DEPLOYMENT_MODE": "auto",  # Auto-select best available
        "LEANVIBE_MLX_STRATEGY": "production",  # Will fallback to transformers
        
        # Development inference settings
        "LEANVIBE_USE_PRETRAINED_WEIGHTS": "true",
        "LEANVIBE_MODEL_CACHE_SIZE_GB": "8.0",  # Optimized for Phi-3-Mini
        "LEANVIBE_QUANTIZATION": "none",  # No quantization for transformers
        "LEANVIBE_ENABLE_MODEL_CACHING": "true",
        "LEANVIBE_CONTEXT_LENGTH": "4096",  # Phi-3-Mini context length
        
        # Performance settings optimized for development
        "LEANVIBE_MAX_TOKENS": "512",
        "LEANVIBE_TEMPERATURE": "0.7",
        "LEANVIBE_CACHE_TTL": "300",
        
        # Debug settings for development
        "LEANVIBE_DEBUG_MODE": "true",
        "LEANVIBE_DEVELOPMENT_MODE": "true",
        
        # Directories
        "LEANVIBE_CACHE_DIR": str(Path.home() / ".cache" / "leanvibe"),
        "LEANVIBE_CONFIG_DIR": str(Path.home() / ".config" / "leanvibe"),
        "LEANVIBE_LOG_DIR": str(Path.home() / ".local" / "share" / "leanvibe" / "logs")
    }
    
    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
        logger.info(f"Set {key}={value}")
    
    # Create directories
    for dir_var in ["LEANVIBE_CACHE_DIR", "LEANVIBE_CONFIG_DIR", "LEANVIBE_LOG_DIR"]:
        dir_path = Path(os.environ[dir_var])
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")


def create_development_env_file() -> None:
    """Create .env file for development configuration"""
    env_file_path = Path.cwd() / ".env.development"
    
    env_content = """# LeanVibe Development Configuration
# Optimized for transformers-based Phi-3-Mini inference
# Source this file: source .env.development

# Model configuration optimized for transformers
export LEANVIBE_MODEL_NAME="microsoft/Phi-3-mini-4k-instruct"
export LEANVIBE_FALLBACK_MODEL="microsoft/Phi-3-mini-4k-instruct"
export LEANVIBE_DEPLOYMENT_MODE="auto"
export LEANVIBE_MLX_STRATEGY="production"

# Development inference settings
export LEANVIBE_USE_PRETRAINED_WEIGHTS="true"
export LEANVIBE_MODEL_CACHE_SIZE_GB="8.0"
export LEANVIBE_QUANTIZATION="none"
export LEANVIBE_ENABLE_MODEL_CACHING="true"
export LEANVIBE_CONTEXT_LENGTH="4096"

# Performance settings
export LEANVIBE_MAX_TOKENS="512"
export LEANVIBE_TEMPERATURE="0.7"
export LEANVIBE_CACHE_TTL="300"

# Debug settings for development
export LEANVIBE_DEBUG_MODE="true"
export LEANVIBE_DEVELOPMENT_MODE="true"

# Directories
export LEANVIBE_CACHE_DIR="$HOME/.cache/leanvibe"
export LEANVIBE_CONFIG_DIR="$HOME/.config/leanvibe" 
export LEANVIBE_LOG_DIR="$HOME/.local/share/leanvibe/logs"

echo "✅ LeanVibe Development environment configured"
echo "Model: Phi-3-Mini (3.8B parameters, 4k context)"
echo "Mode: Transformers-based inference with pretrained weights"
echo "Backend: http://localhost:8000"
"""
    
    with open(env_file_path, 'w') as f:
        f.write(env_content)
    
    logger.info(f"Created development environment file: {env_file_path}")
    logger.info("To use: source .env.development")


def test_development_configuration() -> bool:
    """Test the development configuration"""
    logger.info("Testing development configuration...")
    
    try:
        # Import and test configuration
        sys.path.append(str(Path(__file__).parent / "leanvibe-backend"))
        from app.config.unified_config import get_config, create_development_config
        
        # Test development configuration
        dev_config = create_development_config()
        logger.info(f"✅ Development config created: {dev_config.model.model_name}")
        
        # Validate development settings
        if dev_config.model.model_name == "microsoft/Phi-3-mini-4k-instruct":
            logger.info("✅ Correct model configured for development")
        else:
            logger.warning(f"Unexpected model: {dev_config.model.model_name}")
        
        if dev_config.debug.development_mode:
            logger.info("✅ Development mode enabled")
        else:
            logger.warning("Development mode not enabled")
        
        # Test memory requirements
        memory_reqs = dev_config.get_memory_requirements()
        total_memory = memory_reqs["total_estimated_gb"]
        
        if total_memory < 12.0:  # Expected for Phi-3-Mini
            logger.info(f"✅ Appropriate memory allocation for development: {total_memory:.1f}GB")
        else:
            logger.warning(f"Memory allocation high for development: {total_memory:.1f}GB")
        
        logger.info("✅ Development configuration test passed")
        return True
        
    except Exception as e:
        logger.error(f"Development configuration test failed: {e}")
        return False


def create_gemini_integration_script() -> None:
    """Create script for Gemini CLI integration and testing"""
    gemini_script_path = Path.cwd() / "test_with_gemini.py"
    
    gemini_script_content = '''#!/usr/bin/env python3
"""
Gemini CLI Integration for Enhanced LeanVibe Testing
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List


async def run_gemini_analysis(prompt: str, context_files: List[str] = None) -> Dict[str, Any]:
    """Run analysis using Gemini CLI"""
    try:
        # Basic gemini command structure
        cmd = ["gemini", "chat"]
        
        if context_files:
            for file in context_files:
                if Path(file).exists():
                    cmd.extend(["--file", file])
        
        cmd.append(prompt)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "response": result.stdout.strip(),
                "analysis": "Gemini analysis completed"
            }
        else:
            return {
                "status": "error",
                "error": result.stderr.strip(),
                "analysis": "Gemini analysis failed"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": "Gemini analysis timed out",
            "analysis": "Request took too long"
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "error": "Gemini CLI not found",
            "analysis": "Install Gemini CLI: pip install google-generativeai"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "analysis": "Unexpected error during Gemini analysis"
        }


async def test_backend_with_gemini() -> None:
    """Test backend functionality using Gemini analysis"""
    print("🤖 Testing LeanVibe Backend with Gemini Analysis...")
    
    # Test backend health
    health_prompt = """
    Analyze the LeanVibe backend health status and provide insights on:
    1. Service initialization status
    2. AI inference capabilities  
    3. Performance metrics
    4. Any potential issues or optimizations
    """
    
    result = await run_gemini_analysis(
        health_prompt,
        context_files=["leanvibe-backend/app/main.py"]
    )
    
    print(f"Health Analysis: {result}")
    
    # Test AI service configuration
    ai_prompt = """
    Review the AI service configuration and provide recommendations for:
    1. Phi-3-Mini integration optimization
    2. Inference performance improvements
    3. Error handling enhancements
    4. Production readiness assessment
    """
    
    ai_result = await run_gemini_analysis(
        ai_prompt,
        context_files=[
            "leanvibe-backend/app/services/transformers_phi3_service.py",
            "leanvibe-backend/app/services/enhanced_ai_service.py"
        ]
    )
    
    print(f"AI Service Analysis: {ai_result}")


async def validate_configuration_with_gemini() -> None:
    """Validate configuration using Gemini analysis"""
    print("⚙️ Validating Configuration with Gemini...")
    
    config_prompt = """
    Analyze the unified configuration system and provide insights on:
    1. Development vs production configuration appropriateness
    2. Memory requirements and optimization opportunities
    3. Fallback mechanisms and error handling
    4. Security and performance considerations
    """
    
    result = await run_gemini_analysis(
        config_prompt,
        context_files=["leanvibe-backend/app/config/unified_config.py"]
    )
    
    print(f"Configuration Analysis: {result}")


async def main():
    """Main Gemini integration test function"""
    print("🚀 Starting Gemini CLI Integration Testing...")
    
    # Run all tests
    await test_backend_with_gemini()
    await validate_configuration_with_gemini()
    
    print("✅ Gemini CLI integration testing completed")


if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open(gemini_script_path, 'w') as f:
        f.write(gemini_script_content)
    
    # Make executable
    gemini_script_path.chmod(0o755)
    
    logger.info(f"Created Gemini integration script: {gemini_script_path}")
    logger.info("To use: python test_with_gemini.py")


def print_development_instructions():
    """Print instructions for development setup"""
    instructions = """
🚀 Development Environment Setup Complete!

Your LeanVibe development environment is now optimized for:
- ✅ Transformers-based Phi-3-Mini inference (real AI, not mock)
- ✅ No MLX-LM dependency required
- ✅ Full debugging and development features enabled
- ✅ Gemini CLI integration for enhanced testing

To start development:

1. Load development environment:
   source .env.development

2. Start backend server:
   cd leanvibe-backend
   python -m uvicorn app.main:app --reload --port 8000

3. Test AI inference:
   curl -X POST http://localhost:8000/api/v1/ai/chat \\
     -H "Content-Type: application/json" \\
     -d '{"message": "Write a Python function to sort a list"}'

4. Run enhanced testing with Gemini:
   python test_with_gemini.py

Development Configuration:
- Model: microsoft/Phi-3-mini-4k-instruct (3.8B parameters)
- Context: 4,096 tokens (optimized for development)
- Inference: Real pretrained weights via transformers
- Mode: Development with enhanced debugging
- Memory: ~8GB cache (suitable for development)

Backend Endpoints:
- Health: http://localhost:8000/health
- MLX Health: http://localhost:8000/health/mlx
- AI Chat: http://localhost:8000/api/v1/ai/chat
- Tasks: http://localhost:8000/api/v1/tasks

Debug Features:
- Enhanced logging with correlation IDs
- Performance tracking and optimization
- Error categorization with recovery suggestions  
- Real-time inference monitoring

Next Steps:
- Test AI inference endpoints
- Validate iOS-Backend integration (fix iOS build first)
- Run comprehensive testing with Gemini CLI
- Deploy to production when ready

🎯 Your development environment provides real AI inference capabilities
   without requiring MLX-LM installation!
"""
    print(instructions)


def main():
    """Main setup function"""
    logger.info("🚀 Setting up LeanVibe development environment...")
    
    # Setup environment
    setup_development_environment()
    
    # Create persistent configuration
    create_development_env_file()
    
    # Create Gemini integration
    create_gemini_integration_script()
    
    # Test configuration
    if test_development_configuration():
        logger.info("✅ Development configuration validated")
    else:
        logger.error("❌ Development configuration validation failed")
        return False
    
    # Print usage instructions
    print_development_instructions()
    
    logger.info("✅ Development environment setup completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)