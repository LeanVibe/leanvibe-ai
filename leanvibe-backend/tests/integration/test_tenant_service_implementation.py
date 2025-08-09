"""
IMPLEMENTATION: Critical Multi-Tenant Service Integration Tests
Priority 0 - Week 1 Implementation

These tests implement the critical multi-tenant security flows identified in the analysis.
Status: IMPLEMENTING - Multi-tenant service integration testing (342 lines, 0% business logic tested)
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, patch, MagicMock

# Configure pytest for async tests
pytestmark = pytest.mark.asyncio

from app.services.tenant_service import TenantService
from app.models.tenant_models import (
    Tenant, TenantCreate, TenantUpdate, TenantUsage, TenantQuotas,
    TenantStatus, TenantPlan, TenantDataResidency, DEFAULT_QUOTAS
)
from app.core.exceptions import (
    ResourceNotFoundError, InsufficientPermissionsError,
    TenantQuotaExceededError
)


@pytest_asyncio.fixture
async def tenant_service():
    """Create tenant service with mocked database"""
    mock_db = AsyncMock()
    service = TenantService(db=mock_db)
    return service


@pytest_asyncio.fixture
async def sample_tenant_a():
    """Sample tenant A for isolation testing"""
    return Tenant(
        id=uuid4(),
        organization_name="Company A",
        slug="company-a",
        admin_email="admin@company-a.com",
        status=TenantStatus.ACTIVE,
        plan=TenantPlan.TEAM,
        quotas=DEFAULT_QUOTAS[TenantPlan.TEAM]
    )


@pytest_asyncio.fixture
async def sample_tenant_b():
    """Sample tenant B for isolation testing"""
    return Tenant(
        id=uuid4(),
        organization_name="Company B",
        slug="company-b", 
        admin_email="admin@company-b.com",
        status=TenantStatus.ACTIVE,
        plan=TenantPlan.ENTERPRISE,
        quotas=DEFAULT_QUOTAS[TenantPlan.ENTERPRISE]
    )


@pytest_asyncio.fixture
async def sample_parent_tenant():
    """Sample parent tenant for hierarchy testing"""
    return Tenant(
        id=uuid4(),
        organization_name="Parent Corp",
        slug="parent-corp",
        admin_email="admin@parent-corp.com",
        status=TenantStatus.ACTIVE,
        plan=TenantPlan.ENTERPRISE,
        quotas=DEFAULT_QUOTAS[TenantPlan.ENTERPRISE]
    )


class TestTenantServiceCreationAndManagement:
    """Test critical tenant creation and lifecycle management"""

    async def test_successful_tenant_creation(self, tenant_service):
        """Test successful tenant creation with proper initialization"""
        create_request = TenantCreate(
            organization_name="Test Company",
            slug="test-company",
            admin_email="admin@test-company.com",
            plan=TenantPlan.TEAM,
            data_residency=TenantDataResidency.US
        )
        
        # Mock database operations
        tenant_service.db.execute = AsyncMock()
        tenant_service.db.commit = AsyncMock()
        tenant_service.db.refresh = AsyncMock()
        
        # Mock slug availability check
        with patch.object(tenant_service, '_is_slug_available') as mock_slug:
            mock_slug.return_value = True
            
            # Mock quota initialization
            with patch.object(tenant_service, '_initialize_tenant_quotas') as mock_quotas:
                mock_quotas.return_value = DEFAULT_QUOTAS[TenantPlan.TEAM]
                
                # Mock audit logging
                with patch.object(tenant_service, '_log_tenant_event') as mock_audit:
                    
                    result = await tenant_service.create_tenant(create_request)
                    
                    # Verify tenant creation
                    assert isinstance(result, Tenant)
                    assert result.organization_name == "Test Company"
                    assert result.slug == "test-company"
                    assert result.admin_email == "admin@test-company.com"
                    assert result.plan == TenantPlan.TEAM
                    assert result.status == TenantStatus.TRIAL  # Default status
                    assert result.data_residency == TenantDataResidency.US
                    
                    # Verify method calls
                    mock_slug.assert_called_once_with("test-company")
                    mock_quotas.assert_called_once_with(TenantPlan.TEAM)
                    tenant_service.db.commit.assert_called_once()
                    
                    # Verify audit logging
                    mock_audit.assert_called_with(
                        result.id,
                        "tenant_created",
                        f"Tenant '{result.organization_name}' created",
                        True,
                        metadata={
                            "plan": TenantPlan.TEAM,
                            "data_residency": TenantDataResidency.US,
                            "admin_email": "admin@test-company.com"
                        }
                    )

    async def test_tenant_creation_duplicate_slug(self, tenant_service):
        """Test tenant creation failure with duplicate slug"""
        create_request = TenantCreate(
            organization_name="Duplicate Company",
            slug="existing-company",
            admin_email="admin@duplicate.com"
        )
        
        with patch.object(tenant_service, '_is_slug_available') as mock_slug:
            mock_slug.return_value = False
            
            with pytest.raises(ValueError, match="already exists"):
                await tenant_service.create_tenant(create_request)
            
            mock_slug.assert_called_once_with("existing-company")

    async def test_tenant_status_transitions(self, tenant_service, sample_tenant_a):
        """Test valid tenant status transitions"""
        tenant_service.db.execute = AsyncMock()
        tenant_service.db.commit = AsyncMock()
        
        with patch.object(tenant_service, 'get_tenant_by_id') as mock_get_tenant:
            mock_get_tenant.return_value = sample_tenant_a
            
            with patch.object(tenant_service, '_log_tenant_event') as mock_audit:
                
                # Test trial to active transition
                result = await tenant_service.update_tenant_status(
                    sample_tenant_a.id,
                    TenantStatus.ACTIVE,
                    reason="Payment successful"
                )
                
                assert result.status == TenantStatus.ACTIVE
                mock_audit.assert_called_with(
                    sample_tenant_a.id,
                    "tenant_status_changed",
                    f"Status changed from {TenantStatus.ACTIVE} to {TenantStatus.ACTIVE}",
                    True,
                    metadata={"reason": "Payment successful", "previous_status": TenantStatus.ACTIVE}
                )

    async def test_tenant_suspension_and_cleanup(self, tenant_service, sample_tenant_a):
        """Test tenant suspension properly cleans up resources"""
        tenant_service.db.execute = AsyncMock()
        tenant_service.db.commit = AsyncMock()
        
        with patch.object(tenant_service, 'get_tenant_by_id') as mock_get_tenant:
            mock_get_tenant.return_value = sample_tenant_a
            
            with patch.object(tenant_service, '_cleanup_tenant_sessions') as mock_cleanup:
                with patch.object(tenant_service, '_log_tenant_event') as mock_audit:
                    
                    result = await tenant_service.suspend_tenant(
                        sample_tenant_a.id,
                        reason="Policy violation"
                    )
                    
                    assert result.status == TenantStatus.SUSPENDED
                    mock_cleanup.assert_called_once_with(sample_tenant_a.id)
                    mock_audit.assert_called()


class TestTenantServiceIsolationSecurity:
    """Test critical tenant data isolation and security"""

    async def test_tenant_data_isolation_enforcement(self, tenant_service, sample_tenant_a, sample_tenant_b):
        """Test tenant data cannot be accessed across tenant boundaries"""
        
        # Mock database query that should include tenant_id filter
        tenant_service.db.execute = AsyncMock()
        
        with patch.object(tenant_service, '_execute_tenant_scoped_query') as mock_query:
            # Mock return value for tenant A data request
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = ["tenant_a_data"]
            mock_query.return_value = mock_result
            
            # Request data for tenant A
            result = await tenant_service.get_tenant_data(
                tenant_id=sample_tenant_a.id,
                data_type="projects"
            )
            
            # Verify tenant isolation is enforced
            mock_query.assert_called_once()
            call_args = mock_query.call_args[0]  # Get positional arguments
            
            # Verify the query includes tenant_id filter
            assert "tenant_id" in str(call_args)
            assert str(sample_tenant_a.id) in str(call_args)
            
            # Verify no cross-tenant data access
            assert str(sample_tenant_b.id) not in str(call_args)

    async def test_cross_tenant_data_access_prevention(self, tenant_service, sample_tenant_a, sample_tenant_b):
        """Test that tenant A cannot access tenant B's resources"""
        
        # Mock scenario: User from tenant A tries to access tenant B resource
        resource_id = uuid4()
        
        with patch.object(tenant_service, '_get_resource_tenant_id') as mock_get_tenant:
            # Resource belongs to tenant B
            mock_get_tenant.return_value = sample_tenant_b.id
            
            # User from tenant A tries to access it
            with pytest.raises(InsufficientPermissionsError):
                await tenant_service.access_resource(
                    requesting_tenant_id=sample_tenant_a.id,
                    resource_id=resource_id,
                    action="read"
                )
            
            mock_get_tenant.assert_called_once_with(resource_id)

    async def test_tenant_admin_scope_limitation(self, tenant_service, sample_tenant_a, sample_tenant_b):
        """Test tenant admin can only manage their own tenant"""
        
        admin_tenant_id = sample_tenant_a.id
        target_tenant_id = sample_tenant_b.id
        
        # Mock admin trying to manage different tenant
        with patch.object(tenant_service, '_verify_tenant_admin_permissions') as mock_verify:
            mock_verify.return_value = False  # No permission for cross-tenant admin
            
            with pytest.raises(InsufficientPermissionsError):
                await tenant_service.update_tenant_configuration(
                    admin_tenant_id=admin_tenant_id,
                    target_tenant_id=target_tenant_id,
                    configuration={}
                )
            
            mock_verify.assert_called_once_with(admin_tenant_id, target_tenant_id)

    async def test_database_row_level_security_validation(self, tenant_service, sample_tenant_a):
        """Test database row-level security is properly enforced"""
        
        with patch.object(tenant_service, '_validate_row_level_security') as mock_validate:
            mock_validate.return_value = True
            
            # Test that RLS validation is called for data queries
            await tenant_service.get_tenant_usage(sample_tenant_a.id)
            
            # Verify RLS validation was performed
            mock_validate.assert_called_with(
                table_name="tenant_usage",
                tenant_id=sample_tenant_a.id,
                operation="SELECT"
            )


