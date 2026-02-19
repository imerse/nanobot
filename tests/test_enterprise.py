"""
Enterprise Module Tests

Tests for Phase 2 enterprise features: Auth, Tenant, License, Storage.
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enterprise.auth import AuthManager, Tenant, User
from enterprise.tenant import TenantManager, TenantConfig
from enterprise.license import LicenseManager, LicenseType, LicenseStatus


class TestTenantManager:
    """Tenant Manager Tests"""
    
    def test_create_tenant(self):
        """Test creating a tenant"""
        tm = TenantManager()
        config = TenantConfig(
            id="test_company",
            name="Test Company",
            llm_provider="openai",
            llm_model="gpt-4",
            max_users=50,
            max_conversations=500
        )
        tm.create_tenant(config)
        
        tenant = tm.get_tenant("test_company")
        assert tenant is not None
        assert tenant.name == "Test Company"
        assert tenant.max_users == 50
    
    def test_get_tenant_not_found(self):
        """Test getting non-existent tenant"""
        tm = TenantManager()
        tenant = tm.get_tenant("nonexistent")
        assert tenant is None
    
    def test_update_tenant(self):
        """Test updating tenant"""
        tm = TenantManager()
        config = TenantConfig(
            id="test_company",
            name="Test Company",
            llm_provider="openai",
            llm_model="gpt-4",
            max_users=50,
            max_conversations=500
        )
        tm.create_tenant(config)
        
        # Update
        new_config = TenantConfig(
            id="test_company",
            name="Updated Company",
            llm_provider="openai",
            llm_model="gpt-4",
            max_users=100,
            max_conversations=1000
        )
        result = tm.update_tenant("test_company", new_config)
        assert result is True
        
        tenant = tm.get_tenant("test_company")
        assert tenant.name == "Updated Company"
        assert tenant.max_users == 100
    
    def test_delete_tenant(self):
        """Test deleting tenant"""
        tm = TenantManager()
        config = TenantConfig(
            id="test_company",
            name="Test Company",
            llm_provider="openai",
            llm_model="gpt-4",
            max_users=50,
            max_conversations=500
        )
        tm.create_tenant(config)
        
        result = tm.delete_tenant("test_company")
        assert result is True
        assert tm.get_tenant("test_company") is None


class TestAuthManager:
    """Auth Manager Tests"""
    
    def test_register_tenant(self):
        """Test registering a tenant"""
        am = AuthManager()
        tenant = Tenant(
            id="test_tenant",
            name="Test Tenant",
            created_at=datetime.now(),
            settings={"active": True}
        )
        am.register_tenant(tenant)
        
        # Verify by attempting auth
        user = User(
            id="user_001",
            tenant_id="test_tenant",
            name="Test User",
            email="test@example.com",
            permissions=["read"],
            created_at=datetime.now()
        )
        am.register_user(user)
        
        authenticated = am.authenticate("user_001", "test_tenant")
        assert authenticated is not None
        assert authenticated.name == "Test User"
    
    def test_authenticate_invalid_user(self):
        """Test authenticating invalid user"""
        am = AuthManager()
        result = am.authenticate("invalid_user", "invalid_tenant")
        assert result is None
    
    def test_authenticate_inactive_tenant(self):
        """Test authenticating with inactive tenant"""
        am = AuthManager()
        
        # Register tenant as inactive
        tenant = Tenant(
            id="inactive_tenant",
            name="Inactive Tenant",
            created_at=datetime.now(),
            settings={"active": False}
        )
        am.register_tenant(tenant)
        
        user = User(
            id="user_001",
            tenant_id="inactive_tenant",
            name="Test User",
            email="test@example.com",
            permissions=[],
            created_at=datetime.now()
        )
        am.register_user(user)
        
        result = am.authenticate("user_001", "inactive_tenant")
        assert result is None
    
    def test_check_permission(self):
        """Test permission checking"""
        am = AuthManager()
        
        user = User(
            id="user_001",
            tenant_id="test_tenant",
            name="Test User",
            email="test@example.com",
            permissions=["read", "write"],
            created_at=datetime.now()
        )
        
        assert am.check_permission(user, "read") is True
        assert am.check_permission(user, "write") is True
        assert am.check_permission(user, "admin") is False


class TestLicenseManager:
    """License Manager Tests"""
    
    def test_create_license(self):
        """Test creating a license"""
        lm = LicenseManager()
        license, key = lm.create_license(
            tenant_id="test_tenant",
            license_type=LicenseType.STANDARD,
            max_users=10,
            max_conversations=1000,
            days=30
        )
        
        assert license is not None
        assert key is not None
        assert license.tenant_id == "test_tenant"
        assert license.license_type == LicenseType.STANDARD
        assert license.max_users == 10
        assert license.is_valid() is True
    
    def test_activate_license(self):
        """Test activating a license"""
        lm = LicenseManager()
        license, key = lm.create_license(
            tenant_id="test_tenant",
            license_type=LicenseType.TRIAL,
            max_users=5,
            max_conversations=100,
            days=14
        )
        
        activated = lm.activate_license(key)
        assert activated is not None
        assert activated.is_valid() is True
    
    def test_get_license_by_tenant(self):
        """Test getting license by tenant"""
        lm = LicenseManager()
        license, _ = lm.create_license(
            tenant_id="test_tenant",
            license_type=LicenseType.PROFESSIONAL,
            max_users=50,
            max_conversations=5000,
            days=365
        )
        
        found = lm.get_license_by_tenant("test_tenant")
        assert found is not None
        assert found.license_type == LicenseType.PROFESSIONAL
    
    def test_validate_usage_within_limit(self):
        """Test usage validation within limits"""
        lm = LicenseManager()
        license, _ = lm.create_license(
            tenant_id="test_tenant",
            license_type=LicenseType.STANDARD,
            max_users=10,
            max_conversations=100,
            days=30
        )
        
        result = lm.validate_usage(license.id, 5, 50)
        assert result is True
    
    def test_validate_usage_exceeds_limit(self):
        """Test usage validation exceeding limits"""
        lm = LicenseManager()
        license, _ = lm.create_license(
            tenant_id="test_tenant",
            license_type=LicenseType.STANDARD,
            max_users=10,
            max_conversations=100,
            days=30
        )
        
        # Exceeds user limit
        result = lm.validate_usage(license.id, 15, 50)
        assert result is False
        
        # Exceeds conversation limit
        result = lm.validate_usage(license.id, 5, 200)
        assert result is False
    
    def test_revoke_license(self):
        """Test revoking a license"""
        lm = LicenseManager()
        license, _ = lm.create_license(
            tenant_id="test_tenant",
            license_type=LicenseType.STANDARD,
            max_users=10,
            max_conversations=100,
            days=30
        )
        
        result = lm.revoke_license(license.id)
        assert result is True
        
        # Check license is revoked
        lic = lm.get_license(license.id)
        assert lic.status == LicenseStatus.REVOKED
        assert lic.is_valid() is False
    
    def test_list_licenses(self):
        """Test listing all licenses"""
        lm = LicenseManager()
        lm.create_license("tenant1", LicenseType.TRIAL, 5, 100, 14)
        lm.create_license("tenant2", LicenseType.STANDARD, 10, 1000, 30)
        lm.create_license("tenant3", LicenseType.PROFESSIONAL, 50, 10000, 365)
        
        licenses = lm.list_licenses()
        assert len(licenses) == 3


class TestLicense:
    """License Entity Tests"""
    
    def test_is_valid_active(self):
        """Test valid active license"""
        from enterprise.license import License
        license = License(
            id="test",
            tenant_id="tenant",
            license_type=LicenseType.STANDARD,
            status=LicenseStatus.ACTIVE,
            max_users=10,
            max_conversations=100,
            issued_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        assert license.is_valid() is True
    
    def test_is_valid_expired(self):
        """Test expired license"""
        from enterprise.license import License
        license = License(
            id="test",
            tenant_id="tenant",
            license_type=LicenseType.STANDARD,
            status=LicenseStatus.ACTIVE,
            max_users=10,
            max_conversations=100,
            issued_at=datetime.now() - timedelta(days=60),
            expires_at=datetime.now() - timedelta(days=30)
        )
        assert license.is_valid() is False
    
    def test_is_valid_revoked(self):
        """Test revoked license"""
        from enterprise.license import License
        license = License(
            id="test",
            tenant_id="tenant",
            license_type=LicenseType.STANDARD,
            status=LicenseStatus.REVOKED,
            max_users=10,
            max_conversations=100,
            issued_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        assert license.is_valid() is False
    
    def test_days_remaining(self):
        """Test days remaining calculation"""
        from enterprise.license import License
        license = License(
            id="test",
            tenant_id="tenant",
            license_type=LicenseType.STANDARD,
            status=LicenseStatus.ACTIVE,
            max_users=10,
            max_conversations=100,
            issued_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=15)
        )
        days = license.days_remaining()
        assert 14 <= days <= 15
    
    def test_is_feature_enabled(self):
        """Test feature flag checking"""
        from enterprise.license import License
        license = License(
            id="test",
            tenant_id="tenant",
            license_type=LicenseType.PROFESSIONAL,
            status=LicenseStatus.ACTIVE,
            max_users=10,
            max_conversations=100,
            issued_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30),
            features={"vector_search": True, "custom_branding": False}
        )
        assert license.is_feature_enabled("vector_search") is True
        assert license.is_feature_enabled("custom_branding") is False
        assert license.is_feature_enabled("nonexistent") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
