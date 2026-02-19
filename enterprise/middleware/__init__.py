"""
Enterprise Middleware

Request/response middleware for enterprise features.
"""

from typing import Callable, Any
from functools import wraps
import time


class TenantMiddleware:
    """
    Middleware to extract tenant information from requests.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract tenant from headers
        headers = dict(scope.get("headers", []))
        tenant_id = headers.get(b"x-tenant-id", b"").decode()
        
        # Add to scope
        scope["tenant_id"] = tenant_id
        
        await self.app(scope, receive, send)


class LicenseMiddleware:
    """
    Middleware to validate license for each request.
    """
    
    def __init__(self, app, license_manager):
        self.app = app
        self.license_manager = license_manager
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract tenant
        tenant_id = scope.get("tenant_id", "")
        
        if tenant_id:
            license = self.license_manager.get_license_by_tenant(tenant_id)
            if not license or not license.is_valid():
                # Return 403 Forbidden
                await self._send_403(send)
                return
        
        await self.app(scope, receive, send)
    
    async def _send_403(self, send):
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"error": "License invalid or expired"}',
        })


class RateLimitMiddleware:
    """
    Rate limiting middleware.
    """
    
    def __init__(self, app, max_requests: int = 100, window: int = 60):
        self.app = app
        self.max_requests = max_requests
        self.window = window
        self._requests = {}
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Get client ID
        client_id = scope.get("client", ("", 0))[0]
        
        now = time.time()
        
        # Check rate limit
        if client_id in self._requests:
            requests = [t for t in self._requests[client_id] if now - t < self.window]
            if len(requests) >= self.max_requests:
                await self._send_429(send)
                return
            self._requests[client_id] = requests + [now]
        else:
            self._requests[client_id] = [now]
        
        await self.app(scope, receive, send)
    
    async def _send_429(self, send):
        await send({
            "type": "http.response.start",
            "status": 429,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": b'{"error": "Rate limit exceeded"}',
        })


def require_permission(permission: str):
    """
    Decorator to require specific permission.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs or context
            user = kwargs.get("user")
            if not user:
                raise PermissionError(f"Permission '{permission}' required")
            
            if permission not in user.permissions:
                raise PermissionError(f"Permission '{permission}' required")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_tenant(func: Callable) -> Callable:
    """
    Decorator to require tenant context.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        tenant_id = kwargs.get("tenant_id")
        if not tenant_id:
            raise ValueError("Tenant ID required")
        
        return await func(*args, **kwargs)
    return wrapper
