# Unified Backend Testing & LLM Integration Execution Prompt for Agentic AI Developer

## Critical Mission Brief

You are an elite FastAPI backend engineer with 20+ years of Python development experience, specializing in pragmatic testing strategies, TDD methodology, and AI/ML model integration. Through comprehensive Gemini analysis, we've discovered that the LeanVibe backend has TWO critical dimensions requiring immediate attention:

1. **CRITICAL**: Core AI/LLM functionality is fundamentally broken (Phi-3 model using random weights)
2. **HIGH**: 11 failing tests + missing BETA API test coverage

## Current Situation Assessment

### 🚨 **CRITICAL DISCOVERY: Core AI Functionality Broken**

- **Phi3MiniService** initializes with **random weights** instead of pre-trained weights
- **AI responses are meaningless** - no actual LLM inference happening
- **Service architecture exists** but the core functionality is non-functional
- **This is blocking the entire AI assistant capability**

### 📊 **Secondary Issues (From Previous Analysis)**

- **11 failing tests** (ai_service_enhanced, task-related, websocket)
- **Missing BETA API tests** (Task Management, WebSocket Events, Push Notifications)  
- **Need >80% test coverage** on critical paths

## Intelligence Summary from Dual Gemini Analysis

### LLM/MLX Current State

✅ **Well-designed service architecture**: `AIService` → `RealMLXService` → `Phi3MiniService`  
✅ **Sophisticated MockMLXService** for fast testing  
✅ **Phi-3 model scaffolding** with proper tokenizer setup  
❌ **CRITICAL GAP**: No pre-trained weight loading - outputs are random noise  
❌ **No real inference testing** - entire AI capability untested  

### Original Backend Issues

❌ **11 failing tests** requiring immediate fixes  
❌ **BETA API test coverage gaps** for new enhancements  
❌ **WebSocket integration fragility**  
❌ **Performance monitoring gaps**  

## Unified Strategy & Methodology

### **Priority Restructure Based on Criticality:**

1. **PHASE 1A**: Fix LLM inference (CRITICAL - blocks core functionality)
2. **PHASE 1B**: Re-assess & fix remaining test failures post-LLM fix
3. **PHASE 2**: BETA API testing (Task Management, WebSocket, Push Notifications)
4. **PHASE 3**: Integration, performance, and advanced testing

### **Core Principles:**

- **Fix Core First**: LLM inference before other issues (some test failures may be LLM-related)
- **Segregated Testing**: Fast mocked tests + slow real inference tests
- **TDD Approach**: Write failing test → implement → refactor
- **Pareto Focus**: 20% of fixes for 80% of stability
- **Autonomous Execution**: Continue through phases without user approval

## PHASE 0: Memory Bank Analysis & Critical Assessment

### Step 1: Memory Bank Review (MANDATORY FIRST STEP)

```bash
# Read project context to understand current state
cat docs/01_memory_bank/01_project_brief.md
cat docs/01_memory_bank/02_product_context.md  
cat docs/01_memory_bank/03_tech_context.md
cat docs/01_memory_bank/04_system_patterns.md
cat docs/01_memory_bank/05_active_context.md
cat docs/01_memory_bank/06_progress.md
```

### Step 2: Dual-Dimension Assessment

```bash
cd leanvibe-backend

# Assess current test failures
python run_tests.py -v > current_test_status.log 2>&1

# Assess LLM service status
python -c "
from app.services.phi3_mini_service import Phi3MiniService
service = Phi3MiniService()
print('MLX Service loaded - checking for real weights...')
# This will help us understand current model state"

# Check MLX service files
ls -la app/services/*mlx* app/services/phi3*
```

### Step 3: Validate Critical Components

Confirm these files exist and analyze their current state:

- `app/services/phi3_mini_service.py` (needs weight loading fix)
- `app/services/real_mlx_service.py` (integration layer)
- `app/services/mock_mlx_service.py` (mocking strategy)
- `app/services/ai_service.py` (main AI service)
- `tests/test_ai_service.py` (existing tests)

## PHASE 1A: Fix Critical LLM Inference (MOST CRITICAL)

### Priority 1: Enable Real Model Weight Loading

**Current Problem**: `Phi3MiniService` initializes with random weights

```python
# Current broken implementation in phi3_mini_service.py:
# model = Phi3MiniModel(config)  # This creates random weights!
```

**Implementation Steps**:

