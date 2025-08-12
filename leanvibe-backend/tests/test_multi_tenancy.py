"""
Tests for multi-tenancy implementation in LeanVibe Enterprise SaaS Platform
Validates tenant isolation, quota management, and data security
"""

import pytest
from uuid import UUID
from datetime import datetime, timedelta

from app.models.tenant_models import (
    Tenant, TenantCreate, TenantUpdate, TenantUsage, TenantStatus, TenantPlan, DEFAULT_QUOTAS
)


class TestTenantModels:
    """Test tenant model validation and logic"""
    
    def test_create_tenant_success(self):
        """Test successful tenant creation"""
        tenant_data = TenantCreate(
            organization_name="Acme Corporation",
            display_name="Acme Corp",
            slug="acme-corp",
            admin_email="admin@acme.com",
            plan=TenantPlan.TEAM
        )
        
        # Test tenant creation data validation
        assert tenant_data.organization_name == "Acme Corporation"
        assert tenant_data.slug == "acme-corp"
        assert tenant_data.plan == TenantPlan.TEAM
        
        # Create tenant instance using the data
        tenant = Tenant(
            organization_name=tenant_data.organization_name,
            display_name=tenant_data.display_name,
            slug=tenant_data.slug,
            admin_email=tenant_data.admin_email,
            plan=tenant_data.plan,
            quotas=DEFAULT_QUOTAS[tenant_data.plan],
            trial_ends_at=datetime.utcnow() + timedelta(days=14)
        )
        
        # Validate tenant properties
        assert tenant.organization_name == "Acme Corporation"
        assert tenant.slug == "acme-corp"
        assert tenant.plan == TenantPlan.TEAM
        assert tenant.status == TenantStatus.TRIAL
        assert tenant.quotas.max_users == 10  # Team plan quota
        assert tenant.trial_ends_at > datetime.utcnow()
    
    def test_tenant_quota_validation(self):
        """Test tenant quota validation"""
        # Test Developer plan quotas
        dev_quotas = DEFAULT_QUOTAS[TenantPlan.DEVELOPER]
        assert dev_quotas.max_users == 1
        assert dev_quotas.max_projects == 5
        assert dev_quotas.max_api_calls_per_month == 10000
        
        # Test Team plan quotas
        team_quotas = DEFAULT_QUOTAS[TenantPlan.TEAM]
        assert team_quotas.max_users == 10
        assert team_quotas.max_projects == 50
        assert team_quotas.max_api_calls_per_month == 100000
        
        # Test Enterprise plan quotas
        enterprise_quotas = DEFAULT_QUOTAS[TenantPlan.ENTERPRISE]
        assert enterprise_quotas.max_users == 999999  # Unlimited
        assert enterprise_quotas.max_projects == 999999  # Unlimited
    
    def test_invalid_tenant_slug(self):
        """Test validation of tenant slug format"""
        invalid_slugs = [
            "INVALID-CAPS",  # Should be lowercase
            "invalid_underscore",  # Should use hyphens
            "invalid space",  # Should not contain spaces
            "invalid@symbol",  # Should not contain special chars
            "a",  # Too short
            "a" * 51  # Too long
        ]
        
        for slug in invalid_slugs:
            with pytest.raises(ValueError):
                TenantCreate(
                    organization_name="Test",
                    slug=slug,
                    admin_email="test@example.com"
                )
    
    def test_tenant_status_transitions(self):
        """Test valid tenant status transitions"""
        tenant = Tenant(
            organization_name="Test Corp",
            slug="test-corp",
            admin_email="test@example.com",
            quotas=DEFAULT_QUOTAS[TenantPlan.DEVELOPER]
        )
        
        # Initial status should be TRIAL
        assert tenant.status == TenantStatus.TRIAL
        
        # Valid transitions from TRIAL
        valid_from_trial = [TenantStatus.ACTIVE, TenantStatus.CANCELLED]
        for status in valid_from_trial:
            tenant.status = status
            assert tenant.status == status
    
    def test_quota_enforcement(self):
        """Test quota enforcement logic"""
        tenant_usage = TenantUsage(
            tenant_id=UUID("12345678-1234-5678-9012-123456789012"),
            users_count=5,
            projects_count=10,
            api_calls_this_month=5000
        )
        
        dev_quotas = DEFAULT_QUOTAS[TenantPlan.DEVELOPER]
        
        # Check quota violations
        assert tenant_usage.users_count > dev_quotas.max_users  # Should exceed
        assert tenant_usage.projects_count > dev_quotas.max_projects  # Should exceed
        assert tenant_usage.api_calls_this_month < dev_quotas.max_api_calls_per_month  # Should be within
    
    def test_tenant_hierarchy(self):
        """Test tenant hierarchy support"""
        parent_tenant = Tenant(
            organization_name="Parent Corp",
            slug="parent-corp", 
            admin_email="admin@parent.com",
            plan=TenantPlan.ENTERPRISE,
            quotas=DEFAULT_QUOTAS[TenantPlan.ENTERPRISE]
        )
        
        child_tenant = Tenant(
            organization_name="Child Division",
            slug="child-division",
            admin_email="admin@child.com",
            plan=TenantPlan.TEAM,
            parent_tenant_id=parent_tenant.id,
            quotas=DEFAULT_QUOTAS[TenantPlan.TEAM]
        )
        
        # Validate hierarchy relationship
        assert child_tenant.parent_tenant_id == parent_tenant.id
        assert parent_tenant.parent_tenant_id is None
    
    def test_data_residency_compliance(self):
        """Test data residency configuration"""
        from app.models.tenant_models import TenantDataResidency
        
        tenant = Tenant(
            organization_name="EU Company",
            slug="eu-company",
            admin_email="admin@eucompany.eu",
            data_residency=TenantDataResidency.EU,
            quotas=DEFAULT_QUOTAS[TenantPlan.TEAM]
        )
        
        assert tenant.data_residency == TenantDataResidency.EU
        
        # Test all supported regions
        supported_regions = [
            TenantDataResidency.US,
            TenantDataResidency.EU,
            TenantDataResidency.UK,
            TenantDataResidency.CANADA,
            TenantDataResidency.AUSTRALIA
        ]
        
        for region in supported_regions:
            tenant.data_residency = region
            assert tenant.data_residency == region


