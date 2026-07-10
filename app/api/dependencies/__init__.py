"""
Dependency injectors for API authentication and authorization.
"""

from typing import Optional, Annotated
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.auth import AuthService, TokenManager
from app.core.permissions import PermissionChecker, Permission, Role

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)
optional_security = HTTPBearer(auto_error=False)


class CurrentUser:
    """Current authenticated user data."""
    
    def __init__(
        self,
        user_id: str,
        username: str,
        roles: list[str],
        permissions: list[str]
    ):
        self.user_id = user_id
        self.username = username
        self.roles = roles
        self.permissions = permissions
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        return PermissionChecker.has_permission(self.roles, permission)
    
    def has_role(self, role: Role) -> bool:
        """Check if user has a specific role."""
        return role.value in self.roles


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> CurrentUser:
    """
    Get the current authenticated user from the JWT token.
    
    Args:
        credentials: HTTP bearer credentials
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
        )

    token = credentials.credentials
    
    try:
        payload = AuthService.verify_access_token(token)
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    username = payload.get("username")
    roles = payload.get("roles", [])
    permissions = payload.get("permissions", [])
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return CurrentUser(
        user_id=user_id,
        username=username,
        roles=roles,
        permissions=permissions
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> Optional[CurrentUser]:
    """
    Get the current user if authenticated, otherwise None.
    
    Args:
        credentials: HTTP bearer credentials (optional)
        
    Returns:
        Current user object or None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_permission(permission: Permission):
    """
    Dependency that requires a specific permission.
    
    Args:
        permission: Required permission
        
    Returns:
        Dependency function
    """
    async def check_permission(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.has_permission(permission):
            logger.warning(f"Permission denied for user {user.username}: {permission}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have permission: {permission}"
            )
        return user
    
    return check_permission


def require_role(role: Role):
    """
    Dependency that requires a specific role.
    
    Args:
        role: Required role
        
    Returns:
        Dependency function
    """
    async def check_role(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.has_role(role):
            logger.warning(f"Role denied for user {user.username}: {role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have role: {role}"
            )
        return user
    
    return check_role


def require_any_permission(*permissions: Permission):
    """
    Dependency that requires any of the specified permissions.
    
    Args:
        permissions: Required permissions
        
    Returns:
        Dependency function
    """
    async def check_permissions(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not PermissionChecker.has_any_permission(user.roles, list(permissions)):
            logger.warning(f"No required permission for user {user.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have required permissions"
            )
        return user
    
    return check_permissions


def require_all_permissions(*permissions: Permission):
    """
    Dependency that requires all specified permissions.
    
    Args:
        permissions: Required permissions
        
    Returns:
        Dependency function
    """
    async def check_permissions(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not PermissionChecker.has_all_permissions(user.roles, list(permissions)):
            logger.warning(f"Missing required permissions for user {user.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have all required permissions"
            )
        return user
    
    return check_permissions


class RateLimitChecker:
    """Check and enforce rate limiting."""
    
    _request_counts = {}
    
    @staticmethod
    def check_rate_limit(
        user_id: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if user is within rate limit.
        
        Args:
            user_id: User ID
            max_requests: Max requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if within limit
        """
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        key = (user_id, window_seconds)
        
        if key not in RateLimitChecker._request_counts:
            RateLimitChecker._request_counts[key] = []
        
        # Remove old requests outside the window
        window_start = now - timedelta(seconds=window_seconds)
        RateLimitChecker._request_counts[key] = [
            ts for ts in RateLimitChecker._request_counts[key]
            if ts > window_start
        ]
        
        # Check limit
        if len(RateLimitChecker._request_counts[key]) >= max_requests:
            return False
        
        # Add current request
        RateLimitChecker._request_counts[key].append(now)
        return True


def check_rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    Dependency for rate limiting.
    
    Args:
        max_requests: Max requests allowed
        window_seconds: Time window in seconds
        
    Returns:
        Dependency function
    """
    async def rate_limit_check(user: CurrentUser = Depends(get_current_user)):
        if not RateLimitChecker.check_rate_limit(user.user_id, max_requests, window_seconds):
            logger.warning(f"Rate limit exceeded for user {user.username}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        return user
    
    return rate_limit_check
