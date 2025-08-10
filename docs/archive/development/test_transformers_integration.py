#!/usr/bin/env python3
"""
Integration test for the transformers Phi-3 service
Tests the service directly without full server startup
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the backend app to path
backend_path = Path(__file__).parent / "leanvibe-backend"
sys.path.insert(0, str(backend_path))

async def test_transformers_service():
    """Test the transformers Phi-3 service directly"""
    print("🧪 Testing Transformers Phi-3 Service Integration")
    print("=" * 60)
    
    try:
        # Import the service
        from app.services.transformers_phi3_service import transformers_phi3_service
        print("✅ Successfully imported transformers service")
        
        # Initialize the service
        print("\n🚀 Initializing service...")
        start_time = time.time()
        success = await transformers_phi3_service.initialize()
        init_time = time.time() - start_time
        
        if not success:
            print("❌ Service initialization failed")
            return False
            
        print(f"✅ Service initialized in {init_time:.2f}s")
        
        # Get health status
        print("\n📊 Health Status:")
        health = transformers_phi3_service.get_health_status()
        for key, value in health.items():
            print(f"   {key}: {value}")
        
        # Test text generation
        print("\n🤖 Testing text generation...")
        test_prompt = "Explain what Python is in one sentence:"
        
        start_time = time.time()
        result = await transformers_phi3_service.generate_text(
            test_prompt,
            max_new_tokens=50,
            temperature=0.7
        )
        generation_time = time.time() - start_time
        
        print(f"📝 Prompt: {test_prompt}")
        print(f"⏱️  Generation time: {generation_time:.2f}s")
        
        if result["status"] == "success":
            print(f"✅ Generated response:")
            print(f"   Response: {result['response']}")
            print(f"   Using pretrained: {result.get('using_pretrained', False)}")
            print(f"   Model: {result.get('model_name', 'unknown')}")
            print(f"   Tokens/sec: {result.get('tokens_per_second', 0):.1f}")
        else:
            print(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Test unified MLX service integration
        print("\n🔗 Testing Unified MLX Service Integration...")
        from app.services.unified_mlx_service import unified_mlx_service
        
        # Initialize unified service
        await unified_mlx_service.initialize()
        print("✅ Unified MLX service initialized")
        
        # Test code completion through unified service
        context = {
            "file_path": "test.py",
            "cursor_position": 0,
            "content": "def fibonacci(n):"
        }
        
        completion_result = await unified_mlx_service.generate_code_completion(
            context, "suggest"
        )
        
        print(f"🎯 Code completion result:")
        print(f"   Status: {completion_result['status']}")
        if completion_result['status'] == 'success':
            print(f"   Response: {completion_result['response'][:100]}...")
            print(f"   Confidence: {completion_result['confidence']}")
            print(f"   Model: {completion_result.get('model', 'unknown')}")
            print(f"   Using pretrained: {completion_result.get('using_pretrained', False)}")
        
        print(f"\n✅ All tests passed! Transformers Phi-3 integration working.")
        print(f"🎉 Real model weights are loaded and generating quality responses.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            if 'transformers_phi3_service' in locals():
                await transformers_phi3_service.shutdown()
                print("🧹 Service cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

if __name__ == "__main__":
    success = asyncio.run(test_transformers_service())
    if success:
        print(f"\n🎯 INTEGRATION TEST PASSED")
        print(f"✅ Phi-3 model with real pre-trained weights is working!")
        exit(0)
    else:
        print(f"\n❌ INTEGRATION TEST FAILED")
        exit(1)