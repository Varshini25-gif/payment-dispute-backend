"""
Authentication API routes.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.auth import AuthService, TokenManager
from app.core.security import PasswordManager
from app.core.permissions import Role
from app.api.dependencies import (
    get_current_user,
    CurrentUser,
    require_permission
)
from app.core.permissions import Permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models
class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ChangePasswordRequest(BaseModel):
    """Change password request model."""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class TokenInfo(BaseModel):
    """Token information model."""
    user_id: str
    username: str
    roles: list[str]
    permissions: list[str]
    expires_at: datetime
    issued_at: datetime


class UserInfo(BaseModel):
    """User information model."""
    user_id: str
    username: str
    roles: list[str]
    permissions: list[str]


# Demo in-memory user database (replace with actual database)
DEMO_USERS = {
    "admin": {
        "user_id": "1",
        "username": "admin",
        "password_hash": PasswordManager.hash_password("Admin@123"),
        "roles": [Role.ADMIN.value],
        "permissions": []
    },
    "manager": {
        "user_id": "2",
        "username": "manager",
        "password_hash": PasswordManager.hash_password("Manager@123"),
        "roles": [Role.MANAGER.value],
        "permissions": []
    },
    "analyst": {
        "user_id": "3",
        "username": "analyst",
        "password_hash": PasswordManager.hash_password("Analyst@123"),
        "roles": [Role.ANALYST.value],
        "permissions": []
    },
}


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(request: LoginRequest):
    """
    Authenticate user and return tokens.
    
    Args:
        request: Login credentials
        
    Returns:
        Login response with tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    # Find user (replace with database lookup)
    user = DEMO_USERS.get(request.username)
    if not user:
        logger.warning(f"Login attempt for non-existent user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not AuthService.authenticate_user(
        request.username,
        request.password,
        user["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create tokens
    tokens = AuthService.create_tokens(
        user_id=user["user_id"],
        username=user["username"],
        roles=user["roles"],
        permissions=user["permissions"]
    )
    
    logger.info(f"User logged in: {request.username}")
    
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=30 * 60,  # 30 minutes
        user={
            "user_id": user["user_id"],
            "username": user["username"],
            "roles": user["roles"]
        }
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Generate a new access token from a refresh token.
    
    Args:
        request: Refresh token request
        
    Returns:
        New access token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        new_access_token = AuthService.refresh_access_token(request.refresh_token)
        
        return RefreshTokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=30 * 60
        )
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: CurrentUser = Depends()):
    """
    Logout user (blacklist token).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # Get token from header (you need to extract it)
    logger.info(f"User logged out: {current_user.username}")
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: CurrentUser = Depends()):
    """
    Get information about the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
    """
    return UserInfo(
        user_id=current_user.user_id,
        username=current_user.username,
        roles=current_user.roles,
        permissions=current_user.permissions
    )


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser = Depends()
):
    """
    Change user password.
    
    Args:
        request: Password change request
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # Get user from database
    user = DEMO_USERS.get(current_user.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify old password
    if not PasswordManager.verify_password(request.old_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid current password"
        )
    
    # Validate new password
    is_valid, error = PasswordManager.validate_password_policy(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Update password (in real app, update in database)
    user["password_hash"] = PasswordManager.hash_password(request.new_password)
    
    logger.info(f"Password changed for user: {current_user.username}")
    
    return {"message": "Password changed successfully"}


@router.get("/token-info", response_model=TokenInfo)
async def get_token_info(current_user: CurrentUser = Depends()):
    """
    Get information about the current token.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Token information
    """
    # Return token info from current_user
    return TokenInfo(
        user_id=current_user.user_id,
        username=current_user.username,
        roles=current_user.roles,
        permissions=current_user.permissions,
        expires_at=datetime.utcnow(),  # Should be extracted from token
        issued_at=datetime.utcnow()    # Should be extracted from token
    )


# Protected endpoint examples
@router.get("/admin-only")
async def admin_only_endpoint(
    current_user: CurrentUser = Depends(require_permission(Permission.MANAGE_SYSTEM))
):
    """
    Admin only endpoint example.
    
    Args:
        current_user: Current authenticated user with admin permission
        
    Returns:
        Admin data
    """
    return {
        "message": "This is an admin only endpoint",
        "user": current_user.username
    }


@router.get("/manager-data")
async def manager_data_endpoint(
    current_user: CurrentUser = Depends(require_permission(Permission.MANAGE_ROUTING))
):
    """
    Manager data endpoint example.
    
    Args:
        current_user: Current authenticated user with manager permission
        
    Returns:
        Manager data
    """
    return {
        "message": "This is a manager endpoint",
        "user": current_user.username,
        "role": current_user.roles[0] if current_user.roles else None
    }
