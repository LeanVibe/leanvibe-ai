#!/usr/bin/env python3
"""
Setup script for enabling real LLM inference with Qwen2.5-Coder-32B
This script configures the environment for testing with real model weights
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_system_requirements() -> Dict[str, Any]:
    """Check if system meets requirements for real model inference"""
    requirements = {
        "memory_gb": 32,
        "disk_space_gb": 50,
        "python_version": (3, 11),
        "mlx_available": False,
        "mlx_lm_available": False
    }
    
    status = {
        "meets_requirements": True,
        "checks": {},
        "warnings": [],
        "errors": []
    }
    
    # Check Python version
    current_python = sys.version_info[:2]
    status["checks"]["python_version"] = current_python >= requirements["python_version"]
    if not status["checks"]["python_version"]:
        status["errors"].append(f"Python {requirements['python_version']} required, found {current_python}")
        status["meets_requirements"] = False
    
    # Check MLX availability
    try:
        import mlx.core as mx
        status["checks"]["mlx_core"] = True
        logger.info("✅ MLX core available")
        
        # Test MLX functionality
        test_array = mx.array([1.0, 2.0, 3.0])
        memory_mb = mx.get_active_memory() / 1024 / 1024
        logger.info(f"✅ MLX core functional, active memory: {memory_mb:.1f}MB")
        
    except ImportError as e:
        status["checks"]["mlx_core"] = False
        status["errors"].append(f"MLX core not available: {e}")
        status["meets_requirements"] = False
    
    # Check MLX-LM availability
    try:
        from mlx_lm import load, generate
        status["checks"]["mlx_lm"] = True
        logger.info("✅ MLX-LM available")
    except ImportError as e:
        status["checks"]["mlx_lm"] = False
        status["warnings"].append(f"MLX-LM not available: {e}")
    
    # Check memory (rough estimate)
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        status["checks"]["memory"] = memory_gb >= requirements["memory_gb"]
        logger.info(f"System memory: {memory_gb:.1f}GB (required: {requirements['memory_gb']}GB)")
        
        if not status["checks"]["memory"]:
            status["warnings"].append(f"Low memory: {memory_gb:.1f}GB (recommended: {requirements['memory_gb']}GB)")
            
    except ImportError:
        status["warnings"].append("psutil not available, cannot check memory")
        status["checks"]["memory"] = None
    
    # Check disk space
    try:
        cache_dir = Path.home() / ".cache" / "leanvibe"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        free_space_gb = os.statvfs(cache_dir).f_bavail * os.statvfs(cache_dir).f_frsize / (1024**3)
        status["checks"]["disk_space"] = free_space_gb >= requirements["disk_space_gb"]
        logger.info(f"Available disk space: {free_space_gb:.1f}GB (required: {requirements['disk_space_gb']}GB)")
        
        if not status["checks"]["disk_space"]:
            status["warnings"].append(f"Low disk space: {free_space_gb:.1f}GB (recommended: {requirements['disk_space_gb']}GB)")
            
    except Exception as e:
        status["warnings"].append(f"Cannot check disk space: {e}")
        status["checks"]["disk_space"] = None
    
    return status


def setup_environment_variables() -> None:
    """Setup environment variables for real inference"""
    logger.info("Setting up environment variables for real inference...")
    
    env_vars = {
        # Model configuration for Qwen2.5-Coder-32B
        "LEANVIBE_MODEL_NAME": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "LEANVIBE_FALLBACK_MODEL": "microsoft/Phi-3-mini-128k-instruct",
        "LEANVIBE_DEPLOYMENT_MODE": "direct",  # Force direct MLX inference
        "LEANVIBE_MLX_STRATEGY": "production",  # Use production strategy
        
        # Real inference settings
        "LEANVIBE_USE_PRETRAINED_WEIGHTS": "true",
        "LEANVIBE_MODEL_CACHE_SIZE_GB": "25.0",
        "LEANVIBE_QUANTIZATION": "4bit",
        "LEANVIBE_ENABLE_MODEL_CACHING": "true",
        "LEANVIBE_CONTEXT_LENGTH": "32768",
        
        # Performance optimization
        "LEANVIBE_MAX_TOKENS": "1024",
        "LEANVIBE_TEMPERATURE": "0.7",
        "LEANVIBE_CACHE_TTL": "3600",
        
        # Debug and logging
        "LEANVIBE_DEBUG_MODE": "false",  # Disable for performance
        "LEANVIBE_DEVELOPMENT_MODE": "false",
        
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


def create_env_file() -> None:
    """Create .env file for persistent configuration"""
    env_file_path = Path.cwd() / ".env.real_inference"
    
    env_content = """# LeanVibe Real Inference Configuration
# Source this file: source .env.real_inference

# Model configuration for Qwen2.5-Coder-32B
export LEANVIBE_MODEL_NAME="Qwen/Qwen2.5-Coder-32B-Instruct"
export LEANVIBE_FALLBACK_MODEL="microsoft/Phi-3-mini-128k-instruct"
export LEANVIBE_DEPLOYMENT_MODE="direct"
export LEANVIBE_MLX_STRATEGY="production"

# Real inference settings
export LEANVIBE_USE_PRETRAINED_WEIGHTS="true"
export LEANVIBE_MODEL_CACHE_SIZE_GB="25.0"
export LEANVIBE_QUANTIZATION="4bit"
export LEANVIBE_ENABLE_MODEL_CACHING="true"
export LEANVIBE_CONTEXT_LENGTH="32768"

