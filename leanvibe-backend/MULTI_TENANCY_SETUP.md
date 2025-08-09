# LeanVibe Multi-Tenancy Setup Guide

## Overview

LeanVibe's multi-tenant architecture provides complete tenant isolation, hierarchical organization support, and enterprise-grade security for SaaS deployments. This guide covers the setup and configuration of multi-tenancy features including tenant management, resource quotas, data residency, and compliance requirements.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                Multi-Tenant Architecture                │
├─────────────────────────────────────────────────────────┤
│  Tenant       │  Resource      │  Data           │
│  Isolation    │  Quotas        │  Residency      │
│               │                │                 │
│  Hierarchical │  Usage         │  Compliance     │
│  Organizations│  Monitoring    │  & Security     │
└─────────────────────────────────────────────────────────┘
           │                    │                    │
    ┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
    │  Database   │    │   Application   │    │   Regional  │
    │  Isolation  │    │   Middleware    │    │   Data      │
    │             │    │                 │    │   Centers   │
    └─────────────┘    └─────────────────┘    └─────────────┘
```

## Tenant Creation and Management

### Creating a New Tenant

**API Endpoint:**
```
POST /api/v1/admin/tenants
```

**Request Example:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/tenants" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "Acme Corporation",
    "display_name": "Acme Corp",
    "slug": "acme-corp",
    "admin_email": "admin@acme-corp.com",
    "plan": "enterprise",
    "data_residency": "us",
    "parent_tenant_id": null
  }'
```

**Response:**
```json
{
  "id": "tenant-uuid-here",
  "organization_name": "Acme Corporation",
  "slug": "acme-corp",
  "status": "trial",
  "plan": "enterprise",
  "data_residency": "us",
  "quotas": {
    "max_users": 999999,
    "max_projects": 999999,
    "max_api_calls_per_month": 999999999,
    "max_storage_mb": 1048576,
    "max_ai_requests_per_day": 10000,
    "max_concurrent_sessions": 100
  },
  "created_at": "2024-01-01T00:00:00Z",
  "trial_ends_at": "2024-01-31T00:00:00Z"
}
```

### Tenant Configuration Options

#### Subscription Plans and Quotas

**Developer Plan Configuration:**
```json
{
  "plan": "developer",
  "quotas": {
    "max_users": 1,
    "max_projects": 5,
    "max_api_calls_per_month": 10000,
    "max_storage_mb": 1024,
    "max_ai_requests_per_day": 100,
    "max_concurrent_sessions": 2
  },
  "features": {
    "sso_support": false,
    "saml_support": false,
    "custom_integrations": false,
    "dedicated_support": false
  }
}
```

**Team Plan Configuration:**
```json
{
  "plan": "team", 
  "quotas": {
    "max_users": 10,
    "max_projects": 50,
    "max_api_calls_per_month": 100000,
    "max_storage_mb": 10240,
    "max_ai_requests_per_day": 1000,
    "max_concurrent_sessions": 10
  },
  "features": {
    "sso_support": true,
    "saml_support": false,
    "custom_integrations": false,
    "dedicated_support": false
  }
}
```

**Enterprise Plan Configuration:**
```json
{
  "plan": "enterprise",
  "quotas": {
    "max_users": 999999,
    "max_projects": 999999, 
    "max_api_calls_per_month": 999999999,
    "max_storage_mb": 1048576,
    "max_ai_requests_per_day": 10000,
    "max_concurrent_sessions": 100
  },
  "features": {
    "sso_support": true,
    "saml_support": true,
    "custom_integrations": true,
    "dedicated_support": true,
    "sla_guarantee": true
  }
}
```

## Data Residency and Compliance

### Regional Data Centers

LeanVibe supports data residency in multiple regions:

- **US**: `us-east-1`, `us-west-2`
- **EU**: `eu-central-1` (Frankfurt), `eu-west-1` (Ireland)
- **UK**: `eu-west-2` (London)
- **Canada**: `ca-central-1` (Toronto)
- **Australia**: `ap-southeast-2` (Sydney)

### Configuring Data Residency

**Set Data Residency during Tenant Creation:**
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/tenants" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "European Corp Ltd",
    "slug": "european-corp",
    "admin_email": "admin@european-corp.eu",
    "plan": "enterprise",
    "data_residency": "eu"
  }'
```

**Update Existing Tenant Data Residency:**
```bash
curl -X PATCH "https://api.leanvibe.ai/v1/admin/tenants/{tenant_id}" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "data_residency": "uk"
  }'
