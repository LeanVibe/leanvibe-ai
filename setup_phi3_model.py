#!/usr/bin/env python3
"""
Simple script to download and test MLX Phi-3 model
"""

import asyncio
import sys
import os

async def setup_phi3_model():
    """Download and setup the Phi-3 model"""
    
    print("🧠 Setting up MLX Phi-3 Model")
    print("=" * 40)
    
    # Check MLX availability
    try:
        import mlx.core as mx
        print("✅ MLX Core available")
    except ImportError:
        print("❌ MLX not available. Install with: pip install mlx")
        return False
    
    # Check MLX-LM availability
    try:
        from mlx_lm import load, generate
        print("✅ MLX-LM available")
    except ImportError:
        print("❌ MLX-LM not available. Install with: pip install mlx-lm")
        return False
    
    # Download and load the model
    print("\n📥 Downloading Phi-3 model (this may take a few minutes on first run)...")
    try:
        model, tokenizer = load("microsoft/Phi-3-mini-128k-instruct")
        print("✅ Model downloaded and loaded successfully!")
        
        # Test inference
        print("\n🧪 Testing inference...")
        prompt = "def fibonacci(n):"
        response = generate(
            model, 
            tokenizer, 
            prompt, 
            max_tokens=50,
            temp=0.7
        )
        
        print(f"✅ Inference test successful!")
        print(f"   Prompt: {prompt}")
        print(f"   Response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model setup failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_phi3_model())
    
    if success:
        print("\n🎉 Setup Complete!")
        print("\n💡 Next steps:")
        print("   1. The model is now cached locally")
        print("   2. Future loads will be much faster")
        print("   3. You can now use the LeanVibe MLX services")
        print("   4. Test with: python test_phi3_model.py")
    else:
        print("\n❌ Setup failed. Check the error messages above.")