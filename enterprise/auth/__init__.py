"""
Enterprise Authentication Module

Multi-tenant authentication and authorization.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Tenant:
    """Tenant entity"""
    id: str
    name: str
    created_at: datetime
    settings: dict
    
    def is_active(self) -> bool:
        return self.settings.get("active", True)


@dataclass 
class User:
    """User entity"""
    id: str
    tenant_id: str
    name: str
    email: str
    permissions: list[str]
    created_at: datetime
    
    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions


class AuthManager:
    """Multi-tenant authentication manager"""
    
    def __init__(self):
        self._tenants: dict[str, Tenant] = {}
        self._users: dict[str, User] = {}
    
    def register_tenant(self, tenant: Tenant) -> None:
        """Register a new tenant"""
        self._tenants[tenant.id] = tenant
    
    def register_user(self, user: User) -> None:
        """Register a new user"""
        self._users[user.id] = user
    
    def authenticate(self, user_id: str, tenant_id: str) -> Optional[User]:
        """Authenticate user and verify tenant"""
        user = self._users.get(user_id)
        if not user:
            return None
        
        if user.tenant_id != tenant_id:
            return None
            
        tenant = self._tenants.get(tenant_id)
        if not tenant or not tenant.is_active():
            return None
            
        return user
    
    def check_permission(self, user: User, permission: str) -> bool:
        """Check if user has permission"""
        return user.has_permission(permission)


# Global instance
_auth_manager = AuthManager()


def get_auth_manager() -> AuthManager:
    """Get global auth manager"""
    return _auth_manager
