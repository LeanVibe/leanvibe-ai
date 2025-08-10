import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import time

print("🧪 Testing Phi-3 Model Inference")
print("=" * 50)

model_name = "microsoft/Phi-3-mini-4k-instruct"
print(f"📦 Model: {model_name}")

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"🖥️  Device: {device}")

try:
    print("\n1️⃣ Loading tokenizer...")
    start_time = time.time()
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    tokenizer_time = time.time() - start_time
    print(f"   ✅ Tokenizer loaded in {tokenizer_time:.2f}s")
    
    print("\n2️⃣ Loading model...")
    start_time = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device != "cpu" else torch.float32,
        trust_remote_code=True,
        device_map="auto"
    )
    model_time = time.time() - start_time
    print(f"   ✅ Model loaded in {model_time:.2f}s")
    
    print("\n3️⃣ Testing inference...")
    test_prompt = "What is Python? Explain in one sentence."
    
    inputs = tokenizer(test_prompt, return_tensors="pt")
    if device != "cpu":
        inputs = {k: v.to(device) for k, v in inputs.items()}
    
    start_time = time.time()
    with torch.no_grad():
        outputs = model.generate(
            inputs["input_ids"],
            max_new_tokens=50,
            do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id
        )
    
    inference_time = time.time() - start_time
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    generated_text = response[len(test_prompt):].strip()
    
    print(f"   ✅ Inference completed in {inference_time:.2f}s")
    print(f"\n🤖 Model Response:")
    print(f"   Prompt: {test_prompt}")
    print(f"   Generated: {generated_text}")
    
    print(f"\n📊 Model Information:")
    print(f"   Parameters: ~{sum(p.numel() for p in model.parameters()) / 1e6:.1f}M")
    
    print(f"\n⏱️  Performance Summary:")
    print(f"   Tokenizer load: {tokenizer_time:.2f}s")
    print(f"   Model load: {model_time:.2f}s") 
    print(f"   Inference: {inference_time:.2f}s")
    print(f"   Total: {tokenizer_time + model_time + inference_time:.2f}s")
    
    print(f"\n✅ Phi-3 model test PASSED - Real model inference working!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()