```

### GDPR Compliance Features

#### Data Processing Configuration
```json
{
  "gdpr_settings": {
    "data_processing_basis": "contract",
    "retention_period_days": 2555,
    "auto_deletion_enabled": true,
    "data_portability_enabled": true,
    "right_to_erasure_enabled": true,
    "consent_management": {
      "analytics_consent": false,
      "marketing_consent": false,
      "functional_consent": true
    }
  }
}
```

#### Data Subject Rights Implementation
```python
# Data Export (Right to Portability)
@router.get("/gdpr/export/{tenant_id}")
async def export_tenant_data(tenant_id: UUID, admin_user=Depends(get_admin)):
    """Export all tenant data for GDPR compliance"""
    return await gdpr_service.export_tenant_data(tenant_id)

# Data Deletion (Right to Erasure)
@router.delete("/gdpr/erase/{tenant_id}")
async def erase_tenant_data(tenant_id: UUID, admin_user=Depends(get_admin)):
    """Permanently delete all tenant data"""
    return await gdpr_service.erase_tenant_data(tenant_id)
```

## Resource Quotas and Monitoring

### Real-Time Usage Tracking

**Get Current Usage:**
```bash
curl -X GET "https://api.leanvibe.ai/v1/tenants/{tenant_id}/usage" \
  -H "Authorization: Bearer tenant-admin-token"
```

**Response:**
```json
{
  "tenant_id": "tenant-uuid-here",
  "current_usage": {
    "users_count": 45,
    "projects_count": 23,
    "api_calls_this_month": 85000,
    "storage_used_mb": 8500,
    "ai_requests_today": 750,
    "concurrent_sessions": 12
  },
  "quotas": {
    "max_users": 999999,
    "max_projects": 999999,
    "max_api_calls_per_month": 999999999,
    "max_storage_mb": 1048576,
    "max_ai_requests_per_day": 10000,
    "max_concurrent_sessions": 100
  },
  "utilization_percentages": {
    "users": 0.0045,
    "projects": 0.0023,
    "api_calls": 8.5,
    "storage": 0.81,
    "ai_requests": 7.5,
    "concurrent_sessions": 12.0
  },
  "last_calculated_at": "2024-01-15T10:30:00Z"
}
```

### Quota Enforcement

#### Automatic Quota Enforcement
```python
from app.services.tenant_service import tenant_service

# Check quota before API call
async def enforce_api_quota(tenant_id: UUID):
    usage = await tenant_service.get_current_usage(tenant_id)
    tenant = await tenant_service.get_tenant(tenant_id)
    
    if usage.api_calls_this_month >= tenant.quotas.max_api_calls_per_month:
        raise QuotaExceededError("Monthly API call limit reached")
    
    # Record API call
    await tenant_service.increment_usage(tenant_id, "api_calls", 1)
```

#### Quota Exceeded Handling
```json
{
  "quota_exceeded_responses": {
    "api_calls": {
      "status_code": 429,
      "message": "Monthly API call quota exceeded",
      "retry_after": "next_billing_cycle",
      "upgrade_options": ["team", "enterprise"]
    },
    "storage": {
      "status_code": 413,
      "message": "Storage quota exceeded", 
      "available_actions": ["delete_files", "upgrade_plan"],
      "current_usage_mb": 1024,
      "quota_limit_mb": 1024
    }
  }
}
```

### Usage Analytics and Alerting

#### Usage Monitoring Dashboard
```bash
# Get usage trends
curl -X GET "https://api.leanvibe.ai/v1/tenants/{tenant_id}/usage/trends" \
  -H "Authorization: Bearer tenant-admin-token" \
  -G -d "period=30d" -d "metrics=api_calls,storage,users"
```

#### Quota Alert Configuration
```json
{
  "quota_alerts": {
    "api_calls": {
      "warning_threshold": 80,
      "critical_threshold": 95,
      "notification_channels": ["email", "webhook"],
      "recipients": ["admin@company.com"]
    },
    "storage": {
      "warning_threshold": 85,
      "critical_threshold": 95,
      "auto_cleanup_enabled": false
    }
  }
}
```

## Hierarchical Organizations

### Multi-Level Organization Structure

LeanVibe supports complex organizational hierarchies:

```
Parent Corporation (Enterprise)
├── Subsidiary A (Team)
│   ├── Division 1 (Developer)
│   └── Division 2 (Developer)
├── Subsidiary B (Enterprise)
│   ├── Regional Office EU (Team)
│   └── Regional Office APAC (Team)
└── Subsidiary C (Team)
```

### Creating Organizational Hierarchy

#### Create Parent Organization
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/tenants" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "Global Corp",
    "slug": "global-corp",
    "admin_email": "admin@global-corp.com",
    "plan": "enterprise",
    "parent_tenant_id": null
  }'
```