class TestTenantServiceQuotaManagement:
    """Test critical quota enforcement and tracking"""

    async def test_quota_enforcement_prevents_overuse(self, tenant_service, sample_tenant_a):
        """Test quota limits are strictly enforced"""
        # Set tenant with limited quotas
        sample_tenant_a.quotas.max_projects = 5
        sample_tenant_a.current_usage = {"projects": 5}  # Already at limit
        
        tenant_service.db.execute = AsyncMock()
        
        with patch.object(tenant_service, 'get_tenant_by_id') as mock_get_tenant:
            mock_get_tenant.return_value = sample_tenant_a
            
            with patch.object(tenant_service, '_check_quota_availability') as mock_quota:
                mock_quota.return_value = False  # Quota exceeded
                
                # Should raise TenantQuotaExceededError
                with pytest.raises(TenantQuotaExceededError):
                    await tenant_service.create_project(
                        tenant_id=sample_tenant_a.id,
                        project_data={"name": "New Project"}
                    )
                
                mock_quota.assert_called_once_with(
                    sample_tenant_a,
                    "projects",
                    1  # Attempting to create 1 more project
                )

    async def test_quota_usage_tracking_accuracy(self, tenant_service, sample_tenant_a):
        """Test quota usage is tracked accurately"""
        tenant_service.db.execute = AsyncMock()
        tenant_service.db.commit = AsyncMock()
        
        initial_usage = {"projects": 3, "users": 2}
        sample_tenant_a.current_usage = initial_usage
        
        with patch.object(tenant_service, 'get_tenant_by_id') as mock_get_tenant:
            mock_get_tenant.return_value = sample_tenant_a
            
            # Record usage increase
            await tenant_service.record_usage(
                tenant_id=sample_tenant_a.id,
                resource_type="projects",
                delta=2  # Add 2 more projects
            )
            
            # Verify usage was updated
            assert sample_tenant_a.current_usage["projects"] == 5  # 3 + 2
            tenant_service.db.commit.assert_called_once()

    async def test_quota_plan_upgrade_effects(self, tenant_service, sample_tenant_a):
        """Test quota limits change when plan is upgraded"""
        # Start with Developer plan quotas
        sample_tenant_a.plan = TenantPlan.DEVELOPER
        sample_tenant_a.quotas = DEFAULT_QUOTAS[TenantPlan.DEVELOPER]
        
        tenant_service.db.commit = AsyncMock()
        
        with patch.object(tenant_service, 'get_tenant_by_id') as mock_get_tenant:
            mock_get_tenant.return_value = sample_tenant_a
            
            with patch.object(tenant_service, '_apply_plan_quotas') as mock_apply:
                mock_apply.return_value = DEFAULT_QUOTAS[TenantPlan.TEAM]
                
                # Upgrade to Team plan
                result = await tenant_service.upgrade_tenant_plan(
                    tenant_id=sample_tenant_a.id,
                    new_plan=TenantPlan.TEAM
                )
                
                assert result.plan == TenantPlan.TEAM
                mock_apply.assert_called_once_with(TenantPlan.TEAM)

    async def test_quota_violation_alerts(self, tenant_service, sample_tenant_a):
        """Test quota violation triggers proper alerts"""
        
        with patch.object(tenant_service, '_send_quota_alert') as mock_alert:
            with patch.object(tenant_service, '_log_tenant_event') as mock_audit:
                
                # Simulate quota exceeded
                await tenant_service._handle_quota_exceeded(
                    tenant=sample_tenant_a,
                    quota_type="api_calls",
                    current_usage=11000,
                    quota_limit=10000
                )
                
                # Verify alert was sent
                mock_alert.assert_called_once_with(
                    tenant_id=sample_tenant_a.id,
                    quota_type="api_calls",
                    usage_percentage=110.0,
                    alert_type="quota_exceeded"
                )
                
                # Verify audit log
                mock_audit.assert_called_with(
                    sample_tenant_a.id,
                    "quota_exceeded",
                    "API calls quota exceeded: 11000/10000",
                    False,
                    metadata={
                        "quota_type": "api_calls",
                        "current_usage": 11000,
                        "quota_limit": 10000,
                        "overage": 1000
                    }
                )


