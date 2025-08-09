# 🚀 LeanVibe API Documentation - Contract-First Development

> **OpenAPI schema as source of truth, with auto-generated models and validation**

This documentation showcases LeanVibe's contract-first API approach where the OpenAPI schema drives development, ensuring type safety, automatic documentation, and seamless client integration.

## 📋 Table of Contents

- [Contract-First Philosophy](#contract-first-philosophy)
- [OpenAPI Schema Overview](#openapi-schema-overview)
- [Auto-Generated Models](#auto-generated-models)
- [API Endpoints](#api-endpoints)
- [Contract Validation](#contract-validation)
- [Synthetic Monitoring](#synthetic-monitoring)
- [Client Integration](#client-integration)
- [Breaking Change Detection](#breaking-change-detection)

---

## 🎯 Contract-First Philosophy

### Why Contract-First?

**Traditional API Development:**
```
Code → Documentation → Testing → Integration Issues
```

**LeanVibe Contract-First:**
```
Schema → Models → Implementation → Automatic Validation
```

### Benefits

- ✅ **No Runtime Type Errors**: Auto-generated models ensure type safety
- ✅ **Always Up-to-Date Docs**: Documentation generated from schema
- ✅ **Breaking Change Prevention**: Automatic compatibility checking
- ✅ **Client Integration**: TypeScript types generated automatically
- ✅ **Synthetic Monitoring**: API contracts drive health probes

---

## 📄 OpenAPI Schema Overview

### Schema Location and Management

```bash
# Master API contract
contracts/openapi.yaml          # Source of truth for all APIs

# Generated artifacts
contracts/types.ts              # TypeScript client types  
app/models/generated.py         # Pydantic models
contracts/README.md             # Auto-generated documentation
```

### Schema Structure

```yaml
# contracts/openapi.yaml
openapi: 3.0.3
info:
  title: LeanVibe L3 Coding Agent API
  version: 0.2.0
  description: Advanced AI-powered coding assistant with real-time collaboration

tags:
  - name: health
    description: Health check and system status endpoints
  - name: projects  
    description: Project management endpoints
  - name: tasks
    description: Task management and Kanban board endpoints
  - name: ai
    description: AI-powered code assistance endpoints
```

### Contract Development Workflow

```bash
# 1. Define API contract first
vim contracts/openapi.yaml

# 2. Generate models and types
gen

# 3. Implement using generated models
vim app/api/endpoints/your_endpoint.py

# 4. Validate implementation against contract
vf  # Includes contract validation

# 5. Deploy with automatic monitoring
pp  # Push with contract compatibility checks
```

---

## 🤖 Auto-Generated Models

### Python Pydantic Models

Models are automatically generated from OpenAPI schemas and provide:

```python
# Auto-generated from contracts/openapi.yaml
from app.models.generated import (
    HealthResponse,
    MLXHealthResponse, 
    CodeCompletionRequest,
    CodeCompletionResponse,
    Project,
    Task
)

# Type-safe endpoint implementation
@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service="leanvibe-backend", 
        version="0.2.0",
        ai_ready=True
    )
```

### TypeScript Client Types

```typescript
// Auto-generated contracts/types.ts
export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  service: string;
  version: string;
  ai_ready: boolean;
  agent_framework?: string;
  sessions?: object;
  event_streaming?: object;
  error_recovery?: object;
  system_status?: object;
  llm_metrics?: object;
}

// Usage in client code
const response: HealthResponse = await fetch('/health').then(r => r.json());
```

### Model Generation Commands

```bash
# Generate all models from schema
gen

# Generate with validation
gen --validate-compatibility

# Generate specific components
gen --models-only
gen --types-only

# Watch mode for development
gen --watch
```

---

## 🌐 API Endpoints

### Health and Monitoring

#### `GET /health`
Basic health check with comprehensive metrics.

**Response Schema:**
```yaml
components:
  schemas:
    HealthResponse:
      type: object
      required: [status, service, version, ai_ready]
      properties:
        status:
          type: string
          enum: [healthy, degraded, unhealthy]
        service:
          type: string
          example: leanvibe-backend
        version:
          type: string
          example: "0.2.0"
        ai_ready:
          type: boolean
        # ... additional system metrics
```

**Example Response:**
```json
{
  "status": "healthy",
  "service": "leanvibe-backend",
  "version": "0.2.0", 
  "ai_ready": true,
  "agent_framework": "pydantic.ai",
  "sessions": {"active": 3, "total": 127},
  "event_streaming": {"connected_clients": 2},
  "error_recovery": {"recent_recoveries": 0},
  "system_status": {"memory_mb": 245, "cpu_percent": 12},
  "llm_metrics": {"avg_response_time_ms": 340}
}
```

#### `GET /health/mlx`
MLX service health with model status and performance metrics.

**Response Schema:**
```yaml
MLXHealthResponse:
  type: object
  required: [status, model, model_loaded, inference_ready, confidence_score]
  properties:
    status:
      type: string
      enum: [healthy, uninitialized, degraded]
    model:
      type: string
    confidence_score:
      type: number
      minimum: 0
      maximum: 1
    performance:
      type: object
      properties:
        last_inference_time_ms:
          type: number
        average_tokens_per_second:
          type: number
        memory_efficiency:
          type: string
          enum: [good, moderate, poor]
```

### Project Management

#### `GET /api/projects`
List all projects with metrics and status.

**Response Example:**
```json
{
  "projects": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "awesome-project",
      "path": "/path/to/project",
      "status": "active",
      "created_at": "2025-01-15T10:30:00Z",
      "language": "python",
      "metrics": {
        "lines_of_code": 15420,
        "file_count": 87,
        "complexity_score": 2.3,
        "test_coverage": 0.85,
        "maintainability_index": 78
      }
    }
  ],
  "total": 1
}
```

### AI-Powered Code Assistance

#### `POST /api/code-completion`
Get AI-powered code completions with context awareness.

**Request Schema:**
```yaml
CodeCompletionRequest:
  type: object
  required: [file_path]
  properties:
    file_path:
      type: string
      minLength: 1
    cursor_position:
      type: integer
      minimum: 0
      default: 0
    intent:
      type: string
      enum: [suggest, explain, refactor, debug, optimize]
      default: suggest
    content:
      type: string
      nullable: true
    language:
      type: string
      nullable: true
```

**Response Schema:**
```yaml
CodeCompletionResponse:
  type: object
  required: [status, intent, response, confidence, requires_review, context_used, processing_time_ms]
  properties:
    status:
      type: string
      enum: [success, error]
    response:
      type: string
    confidence:
      type: number
      minimum: 0
      maximum: 1
    requires_review:
      type: boolean
    processing_time_ms:
      type: number
```

**Example Usage:**
```python
import requests

# Request code completion
response = requests.post(
    "http://localhost:8000/api/code-completion",
    json={
        "file_path": "/app/services/new_service.py",
        "cursor_position": 245,
        "intent": "suggest",
        "content": "def process_data(data):\n    # cursor here",
        "language": "python"
    }
)

completion = response.json()
print(f"Suggestion: {completion['response']}")
print(f"Confidence: {completion['confidence']:.2%}")
```

---

## ✅ Contract Validation

### Automatic Validation Pipeline

Every API change goes through automatic contract validation:

```bash
# Validation triggered by 'gen' command
gen --validate-compatibility

# Output example:
✅ Schema validation passed
✅ Backward compatibility check passed
✅ Generated models are valid
✅ All existing tests still pass with new schema
⚠️  New endpoint detected: /api/awesome
✅ All required properties have defaults or are nullable
```

### Breaking Change Detection

```yaml
# Example breaking change detection
# contracts/openapi.yaml - BAD CHANGE
components:
  schemas:
    HealthResponse:
      properties:
        status:
          type: string
          enum: [healthy, degraded]  # Removed 'unhealthy' - BREAKING!
```

```bash
gen --validate-compatibility
❌ Breaking changes detected:
  - Removed enum value 'unhealthy' from HealthResponse.status
  - This will break existing clients expecting this value
  
💡 Suggested fixes:
  1. Keep 'unhealthy' value for backward compatibility
  2. Add new status enum with deprecated field mapping
  3. Create new schema version (v2) with breaking changes
```

### Contract Testing

```python
# Automatic contract testing
# tests/tier0/test_contract_validation.py

def test_health_endpoint_matches_schema():
    """Ensure /health response matches OpenAPI schema"""
    response = client.get("/health")
    
    # Auto-generated validation from schema
    health_response = HealthResponse.model_validate(response.json())
    assert health_response.status in ["healthy", "degraded", "unhealthy"]
    assert isinstance(health_response.ai_ready, bool)

def test_openapi_schema_is_valid():
    """Ensure OpenAPI schema is syntactically correct"""
    from openapi_spec_validator import validate_spec
    
    with open("contracts/openapi.yaml") as f:
        spec = yaml.safe_load(f)
    
    validate_spec(spec)  # Raises exception if invalid
```

---

## 🔍 Synthetic Monitoring

### Contract-Driven Health Probes

Synthetic monitoring probes are automatically generated from OpenAPI contracts:

```bash
# Generated synthetic probes
deploy/synthetic_probes.sh

# Probes test every endpoint defined in schema:
✅ GET /health - Response time: 45ms, Status: 200
✅ GET /health/mlx - Response time: 120ms, Status: 200  
✅ GET /api/projects - Response time: 230ms, Status: 200
✅ POST /api/code-completion - Response time: 890ms, Status: 200

# Contract validation in probes:
✅ All responses match OpenAPI schema
✅ Required fields present
✅ Data types correct
✅ Enum values valid
```

### Probe Configuration

```yaml
# Generated from OpenAPI schema
# monitoring/synthetic_probes.yaml
probes:
  - name: health_check
    endpoint: GET /health
    expect_status: 200
    expect_schema: HealthResponse
    timeout_ms: 1000
    
  - name: code_completion
    endpoint: POST /api/code-completion
    payload:
      file_path: "/test/example.py"
      intent: "suggest"
    expect_status: 200  
    expect_schema: CodeCompletionResponse
    timeout_ms: 5000
```

### Monitoring Dashboard Integration

```bash
# View real-time synthetic probe results
qd  # Quality dashboard includes probe status

# API health overview shows:
# ✅ All endpoints responding (100% success rate)
# ✅ Average response time: 234ms
# ✅ Schema compliance: 100%
# ✅ Contract drift: 0 breaking changes
```

---

## 🔗 Client Integration

### Auto-Generated Client Code

TypeScript client generation provides seamless integration:

```typescript
// Auto-generated client (contracts/client.ts)
import { HealthResponse, CodeCompletionRequest, CodeCompletionResponse } from './types';

class LeanVibeClient {
  constructor(private baseUrl: string, private apiKey: string) {}

  async health(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }

  async codeCompletion(request: CodeCompletionRequest): Promise<CodeCompletionResponse> {
    const response = await fetch(`${this.baseUrl}/api/code-completion`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      },
      body: JSON.stringify(request)
    });
    return response.json();
  }
}
```

### Client Usage Examples

```typescript
// iOS/web client integration
import { LeanVibeClient } from './generated/client';

const client = new LeanVibeClient('http://localhost:8000', 'your-api-key');

// Type-safe API calls
const health = await client.health();
console.log(`Service is ${health.status}, AI ready: ${health.ai_ready}`);

const completion = await client.codeCompletion({
  file_path: '/app/main.py',
  cursor_position: 100,
  intent: 'suggest'
});

console.log(`AI suggestion: ${completion.response}`);
console.log(`Confidence: ${completion.confidence}`);
```

### SDK Generation for Multiple Languages

```bash
# Generate SDKs for different platforms
gen --sdk python    # Python client SDK
gen --sdk typescript # TypeScript/JavaScript SDK  
gen --sdk swift      # iOS Swift SDK
gen --sdk kotlin     # Android Kotlin SDK

# All SDKs automatically include:
# ✅ Type-safe request/response models
# ✅ Authentication handling
# ✅ Error handling and retries
# ✅ Async/await support
# ✅ Comprehensive documentation
```

---

## 🔄 Breaking Change Detection

### Schema Evolution Management

```yaml
# contracts/openapi.yaml - Version management
info:
  title: LeanVibe L3 Coding Agent API
  version: 0.3.0  # Bump version for breaking changes
  
# Deprecated fields example  
components:
  schemas:
    HealthResponse:
      properties:
        status:
          type: string
          enum: [healthy, degraded, unhealthy]
        service_name:  # NEW field
          type: string
        service:       # DEPRECATED field
          type: string
          deprecated: true
          description: "Use service_name instead"
```

### Migration Strategy

```bash
# Detect breaking changes before deployment
gen --validate-compatibility --base-version=0.2.0

# Output:
📊 Schema comparison (v0.2.0 → v0.3.0):
✅ 3 endpoints unchanged
✅ 1 endpoint enhanced (backward compatible)
❌ 1 breaking change detected:

Breaking Changes:
- HealthResponse.service field deprecated
  Impact: Existing clients may break
  Migration: Use service_name field instead
  
🚀 Recommended deployment strategy:
1. Deploy v0.3.0 with both fields (service + service_name)
2. Update clients to use service_name
3. Remove deprecated 'service' field in v0.4.0
```

### Gradual Migration Support

```python
# Implementation supporting both old and new fields
@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service="leanvibe-backend",        # Deprecated but maintained
        service_name="leanvibe-backend",   # New field
        version="0.3.0",
        ai_ready=True
    )
```

---

## 🛠 Development Workflow

### Contract-First Development Process

```bash
# 1. Start with API design
vim contracts/openapi.yaml
# Define new endpoint schema

# 2. Generate models and validate
gen --validate-compatibility
# ✅ Schema valid, models generated

# 3. Implement endpoint using generated models  
vim app/api/endpoints/new_feature.py
# Use auto-generated Pydantic models

# 4. Write contract-validated tests
vim tests/tier0/test_new_feature.py
# Tests automatically validate against schema

# 5. Fast verification with contract checking
vf
# ✅ Unit tests + contract validation + type checking

# 6. Full PR validation
vp  
# ✅ Integration tests + schema compatibility + coverage
```

### Schema-Driven Testing

```python
# Contract validation is built into tests
def test_new_endpoint_contract_compliance():
    response = client.post("/api/new-feature", json=valid_request)
    
    # Automatic schema validation
    assert response.status_code == 200
    
    # Generated model validation
    result = NewFeatureResponse.model_validate(response.json())
    assert result.status == "success"
    
    # Schema compliance automatically checked
    # No additional validation code needed!
```

### Real-Time Schema Drift Detection

```bash
# Continuous schema monitoring
qd  # Quality dashboard shows:

Schema Drift Analysis:
✅ 0 breaking changes in last 30 days
✅ 3 backward-compatible enhancements
✅ 100% schema compliance in production
✅ All clients using latest contract versions

Contract Health:
✅ OpenAPI schema validates successfully
✅ All endpoints have comprehensive schemas  
✅ 100% model generation success rate
✅ 0 deprecated fields in active use
```

---

## 📈 API Performance Monitoring

### Contract-Based Performance Tracking

```bash
# Performance metrics tied to contract endpoints
qd  # Shows per-endpoint performance:

Endpoint Performance (Last 24h):
┌─────────────────────┬─────────┬─────────┬──────────┐
│ Endpoint            │ P50     │ P95     │ P99      │
├─────────────────────┼─────────┼─────────┼──────────┤
│ GET /health         │ 45ms    │ 89ms    │ 156ms    │
│ GET /health/mlx     │ 120ms   │ 340ms   │ 580ms    │
│ POST /code-completion│ 890ms  │ 1.2s    │ 2.1s     │
│ GET /api/projects   │ 230ms   │ 450ms   │ 680ms    │
└─────────────────────┴─────────┴─────────┴──────────┘

Contract SLA Compliance:
✅ All endpoints under defined SLA thresholds
✅ No performance regressions detected
✅ 99.9% availability maintained
```

---

## 🚀 Advanced Features

### API Versioning Strategy

```yaml
# Support multiple API versions in same schema
paths:
  /api/v1/health:        # Stable v1 API
    get:
      # ... v1 implementation
  
  /api/v2/health:        # New v2 API with enhancements
    get:
      # ... v2 implementation with additional fields

  /health:               # Latest API (aliases to current version)
    get:
      # ... points to v2
```

### Custom Validation Rules

```python
# Custom contract validation beyond OpenAPI
# tools/custom_validators.py

def validate_endpoint_security(endpoint_path: str, method: str) -> bool:
    """Ensure all endpoints have proper security schemes"""
    # Custom business logic validation
    # Returns True if valid, False with details if not
    pass

def validate_response_time_slas(endpoint_path: str) -> bool:
    """Ensure endpoints have realistic SLA definitions"""
    # Check that performance expectations are defined
    pass
```

### Contract Testing in CI/CD

```yaml
# .github/workflows/contract-validation.yml
name: Contract Validation
on: [push, pull_request]

jobs:
  validate-contracts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Validate OpenAPI Schema
        run: |
          gen --validate-only --strict
          
      - name: Check Breaking Changes  
        run: |
          gen --validate-compatibility --base-ref=main
          
      - name: Generate and Test Models
        run: |
          gen
          vf  # Fast tests including contract validation
          
      - name: Synthetic Probe Validation
        run: |
          ./deploy/synthetic_probes.sh --dry-run
```

---

**🎯 Contract-first development ensures your APIs are reliable, documented, and evolution-friendly by design.**

For more information:
- **[Quick Start Guide](./QUICKSTART.md)** - Get started with contract-first development
- **[Installation Guide](./INSTALLATION.md)** - Set up the complete toolchain
- **[OpenAPI Schema](./contracts/openapi.yaml)** - Browse the complete API contract