class TestTenantMiddleware:
    """Test tenant middleware functionality"""
    
    def test_tenant_context_isolation(self):
        """Test that tenant context is properly isolated"""
        from app.middleware.tenant_middleware import TenantContext
        
        context = TenantContext()
        
        # Initial state should be empty
        assert context.tenant is None
        assert context.user_id is None
        assert context.tenant_id is None
        assert not context.is_valid()
        
        # Set tenant context
        tenant = Tenant(
            organization_name="Test",
            slug="test",
            admin_email="test@example.com",
            status=TenantStatus.ACTIVE,  # Required for is_valid() to return True
            quotas=DEFAULT_QUOTAS[TenantPlan.DEVELOPER]
        )
        
        context.tenant = tenant
        context.user_id = UUID("12345678-1234-5678-9012-123456789012")
        
        # Validate context
        assert context.tenant == tenant
        assert context.tenant_id == tenant.id
        assert context.user_id is not None
        assert context.is_valid()
        
        # Clear context
        context.clear()
        assert context.tenant is None
        assert context.user_id is None
        assert not context.is_valid()
    
    def test_subdomain_extraction(self):
        """Test tenant extraction from subdomain"""
        test_cases = [
            ("acme.leanvibe.ai", "acme"),
            ("test-corp.leanvibe.ai", "test-corp"), 
            ("www.leanvibe.ai", None),  # Skip www
            ("api.leanvibe.ai", None),  # Skip api
            ("localhost:8765", None),   # Skip localhost
        ]
        
        for host, expected_slug in test_cases:
            if "." in host:
                subdomain = host.split(".")[0]
                if subdomain not in ["www", "api", "admin", "app", "staging", "localhost"]:
                    assert subdomain == expected_slug
                else:
                    assert expected_slug is None


class TestTenantSecurity:
    """Test tenant security and data isolation"""
    
    def test_tenant_data_isolation(self):
        """Test that tenant data is properly isolated"""
        tenant_a = Tenant(
            organization_name="Company A",
            slug="company-a",
            admin_email="admin@a.com",
            quotas=DEFAULT_QUOTAS[TenantPlan.DEVELOPER]
        )
        
        tenant_b = Tenant(
            organization_name="Company B", 
            slug="company-b",
            admin_email="admin@b.com",
            quotas=DEFAULT_QUOTAS[TenantPlan.TEAM]
        )
        
        # Tenants should have different IDs
        assert tenant_a.id != tenant_b.id
        assert tenant_a.slug != tenant_b.slug
        assert tenant_a.admin_email != tenant_b.admin_email
    
    def test_tenant_configuration_isolation(self):
        """Test tenant-specific configuration isolation"""
        tenant = Tenant(
            organization_name="Custom Corp",
            slug="custom-corp", 
            admin_email="admin@custom.com",
            quotas=DEFAULT_QUOTAS[TenantPlan.ENTERPRISE]
        )
        
        # Set custom configuration
        tenant.configuration.branding["primary_color"] = "#FF6B35"
        tenant.configuration.features["advanced_analytics"] = True
        tenant.configuration.security_settings["require_2fa"] = True
        
        # Validate configuration isolation
        assert tenant.configuration.branding["primary_color"] == "#FF6B35"
        assert tenant.configuration.features["advanced_analytics"] is True
        assert tenant.configuration.security_settings["require_2fa"] is True
    
    def test_encryption_key_management(self):
        """Test tenant-specific encryption key management"""
        tenant = Tenant(
            organization_name="Secure Corp",
            slug="secure-corp",
            admin_email="admin@secure.com", 
            quotas=DEFAULT_QUOTAS[TenantPlan.ENTERPRISE],
            encryption_key_id="key-123-456-789"
        )
        
        assert tenant.encryption_key_id == "key-123-456-789"
        
        # Each tenant should have unique encryption
        other_tenant = Tenant(
            organization_name="Other Corp",
            slug="other-corp",
            admin_email="admin@other.com",
            quotas=DEFAULT_QUOTAS[TenantPlan.TEAM],
            encryption_key_id="key-987-654-321"
        )
        
        assert tenant.encryption_key_id != other_tenant.encryption_key_id


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])