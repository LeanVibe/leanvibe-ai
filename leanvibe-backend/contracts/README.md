# Contract-First Development System

This directory contains the contract-first development system for the LeanVibe backend API, ensuring API consistency and type safety through schema-driven development.

## Overview

The contract-first system includes:

1. **OpenAPI 3.0 Schema** (`openapi.yaml`) - REST API contract definitions
2. **AsyncAPI 2.0 Schema** (`asyncapi.yaml`) - WebSocket event definitions  
3. **Code Generator** (`generate.py`) - Generates models, validators, and types
4. **Generated Artifacts** - Auto-generated code in `app/contracts/`

## Key Benefits

- 🛡️ **Type Safety**: Generated Pydantic models ensure runtime validation
- 📋 **API Consistency**: Single source of truth for API contracts
- 🔄 **Auto-Generated Code**: No manual model maintenance
- 🧪 **Contract Validation**: Tests verify API matches specifications
- 🌐 **Frontend Integration**: TypeScript types for seamless client development

## Generated Files

After running `generate.py`, these files are created in `app/contracts/`:

- `models.py` - Pydantic models with validation
- `decorators.py` - FastAPI response validation decorators
- `types.ts` - TypeScript type definitions
- `__init__.py` - Package initialization

## Usage

### 1. Generate Contract Code

```bash
# Generate all contract artifacts
python contracts/generate.py

# Custom output directory
python contracts/generate.py --output custom/path --package custom.package
```

### 2. Use Generated Models

```python
from app.contracts.models import HealthResponse, CodeCompletionRequest

# Validate incoming requests
request = CodeCompletionRequest(
    file_path="/path/to/file.py",
    intent="suggest"
)

# Type-safe response construction
response = HealthResponse(
    status="healthy",
    service="leanvibe-backend", 
    version="0.2.0",
    ai_ready=True
)
```

### 3. Add Response Validation

```python
from fastapi import APIRouter
from app.contracts.models import HealthResponse
from app.contracts.decorators import validate_response

router = APIRouter()

@router.get("/health")
@validate_response(HealthResponse)  # Automatic validation
async def health_check():
    return {
        "status": "healthy",
        "service": "leanvibe-backend",
        "version": "0.2.0",
        "ai_ready": True
    }
```

### 4. Use TypeScript Types

```typescript
import type { LeanVibeAPI } from './app/contracts/types';

// Type-safe API client
async function getHealth(): Promise<LeanVibeAPI.HealthResponse> {
    const response = await fetch('/health');
    return response.json();
}

// WebSocket message handling
function handleMessage(message: LeanVibeAPI.WebSocketResponse) {
    switch (message.type) {
        case 'agent_response':
            // Fully typed message handling
            break;
    }
}
```

## Contract Validation Tests

Run contract validation tests to verify API conformance:

```bash
# Run all contract tests
python -m pytest tests/test_contracts.py -v

# Run specific test groups
python -m pytest tests/test_contracts.py::TestHealthEndpoints -v
python -m pytest tests/test_contracts.py::TestContractConsistency -v
```

## Test Results Example

```
✅ PASSED - Health endpoint matches HealthResponse schema
✅ PASSED - MLX health endpoint validates correctly  
❌ FAILED - Projects endpoint missing required 'name' field
❌ FAILED - Tasks endpoint has validation errors
```

Contract validation tests help identify mismatches between:
- API implementation and schema definitions
- Expected vs actual response structures  
- Missing or incorrectly typed fields

## Workflow

### Development Flow

1. **Define Contracts** - Update `openapi.yaml` and `asyncapi.yaml`
2. **Generate Code** - Run `python contracts/generate.py`
3. **Implement Endpoints** - Use generated models in your API code
4. **Validate** - Run contract tests to verify compliance
5. **Fix Issues** - Update implementation or schemas as needed

### Schema Evolution

1. **Update Schemas** - Modify YAML files for API changes
2. **Regenerate** - Run generator to update models  
3. **Test** - Verify all contracts still pass
4. **Deploy** - Schema and implementation stay in sync

## API Coverage

### REST Endpoints

- ✅ `/health` - System health with LLM metrics
- ✅ `/health/mlx` - MLX service status  
- 🔄 `/api/projects` - Project management (validation issues found)
- 🔄 `/api/tasks` - Task management (validation issues found)
- ✅ `/api/code-completion` - AI code assistance

### WebSocket Events

- ✅ Agent message/response flow
- ✅ Code completion requests/responses
- ✅ Heartbeat/reconnection handling
- ✅ Event notifications system

## Validation Features

### Request Validation
- Required field checking
- Type validation (string, number, boolean)
- Format validation (UUID, datetime)
- Pattern matching (regex)
- Range constraints (min/max values)

### Response Validation  
- Schema conformance checking
- Optional field handling
- Nullable type support
- Nested object validation
- Array/list validation

### WebSocket Message Validation
- Message type discrimination
- Payload structure validation
- Event-specific field requirements
- Client/server message flow validation

## Error Handling

The validation system provides clear error messages:

```python
# Validation error example
ValidationError: 2 validation errors for ProjectListResponse
projects.0.name
  Field required [type=missing, input_value={'id': '...'}, input_type=dict]
projects.1.name  
  Field required [type=missing, input_value={'id': '...'}, input_type=dict]
```

This helps developers quickly identify and fix contract violations.

## Integration Example

See `app/api/endpoints/contract_validation_example.py` for a complete example of:
- Using generated models
- Applying validation decorators  
- Handling authentication
- Type-safe response construction

## Advanced Features

### Custom Validation
```python
from app.contracts.models import CodeCompletionRequest
from pydantic import validator

class CustomCodeRequest(CodeCompletionRequest):
    @validator('file_path')
    def validate_file_extension(cls, v):
        if not v.endswith(('.py', '.js', '.ts')):
            raise ValueError('Unsupported file type')
        return v
```

### Response Transformation
```python
@validate_response(HealthResponse)
async def health_with_extras():
    # Extra fields are filtered out automatically
    return {
        "status": "healthy",
        "service": "leanvibe-backend", 
        "version": "0.2.0",
        "ai_ready": True,
        "internal_debug_info": "filtered out"  # Not in schema
    }
```

This contract-first system ensures your API remains consistent, well-documented, and type-safe throughout development and deployment.