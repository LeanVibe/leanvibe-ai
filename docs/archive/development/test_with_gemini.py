#!/usr/bin/env python3
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
        # Correct gemini command structure based on help output
        cmd = ["gemini", "--prompt", prompt]
        
        # Add files to context if available
        if context_files:
            for file in context_files:
                if Path(file).exists():
                    # Read file content and include in prompt
                    with open(file, 'r') as f:
                        file_content = f.read()[:2000]  # Limit content size
                    prompt += f"\n\nFile: {file}\n```\n{file_content}\n```"
        
        # Update command with enhanced prompt
        cmd = ["gemini", "--prompt", prompt]
        
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
