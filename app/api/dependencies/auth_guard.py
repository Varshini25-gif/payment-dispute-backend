"""
Auth guard utilities for protecting API endpoints.
"""

from typing import Optional, List
from functools import wraps
import logging

from fastapi import HTTPException, status
from app.core.permissions import Permission, Role, PermissionChecker

logger = logging.getLogger(__name__)


class AuthGuard:
    """Guard for protecting API endpoints."""
    
    @staticmethod
    def require_authenticated(func):
        """Decorator to require authentication."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            return await func(*args, **kwargs)
        return wrapper
    
    @staticmethod
    def require_permission(permission: Permission):
        """
        Decorator to require a specific permission.
        
        Args:
            permission: Required permission
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user = kwargs.get("current_user")
                if not user or not user.has_permission(permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission required: {permission}"
                    )
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def require_role(role: Role):
        """
        Decorator to require a specific role.
        
        Args:
            role: Required role
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user = kwargs.get("current_user")
                if not user or not user.has_role(role):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Role required: {role}"
                    )
                return await func(*args, **kwargs)
            return wrapper
        return decorator


class EndpointSecurity:
    """Define security requirements for endpoints."""
    
    def __init__(self):
        self.required_permissions: List[Permission] = []
        self.required_roles: List[Role] = []
        self.allow_anonymous = False
        self.rate_limit_enabled = False
        self.rate_limit_requests = 100
        self.rate_limit_seconds = 60
    
    def add_permission(self, permission: Permission) -> "EndpointSecurity":
        """Add required permission."""
        self.required_permissions.append(permission)
        return self
    
    def add_permissions(self, *permissions: Permission) -> "EndpointSecurity":
        """Add multiple required permissions."""
        self.required_permissions.extend(permissions)
        return self
    
    def add_role(self, role: Role) -> "EndpointSecurity":
        """Add required role."""
        self.required_roles.append(role)
        return self
    
    def add_roles(self, *roles: Role) -> "EndpointSecurity":
        """Add multiple required roles."""
        self.required_roles.extend(roles)
        return self
    
    def set_anonymous(self, allow: bool = True) -> "EndpointSecurity":
        """Allow anonymous access."""
        self.allow_anonymous = allow
        return self
    
    def enable_rate_limiting(
        self,
        requests: int = 100,
        seconds: int = 60
    ) -> "EndpointSecurity":
        """Enable rate limiting."""
        self.rate_limit_enabled = True
        self.rate_limit_requests = requests
        self.rate_limit_seconds = seconds
        return self
    
    def validate_user(self, user) -> bool:
        """
        Validate user against security requirements.
        
        Args:
            user: Current user
            
        Returns:
            True if user meets requirements
        """
        if self.allow_anonymous and not user:
            return True
        
        if not user:
            return False
        
        # Check roles
        if self.required_roles:
            if not any(user.has_role(role) for role in self.required_roles):
                return False
        
        # Check permissions (all must be present)
        if self.required_permissions:
            if not all(user.has_permission(perm) for perm in self.required_permissions):
                return False
        
        return True


class AuditableEndpoint:
    """Configuration for auditable endpoints."""
    
    def __init__(
        self,
        action: str,
        resource_type: str,
        log_changes: bool = True
    ):
        self.action = action
        self.resource_type = resource_type
        self.log_changes = log_changes
    
    def create_audit_entry(self, user, request_data, response_data):
        """Create an audit log entry."""
        return {
            "action": self.action,
            "resource_type": self.resource_type,
            "user_id": user.user_id if user else None,
            "username": user.username if user else None,
            "timestamp": datetime.utcnow(),
            "request_data": request_data if self.log_changes else None,
            "response_data": response_data if self.log_changes else None,
        }


# Pre-defined security configurations
SECURITY_CONFIGS = {
    "public": EndpointSecurity().set_anonymous(True),
    "authenticated": EndpointSecurity(),
    "admin_only": EndpointSecurity().add_role(Role.ADMIN),
    "manager_plus": EndpointSecurity().add_roles(Role.ADMIN, Role.MANAGER),
    "read_disputes": EndpointSecurity().add_permission(Permission.READ_DISPUTE),
    "create_disputes": EndpointSecurity().add_permission(Permission.CREATE_DISPUTE),
    "manage_disputes": EndpointSecurity().add_permissions(
        Permission.CREATE_DISPUTE,
        Permission.UPDATE_DISPUTE
    ),
}


from datetime import datetime