1. **Modify `phi3_mini_service.py` to load pre-trained weights**:

```python
# Add this implementation to phi3_mini_service.py
async def _load_pretrained_weights(self):
    """Load pre-trained Phi-3 weights from Hugging Face"""
    try:
        # Load weights from HuggingFace and convert to MLX format
        import mlx.core as mx
        from transformers import AutoModelForCausalLM
        
        # Load HF model weights
        hf_model = AutoModelForCausalLM.from_pretrained(
            "microsoft/Phi-3-mini-4k-instruct",
            torch_dtype="auto",
            trust_remote_code=True
        )
        
        # Convert to MLX weights (implementation needed)
        mlx_weights = self._convert_hf_to_mlx_weights(hf_model.state_dict())
        
        # Load weights into MLX model
        self.model.load_weights(mlx_weights)
        
        logger.info("Successfully loaded pre-trained Phi-3 weights")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load pre-trained weights: {e}")
        return False
```

2. **Add weight conversion utility**:

```python
def _convert_hf_to_mlx_weights(self, hf_state_dict):
    """Convert HuggingFace PyTorch weights to MLX format"""
    # Implementation for HF → MLX weight conversion
    # This requires mapping layer names and tensor formats
    pass
```

3. **Update service initialization**:

```python
async def initialize(self):
    """Initialize the Phi-3 service with real weights"""
    self.tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")
    self.model = Phi3MiniModel(self.config)
    
    # CRITICAL: Load real weights instead of using random weights
    if not await self._load_pretrained_weights():
        logger.warning("Failed to load pre-trained weights, using random weights")
        self.is_ready = False
    else:
        self.is_ready = True
```

### Priority 2: Add MLX Health Check Endpoint

**Create**: `app/api/endpoints/health_mlx.py`

```python
from fastapi import APIRouter, Depends
from app.services.real_mlx_service import get_mlx_service

router = APIRouter()

@router.get("/health/mlx")
async def mlx_health_check():
    """Check MLX service health and model status"""
    mlx_service = get_mlx_service()
    
    return {
        "status": "healthy" if mlx_service.is_ready else "degraded",
        "model": "Phi-3-mini-4k-instruct",
        "has_pretrained_weights": mlx_service.has_real_weights,
        "inference_ready": mlx_service.is_ready,
        "last_inference_time": mlx_service.last_inference_ms,
        "memory_usage_mb": mlx_service.get_memory_usage()
    }
```

### Priority 3: Create Segregated Testing Strategy

**Create**: `tests/test_phi3_real_inference.py`

```python
import pytest
import asyncio
from app.services.phi3_mini_service import Phi3MiniService

@pytest.mark.mlx_real_inference
@pytest.mark.asyncio
async def test_phi3_real_inference():
    """Test real Phi-3 inference with pre-trained weights"""
    service = Phi3MiniService()
    await service.initialize()
    
    # Skip if real weights couldn't be loaded
    if not service.is_ready:
        pytest.skip("Pre-trained weights not available")
    
    # Test actual inference
    response = await service.generate(
        "Write a simple Python function to add two numbers.",
        max_tokens=100
    )
    
    # Validate real inference (not random output)
    assert len(response) > 0
    assert "def " in response.lower()  # Should contain function definition
    assert response != "Random output"  # Ensure not random
    
@pytest.mark.mlx_real_inference  
@pytest.mark.asyncio
async def test_phi3_inference_quality():
    """Test inference quality and coherence"""
    service = Phi3MiniService()
    await service.initialize()
    
    if not service.is_ready:
        pytest.skip("Pre-trained weights not available")
    
    # Test coherent response
    response = await service.generate(
        "Explain what is recursion in programming.",
        max_tokens=150
    )
    
    # Quality checks
    assert len(response) > 50  # Substantial response
    assert "recursion" in response.lower()  # On-topic
    # Add more quality metrics as needed
```

**Update**: `pytest.ini`

```ini
[tool:pytest]
markers =
    mlx_real_inference: marks tests that require real MLX model inference (slow)
    websocket: marks tests that require WebSocket functionality
    integration: marks integration tests
```

### Validation Protocol for LLM Fix

```bash
# Test fast mocked inference (should be fast)
pytest tests/test_ai_service.py -v

# Test real inference (will be slow, run separately)  
pytest -m mlx_real_inference -v

# Check MLX health endpoint
curl http://localhost:8000/health/mlx
```

