"""
Enterprise Tenant Module

Multi-tenant management and isolation.
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class TenantConfig:
    """Tenant configuration"""
    id: str
    name: str
    llm_provider: str
    llm_model: str
    max_users: int
    max_conversations: int
    features: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_feature_enabled(self, feature: str) -> bool:
        return self.features.get(feature, False)


class TenantManager:
    """Manage multiple tenants"""
    
    def __init__(self):
        self._tenants: dict[str, TenantConfig] = {}
    
    def create_tenant(self, config: TenantConfig) -> None:
        """Create a new tenant"""
        self._tenants[config.id] = config
    
    def get_tenant(self, tenant_id: str) -> Optional[TenantConfig]:
        """Get tenant by ID"""
        return self._tenants.get(tenant_id)
    
    def list_tenants(self) -> list[TenantConfig]:
        """List all tenants"""
        return list(self._tenants.values())
    
    def update_tenant(self, tenant_id: str, config: TenantConfig) -> bool:
        """Update tenant configuration"""
        if tenant_id in self._tenants:
            self._tenants[tenant_id] = config
            return True
        return False
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete a tenant"""
        if tenant_id in self._tenants:
            del self._tenants[tenant_id]
            return True
        return False


# Global instance
_tenant_manager = TenantManager()


def get_tenant_manager() -> TenantManager:
    """Get global tenant manager"""
    return _tenant_manager