# Performance settings
export LEANVIBE_MAX_TOKENS="1024"
export LEANVIBE_TEMPERATURE="0.7"
export LEANVIBE_CACHE_TTL="3600"

# Debug settings (optimized for performance)
export LEANVIBE_DEBUG_MODE="false"
export LEANVIBE_DEVELOPMENT_MODE="false"

# Directories
export LEANVIBE_CACHE_DIR="$HOME/.cache/leanvibe"
export LEANVIBE_CONFIG_DIR="$HOME/.config/leanvibe" 
export LEANVIBE_LOG_DIR="$HOME/.local/share/leanvibe/logs"

echo "✅ LeanVibe Real Inference environment configured"
echo "Model: Qwen2.5-Coder-32B-Instruct (32B parameters, 32k context)"
echo "Mode: Direct MLX inference with 4bit quantization"
echo "Cache: 25GB model cache enabled"
"""
    
    with open(env_file_path, 'w') as f:
        f.write(env_content)
    
    logger.info(f"Created environment file: {env_file_path}")
    logger.info("To use: source .env.real_inference")


def test_configuration() -> bool:
    """Test the configuration with real inference services"""
    logger.info("Testing configuration with backend services...")
    
    try:
        # Import and test configuration
        sys.path.append(str(Path(__file__).parent / "leanvibe-backend"))
        from app.config.unified_config import get_config, create_qwen_production_config
        
        # Test production configuration
        config = create_qwen_production_config()
        logger.info(f"✅ Configuration created: {config.model.model_name}")
        
        # Validate configuration
        from app.config.unified_config import config_service
        validation = config_service.validate_config()
        
        if validation["valid"]:
            logger.info("✅ Configuration validation passed")
        else:
            logger.warning(f"Configuration validation warnings: {validation['warnings']}")
            logger.error(f"Configuration validation errors: {validation['errors']}")
        
        # Test memory requirements
        if validation.get("model_requirements"):
            reqs = validation["model_requirements"]
            logger.info(f"Memory requirements: {reqs['total_estimated_gb']:.1f}GB total")
            logger.info(f"Recommended system memory: {reqs['recommended_system_memory_gb']:.1f}GB")
        
        # Test MLX service initialization
        try:
            from app.services.production_model_service import ProductionModelService
            
            # Create service with real inference config
            service = ProductionModelService(config.model)
            logger.info("✅ ProductionModelService created")
            
            # Note: Don't actually initialize here as it would download the model
            logger.info("⚠️  Model initialization skipped (would download 25GB+ model)")
            
            return True
            
        except Exception as e:
            logger.error(f"Service creation failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Configuration test failed: {e}")
        return False


def print_usage_instructions():
    """Print instructions for using real inference"""
    instructions = """
🚀 Real Inference Setup Complete!

To use real Qwen2.5-Coder-32B inference:

1. Load environment:
   source .env.real_inference

2. Start backend with real inference:
   cd leanvibe-backend
   python -m app.main

3. Test inference endpoint:
   curl -X POST http://localhost:8000/api/v1/ai/chat \\
     -H "Content-Type: application/json" \\
     -d '{"message": "Write a Python function to calculate fibonacci"}'

4. Monitor logs for detailed inference debugging:
   tail -f ~/.local/share/leanvibe/logs/leanvibe.log

Model Configuration:
- Model: Qwen2.5-Coder-32B-Instruct (32B parameters)
- Context: 32,768 tokens
- Quantization: 4-bit (memory optimized)
- Cache: 25GB model cache
- Strategy: Direct MLX inference

Memory Requirements:
- Model: ~25GB
- Inference overhead: ~7.5GB  
- Total: ~32.5GB system memory recommended

⚠️  First run will download the model (~25GB)
⚠️  Ensure stable internet connection for initial download
⚠️  Model will be cached locally after first download

Debug Commands:
- Check config: python -c "from app.config.unified_config import *; print(get_real_inference_config())"
- Test MLX: python -c "import mlx.core as mx; print(f'MLX memory: {mx.get_active_memory()/1024/1024:.1f}MB')"
- Validate setup: python setup_real_inference.py --test
"""
    print(instructions)


def main():
    """Main setup function"""
    logger.info("🚀 Setting up LeanVibe for real Qwen2.5-Coder-32B inference...")
    
    # Check system requirements
    logger.info("Checking system requirements...")
    requirements_status = check_system_requirements()
    
    if not requirements_status["meets_requirements"]:
        logger.error("❌ System requirements not met:")
        for error in requirements_status["errors"]:
            logger.error(f"  - {error}")
        logger.warning("Warnings:")
        for warning in requirements_status["warnings"]:
            logger.warning(f"  - {warning}")
        
        logger.error("Please address the errors before proceeding.")
        return False
    
    if requirements_status["warnings"]:
        logger.warning("Warnings detected:")
        for warning in requirements_status["warnings"]:
            logger.warning(f"  - {warning}")
    
    # Setup environment
    setup_environment_variables()
    
    # Create persistent configuration
    create_env_file()
    
    # Test configuration
    if "--test" in sys.argv:
        logger.info("Testing configuration...")
        if test_configuration():
            logger.info("✅ Configuration test passed")
        else:
            logger.error("❌ Configuration test failed")
            return False
    
    # Print usage instructions
    print_usage_instructions()
    
    logger.info("✅ Real inference setup completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)