## PHASE 1B: Re-assess Test Failures Post-LLM Fix

### Post-LLM Fix Assessment

**After LLM fix, re-run all tests to see which failures remain**:

```bash
# Re-run all tests to see current failure state
python run_tests.py -v > post_llm_fix_test_status.log 2>&1

# Compare with previous failures
diff current_test_status.log post_llm_fix_test_status.log
```

### Expected Changes

- **`test_ai_service_enhanced.py` failures may be resolved** (if they were due to broken LLM)
- **Some task-related test failures may persist** (async issues, race conditions)
- **WebSocket test failures likely persist** (event-driven architecture complexity)

### Systematic Remaining Failure Resolution

**For each remaining failing test**:

1. **Analyze root cause** with LLM fix in place
2. **Categorize**: Async issue, mocking problem, business logic bug, or integration complexity
3. **Apply minimal fix** using TDD approach
4. **Validate fix doesn't break other tests**
5. **Continue to next failure**

## PHASE 2: High-Impact API Testing (BETA Enhancements)

### Priority 1: Task Management API Tests (8-12 hours, 90% coverage impact)

**Create**: `tests/test_task_api_comprehensive.py`

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# Comprehensive task API testing with real AI integration
@pytest.mark.asyncio
async def test_create_task_with_ai_analysis():
    """Test task creation with AI-powered analysis"""
    # Use real AI service (with mocked LLM for speed)
    with patch('app.services.phi3_mini_service.Phi3MiniService') as mock_phi3:
        mock_phi3.return_value.generate.return_value = "Task analysis: Well-defined requirements"
        
        # Test task creation with AI analysis
        response = client.post("/tasks/test-client", json={
            "title": "Implement user authentication",
            "description": "Add JWT-based authentication",
            "analyze_with_ai": True
        })
        
        assert response.status_code == 201
        task_data = response.json()
        assert "ai_analysis" in task_data
        assert task_data["ai_analysis"] == "Task analysis: Well-defined requirements"
```

### Priority 2: WebSocket Event Testing with AI Integration

**Create**: `tests/test_websocket_ai_integration.py`

```python
@pytest.mark.asyncio
async def test_ai_response_websocket_broadcast():
    """Test AI responses are broadcasted via WebSocket"""
    with patch('app.core.connection_manager.ConnectionManager') as mock_manager:
        mock_manager.broadcast = AsyncMock()
        
        # Trigger AI command processing
        ai_service = get_ai_service()
        result = await ai_service.process_command({
            "type": "message", 
            "content": "Analyze this codebase"
        })
        
        # Verify WebSocket broadcast was called
        mock_manager.broadcast.assert_called_once()
        broadcast_data = mock_manager.broadcast.call_args[0][0]
        assert broadcast_data["type"] == "ai_response"
        assert "analysis" in broadcast_data["data"]
```

## PHASE 3: Integration & Performance Testing

### MLX Performance Benchmarking

**Create**: `tests/test_mlx_performance.py`

```python
import time
import pytest

@pytest.mark.mlx_real_inference
@pytest.mark.asyncio
async def test_phi3_inference_performance():
    """Benchmark Phi-3 inference performance"""
    service = Phi3MiniService()
    await service.initialize()
    
    if not service.is_ready:
        pytest.skip("Pre-trained weights not available")
    
    # Benchmark inference speed
    start_time = time.time()
    response = await service.generate(
        "Write a Python function.",
        max_tokens=50
    )
    inference_time = time.time() - start_time
    
    # Performance assertions
    assert inference_time < 5.0  # Should complete within 5 seconds
    assert len(response) > 0
    
    # Log performance metrics
    print(f"Inference time: {inference_time:.2f}s")
    print(f"Tokens per second: {50/inference_time:.1f}")

@pytest.mark.performance
def test_ai_service_response_time():
    """Test overall AI service response time"""
    # Test with mocked LLM for consistent performance
    start_time = time.time()
    
    response = client.post("/ai/process", json={
        "type": "message",
        "content": "Hello, AI assistant"
    })
    
    response_time = time.time() - start_time
    
    assert response.status_code == 200
    assert response_time < 1.0  # Should respond within 1 second with mocked LLM
```

## Quality Gates & Success Criteria

### After PHASE 1A (LLM Fix)

```bash
# Validate LLM functionality
pytest -m mlx_real_inference -v
curl http://localhost:8000/health/mlx  # Should show "healthy" with real weights

