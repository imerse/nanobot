"""
Enterprise License Module

License management and validation.
"""

from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import secrets


class LicenseType(Enum):
    """License type"""
    TRIAL = "trial"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class LicenseStatus(Enum):
    """License status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass
class License:
    """License entity"""
    id: str
    tenant_id: str
    license_type: LicenseType
    status: LicenseStatus
    max_users: int
    max_conversations: int
    issued_at: datetime
    expires_at: datetime
    features: dict = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if license is valid"""
        if self.status != LicenseStatus.ACTIVE:
            return False
        return datetime.now() < self.expires_at
    
    def days_remaining(self) -> int:
        """Get days remaining"""
        if not self.is_valid():
            return 0
        delta = self.expires_at - datetime.now()
        return max(0, delta.days)
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if feature is enabled"""
        return self.features.get(feature, False)


class LicenseManager:
    """License management"""
    
    def __init__(self):
        self._licenses: dict[str, License] = {}
        self._license_keys: dict[str, str] = {}  # key -> license_id
    
    def generate_license_key(self, prefix: str = "ENT") -> str:
        """Generate a new license key"""
        random_part = secrets.token_hex(16)
        return f"{prefix}-{random_part.upper()}"
    
    def create_license(
        self,
        tenant_id: str,
        license_type: LicenseType,
        max_users: int,
        max_conversations: int,
        days: int = 365,
        features: dict = None
    ) -> tuple[License, str]:
        """Create a new license"""
        license_id = secrets.token_hex(8)
        license_key = self.generate_license_key(license_type.value[:3].upper())
        
        license = License(
            id=license_id,
            tenant_id=tenant_id,
            license_type=license_type,
            status=LicenseStatus.ACTIVE,
            max_users=max_users,
            max_conversations=max_conversations,
            issued_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=days),
            features=features or {}
        )
        
        self._licenses[license_id] = license
        self._license_keys[license_key] = license_id
        
        return license, license_key
    
    def activate_license(self, license_key: str) -> Optional[License]:
        """Activate a license by key"""
        license_id = self._license_keys.get(license_key)
        if not license_id:
            return None
        
        license = self._licenses.get(license_id)
        if not license:
            return None
        
        if license.status == LicenseStatus.EXPIRED:
            license.status = LicenseStatus.ACTIVE
        
        return license
    
    def get_license(self, license_id: str) -> Optional[License]:
        """Get license by ID"""
        return self._licenses.get(license_id)
    
    def get_license_by_tenant(self, tenant_id: str) -> Optional[License]:
        """Get license for a tenant"""
        for license in self._licenses.values():
            if license.tenant_id == tenant_id and license.is_valid():
                return license
        return None
    
    def validate_usage(self, license_id: str, user_count: int, conversation_count: int) -> bool:
        """Validate usage against license limits"""
        license = self._licenses.get(license_id)
        if not license or not license.is_valid():
            return False
        
        if user_count > license.max_users:
            return False
        if conversation_count > license.max_conversations:
            return False
        
        return True
    
    def revoke_license(self, license_id: str) -> bool:
        """Revoke a license"""
        license = self._licenses.get(license_id)
        if license:
            license.status = LicenseStatus.REVOKED
            return True
        return False
    
    def list_licenses(self) -> list[License]:
        """List all licenses"""
        return list(self._licenses.values())


# Global instance
_license_manager = LicenseManager()


def get_license_manager() -> LicenseManager:
    """Get global license manager"""
    return _license_manager