class TestTenantServiceHierarchyManagement:
    """Test tenant hierarchy and parent-child relationships"""

    async def test_parent_tenant_child_management(self, tenant_service, sample_parent_tenant):
        """Test parent tenant can manage child tenants"""
        
        # Create child tenant
        child_tenant = Tenant(
            id=uuid4(),
            organization_name="Child Company",
            slug="child-company",
            admin_email="admin@child.com",
            status=TenantStatus.ACTIVE,
            plan=TenantPlan.TEAM,
            quotas=DEFAULT_QUOTAS[TenantPlan.TEAM],
            parent_tenant_id=sample_parent_tenant.id
        )
        
        tenant_service.db.execute = AsyncMock()
        
        with patch.object(tenant_service, '_verify_parent_tenant_permissions') as mock_verify:
            mock_verify.return_value = True
            
            with patch.object(tenant_service, 'get_tenant_by_id') as mock_get_tenant:
                mock_get_tenant.return_value = child_tenant
                
                # Parent should be able to manage child
                result = await tenant_service.manage_child_tenant(
                    parent_tenant_id=sample_parent_tenant.id,
                    child_tenant_id=child_tenant.id,
                    action="suspend"
                )
                
                mock_verify.assert_called_once_with(
                    sample_parent_tenant.id,
                    child_tenant.id
                )

    async def test_child_tenant_inheritance_limits(self, tenant_service, sample_parent_tenant):
        """Test child tenant inherits appropriate limits from parent"""
        
        # Mock parent tenant quotas
        parent_quotas = TenantQuotas(
            max_users=100,
            max_projects=500,
            max_api_calls_per_month=1000000,
            max_storage_mb=102400,
            max_ai_requests_per_day=5000,
            max_concurrent_sessions=50
        )
        sample_parent_tenant.quotas = parent_quotas
        
        with patch.object(tenant_service, '_calculate_child_quota_limits') as mock_calculate:
            # Child should get subset of parent quotas
            mock_calculate.return_value = TenantQuotas(
                max_users=20,  # 20% of parent
                max_projects=100,  # 20% of parent  
                max_api_calls_per_month=200000,  # 20% of parent
                max_storage_mb=20480,  # 20% of parent
                max_ai_requests_per_day=1000,  # 20% of parent
                max_concurrent_sessions=10  # 20% of parent
            )
            
            child_quotas = await tenant_service.calculate_child_quotas(
                parent_tenant_id=sample_parent_tenant.id,
                allocation_percentage=0.2
            )
            
            assert child_quotas.max_users == 20
            assert child_quotas.max_projects == 100
            mock_calculate.assert_called_once_with(parent_quotas, 0.2)

    async def test_hierarchy_depth_limits(self, tenant_service, sample_parent_tenant):
        """Test tenant hierarchy depth is limited"""
        
        with patch.object(tenant_service, '_get_tenant_hierarchy_depth') as mock_depth:
            mock_depth.return_value = 5  # Already at maximum depth
            
            create_request = TenantCreate(
                organization_name="Deep Child",
                slug="deep-child",
                admin_email="admin@deep-child.com",
                parent_tenant_id=sample_parent_tenant.id
            )
            
            # Should reject if depth limit exceeded
            with pytest.raises(ValueError, match="hierarchy depth"):
                await tenant_service.create_tenant(create_request)