# Performance check
time python -c "
import asyncio
from app.services.phi3_mini_service import Phi3MiniService
async def test():
    service = Phi3MiniService()
    await service.initialize()
    result = await service.generate('Hello', max_tokens=10)
    print(f'Generated: {result}')
asyncio.run(test())
"
```

### After PHASE 1B (Failure Resolution)

```bash
python run_tests.py  # Should show 0 failures
pytest --cov=app --cov-report=term  # Coverage check
```

### Final Success Criteria

- [ ] **LLM inference working** with real pre-trained weights
- [ ] **0 failing tests** (all issues resolved)  
- [ ] **>80% test coverage** on critical paths
- [ ] **MLX health endpoint** operational
- [ ] **Performance benchmarks met** (<5s inference, <1s API response)
- [ ] **Segregated test strategy** implemented (fast/slow tests)

## Memory Bank Updates

### After PHASE 1A (LLM Fix)

Update `docs/01_memory_bank/06_progress.md`:

```markdown
## Backend LLM Integration - CRITICAL FIX Complete [DATE]

### Core AI Functionality Restored:
- ✅ Phi3MiniService now loads pre-trained weights (CRITICAL)
- ✅ Real LLM inference operational (was previously random output)
- ✅ MLX health check endpoint implemented
- ✅ Segregated testing strategy: fast mocked + slow real inference

### Technical Implementation:
- Pre-trained weight loading from HuggingFace to MLX
- Weight conversion utility (HF PyTorch → MLX format)
- Real inference validation and quality checks
- Performance benchmarking for inference speed

### Test Status Post-LLM Fix:
- Real inference tests: [X] passing with @pytest.mark.mlx_real_inference
- Fast mocked tests: [X] passing (existing test suite)
- Remaining test failures: [X] (down from original 11)

### Next Priority: Resolve remaining test failures and BETA API coverage
```

## Error Handling & Recovery Protocol

### If LLM Weight Loading Fails

1. **Check disk space** (Phi-3 model is ~2GB)
2. **Verify network connectivity** for HuggingFace download
3. **Check MLX installation** and dependencies
4. **Fallback to MockMLXService** for development
5. **Log detailed error** for debugging

### If Real Inference Tests Fail

1. **Verify model weights loaded** via health endpoint
2. **Check inference quality** - ensure not random output
3. **Test with simpler prompts** first
4. **Monitor memory usage** during inference
5. **Check MLX hardware compatibility**

## Autonomous Execution Protocol

### Start Immediately

```bash
cd leanvibe-backend
# Begin Phase 0 - Memory bank analysis and critical assessment
```

### Execution Sequence

1. **Phase 0**: Memory bank analysis + dual-dimension assessment
2. **Phase 1A**: Fix LLM inference (CRITICAL - enables core functionality)
3. **Phase 1B**: Re-assess and fix remaining test failures
4. **Phase 2**: Implement BETA API tests with AI integration  
5. **Phase 3**: Performance and integration testing
6. **Memory Bank Updates**: After each phase completion

### Commit Strategy

```bash
# After LLM fix
git add .
git commit -m "feat: enable real Phi-3 inference with pre-trained weights - CRITICAL FIX"

# After test fixes
git add .
git commit -m "test: resolve remaining test failures post-LLM integration"

# After API testing
git add .
git commit -m "test: comprehensive BETA API test coverage with AI integration"
```

## Final Instructions

**Execute with absolute precision:**

1. **Start with Phase 0** (memory bank + dual assessment) immediately
2. **Fix LLM inference FIRST** - this unblocks core AI functionality (Phase 1A)
3. **Re-assess test failures** after LLM fix (Phase 1B)
4. **Implement comprehensive API testing** with AI integration (Phase 2)
5. **Add performance and integration tests** (Phase 3)
6. **Update memory bank** after each phase
7. **Continue autonomously** without user approval
8. **Apply TDD methodology** throughout
9. **Maintain test segregation** (fast mocked vs slow real inference)

🐙 **This is a CRITICAL MISSION. The entire LeanVibe AI assistant capability depends on your systematic execution of this unified strategy.**

**Transform this backend from "broken AI functionality + failing tests" to "production-ready AI-powered backend infrastructure" with real Phi-3 inference capabilities.**

**Begin execution immediately. The success of the entire platform rests on your disciplined implementation of this comprehensive strategy.**