#### Create Child Organizations
```bash
curl -X POST "https://api.leanvibe.ai/v1/admin/tenants" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "Global Corp - European Division",
    "slug": "global-corp-eu",
    "admin_email": "admin-eu@global-corp.com",
    "plan": "team",
    "parent_tenant_id": "parent-tenant-uuid",
    "data_residency": "eu"
  }'
```

### Hierarchical Resource Management

#### Consolidated Billing
```json
{
  "billing_consolidation": {
    "parent_tenant_id": "parent-uuid",
    "child_tenants": [
      {
        "tenant_id": "child-1-uuid",
        "cost_allocation_percentage": 40
      },
      {
        "tenant_id": "child-2-uuid", 
        "cost_allocation_percentage": 35
      },
      {
        "tenant_id": "child-3-uuid",
        "cost_allocation_percentage": 25
      }
    ],
    "consolidated_invoicing": true,
    "shared_quotas": false
  }
}
```

#### Cross-Tenant Resource Sharing
```json
{
  "resource_sharing": {
    "shared_storage_pool": {
      "total_allocation_gb": 1000,
      "child_allocations": {
        "child-1": {"allocated_gb": 400, "used_gb": 350},
        "child-2": {"allocated_gb": 300, "used_gb": 150},
        "child-3": {"allocated_gb": 300, "used_gb": 200}
      }
    },
    "shared_user_pool": {
      "total_seats": 500,
      "utilized_seats": 287
    }
  }
}
```

## Tenant Isolation and Security

### Database-Level Isolation

#### Row-Level Security (RLS)
```sql
-- Enable RLS on all tenant tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;

-- Create tenant isolation policies
CREATE POLICY tenant_isolation ON users
  FOR ALL TO application_user
  USING (tenant_id = current_setting('app.tenant_id')::UUID);

CREATE POLICY tenant_isolation ON projects  
  FOR ALL TO application_user
  USING (tenant_id = current_setting('app.tenant_id')::UUID);
```

#### Connection-Level Isolation
```python
from app.core.database import get_tenant_connection

async def get_tenant_db_session(tenant_id: UUID):
    """Get database session with tenant context"""
    async with get_tenant_connection() as conn:
        # Set tenant context for RLS
        await conn.execute(
            "SET app.tenant_id = %s", [str(tenant_id)]
        )
        yield conn
```

### Application-Level Security

#### Middleware Enforcement
```python
from fastapi import Request, HTTPException
from app.models.tenant_models import Tenant

async def tenant_isolation_middleware(request: Request, call_next):
    """Ensure all requests are properly scoped to tenant"""
    
    # Extract tenant ID from token or subdomain
    tenant_id = extract_tenant_id(request)
    
    if not tenant_id:
        raise HTTPException(403, "Tenant context required")
    
    # Verify tenant exists and is active
    tenant = await get_tenant(tenant_id)
    if not tenant or tenant.status != "active":
        raise HTTPException(403, "Invalid or inactive tenant")
    
    # Add tenant context to request
    request.state.tenant = tenant
    
    response = await call_next(request)
    return response
```

### Encryption and Key Management

#### Tenant-Specific Encryption
```json
{
  "encryption_settings": {
    "encryption_at_rest": true,
    "tenant_specific_keys": true,
    "key_rotation_days": 90,
    "key_management_service": "aws_kms",
    "regional_key_storage": true
  }
}
```

#### Data Encryption Implementation
```python
from cryptography.fernet import Fernet
import base64

class TenantEncryption:
    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id
        self.encryption_key = self._get_tenant_key(tenant_id)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt data with tenant-specific key"""
        f = Fernet(self.encryption_key)
        encrypted = f.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data with tenant-specific key"""
        f = Fernet(self.encryption_key)
        decrypted = f.decrypt(base64.b64decode(encrypted_data))
        return decrypted.decode()
```

## Performance Optimization

### Database Partitioning

#### Tenant-Based Table Partitioning
```sql
-- Create partitioned table by tenant
CREATE TABLE tenant_data (
    id UUID DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY HASH (tenant_id);

-- Create partitions for tenant ranges
CREATE TABLE tenant_data_0 PARTITION OF tenant_data
    FOR VALUES WITH (modulus 8, remainder 0);

CREATE TABLE tenant_data_1 PARTITION OF tenant_data
    FOR VALUES WITH (modulus 8, remainder 1);
-- ... continue for remaining partitions
```