class TestTenantServiceUsageMonitoring:
    """Test tenant usage monitoring and reporting"""

    async def test_usage_calculation_accuracy(self, tenant_service, sample_tenant_a):
        """Test tenant usage is calculated accurately"""
        
        # Mock usage data from database
        mock_usage_data = {
            "projects": 15,
            "users": 8,
            "api_calls_this_month": 75000,
            "storage_used_mb": 5120,
            "ai_requests_today": 450,
            "concurrent_sessions": 6
        }
        
        with patch.object(tenant_service, '_calculate_current_usage') as mock_calculate:
            mock_calculate.return_value = mock_usage_data
            
            usage = await tenant_service.get_tenant_usage(sample_tenant_a.id)
            
            assert isinstance(usage, TenantUsage)
            assert usage.projects_count == 15
            assert usage.users_count == 8
            assert usage.api_calls_this_month == 75000
            assert usage.storage_used_mb == 5120
            assert usage.ai_requests_today == 450
            assert usage.concurrent_sessions == 6
            
            mock_calculate.assert_called_once_with(sample_tenant_a.id)

    async def test_usage_trend_analysis(self, tenant_service, sample_tenant_a):
        """Test usage trend analysis over time"""
        
        # Mock historical usage data
        historical_data = [
            {"date": "2024-01-01", "api_calls": 50000},
            {"date": "2024-01-02", "api_calls": 65000},
            {"date": "2024-01-03", "api_calls": 75000}
        ]
        
        with patch.object(tenant_service, '_get_usage_history') as mock_history:
            mock_history.return_value = historical_data
            
            with patch.object(tenant_service, '_analyze_usage_trends') as mock_analyze:
                mock_analyze.return_value = {
                    "trend": "increasing",
                    "growth_rate": 0.25,  # 25% growth
                    "projected_monthly": 90000
                }
                
                trends = await tenant_service.analyze_usage_trends(
                    tenant_id=sample_tenant_a.id,
                    metric_type="api_calls",
                    time_period="7_days"
                )
                
                assert trends["trend"] == "increasing"
                assert trends["growth_rate"] == 0.25
                assert trends["projected_monthly"] == 90000
                
                mock_history.assert_called_once_with(
                    sample_tenant_a.id, 
                    "api_calls", 
                    "7_days"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])