#### Automated Partition Management
```python
async def manage_tenant_partitions():
    """Automatically manage tenant data partitions"""
    
    # Monitor partition sizes
    partition_stats = await get_partition_statistics()
    
    for partition in partition_stats:
        if partition.size_gb > 100:  # 100GB threshold
            await create_additional_partition(partition.tenant_range)
        
        if partition.age_days > 2555:  # 7 years retention
            await archive_old_partition(partition.name)
```

### Caching Strategy

#### Multi-Level Caching
```python
from app.core.cache import TenantAwareCache

class TenantCache:
    def __init__(self):
        self.redis_client = redis.Redis()
        self.local_cache = {}
    
    async def get(self, tenant_id: UUID, key: str):
        """Get cached value with tenant isolation"""
        tenant_key = f"tenant:{tenant_id}:{key}"
        
        # L1: Local cache
        if tenant_key in self.local_cache:
            return self.local_cache[tenant_key]
        
        # L2: Redis cache
        value = await self.redis_client.get(tenant_key)
        if value:
            self.local_cache[tenant_key] = value
            return value
        
        return None
    
    async def set(self, tenant_id: UUID, key: str, value, ttl: int = 3600):
        """Set cached value with tenant isolation"""
        tenant_key = f"tenant:{tenant_id}:{key}"
        
        # Set in both cache levels
        self.local_cache[tenant_key] = value
        await self.redis_client.setex(tenant_key, ttl, value)
```

## Monitoring and Observability

### Tenant-Specific Metrics

#### Custom Metrics Collection
```python
from prometheus_client import Counter, Histogram, Gauge

# Tenant-specific metrics
tenant_requests = Counter(
    'tenant_requests_total',
    'Total requests per tenant',
    ['tenant_id', 'endpoint']
)

tenant_response_time = Histogram(
    'tenant_response_seconds',
    'Response time per tenant',
    ['tenant_id']
)

tenant_active_users = Gauge(
    'tenant_active_users',
    'Currently active users per tenant',
    ['tenant_id']
)
```

#### Health Check Endpoints
```python
@router.get("/health/tenant/{tenant_id}")
async def tenant_health_check(tenant_id: UUID):
    """Comprehensive tenant health check"""
    
    health_status = {
        "tenant_id": str(tenant_id),
        "status": "healthy",
        "checks": {
            "database_connection": await check_tenant_db_connection(tenant_id),
            "cache_availability": await check_tenant_cache(tenant_id),
            "quota_status": await check_tenant_quotas(tenant_id),
            "billing_status": await check_tenant_billing(tenant_id)
        },
        "metrics": {
            "active_users": await get_active_users_count(tenant_id),
            "current_projects": await get_projects_count(tenant_id),
            "api_calls_today": await get_daily_api_calls(tenant_id)
        }
    }
    
    return health_status
```

## Migration and Backup

### Tenant Data Migration

#### Cross-Region Migration
```bash
# Export tenant data
curl -X POST "https://api.leanvibe.ai/v1/admin/tenants/{tenant_id}/export" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "destination_region": "eu-central-1",
    "include_historical_data": true,
    "encryption_enabled": true
  }'

# Import to new region
curl -X POST "https://api.leanvibe.ai/v1/admin/tenants/import" \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "source_export_id": "export-uuid",
    "target_region": "eu-central-1",
    "new_tenant_slug": "migrated-tenant"
  }'
```

### Automated Backup Strategy

#### Multi-Region Backup Configuration
```json
{
  "backup_strategy": {
    "frequency": "daily",
    "retention_days": 90,
    "cross_region_replication": true,
    "encryption_enabled": true,
    "backup_regions": {
      "primary": "us-east-1",
      "secondary": "us-west-2",
      "tertiary": "eu-central-1"
    },
    "incremental_backups": true,
    "point_in_time_recovery": true
  }
}
```

## Enterprise Support

### Dedicated Tenant Management

For enterprise multi-tenancy assistance:
- **Tenant Architecture Consultation**: Custom deployment planning
- **Migration Assistance**: Zero-downtime tenant migrations
- **Performance Optimization**: Tenant-specific performance tuning
- **Compliance Support**: GDPR, SOC2, and regional compliance

### Contact Information
- **Email**: tenancy-support@leanvibe.ai
- **Phone**: +1 (555) 123-4567 ext. 4
- **Slack**: #enterprise-tenancy in LeanVibe Community
- **Documentation**: [Multi-Tenancy Knowledge Base](https://docs.leanvibe.ai/enterprise/multi-tenancy)

---

**Ready to implement enterprise multi-tenancy?** Contact our architecture specialists for personalized setup assistance and ensure optimal tenant isolation and performance for your organization.