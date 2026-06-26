"""
Authentication logic for user validation and token generation.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from jose import JWTError
from app.core.security import (
    JWTManager,
    PasswordManager,
    TokenBlacklist,
    SecretManager
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    def authenticate_user(
        username: str,
        password: str,
        stored_hash: str
    ) -> bool:
        """
        Authenticate a user by verifying password.
        
        Args:
            username: Username (for logging)
            password: Plain text password
            stored_hash: Stored password hash
            
        Returns:
            True if authentication successful
        """
        if not PasswordManager.verify_password(password, stored_hash):
            logger.warning(f"Failed authentication attempt for user: {username}")
            return False
        
        logger.info(f"User authenticated: {username}")
        return True
    
    @staticmethod
    def create_tokens(
        user_id: str,
        username: str,
        roles: list[str],
        permissions: list[str]
    ) -> Dict[str, str]:
        """
        Create access and refresh tokens for a user.
        
        Args:
            user_id: User ID
            username: Username
            roles: User roles
            permissions: User permissions
            
        Returns:
            Dictionary containing access_token and refresh_token
        """
        # Create payload
        token_data = {
            "sub": user_id,
            "username": username,
            "roles": roles,
            "permissions": permissions,
            "iat": datetime.utcnow()
        }
        
        # Create access token
        access_token = JWTManager.create_access_token(token_data)
        
        # Create refresh token
        refresh_token = JWTManager.create_refresh_token(token_data)
        
        logger.info(f"Tokens created for user: {username}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        """
        Verify an access token.
        
        Args:
            token: JWT token
            
        Returns:
            Token payload
            
        Raises:
            JWTError: If token is invalid
        """
        # Check blacklist
        if TokenBlacklist.is_blacklisted(token):
            raise JWTError("Token has been revoked")
        
        # Verify token
        payload = JWTManager.verify_token(token, token_type="access")
        
        return payload
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """
        Generate a new access token from a refresh token.
        
        Args:
            refresh_token: JWT refresh token
            
        Returns:
            New access token
            
        Raises:
            JWTError: If refresh token is invalid
        """
        # Verify refresh token
        payload = JWTManager.verify_token(refresh_token, token_type="refresh")
        
        # Create new access token with same claims
        new_token_data = {
            "sub": payload["sub"],
            "username": payload["username"],
            "roles": payload.get("roles", []),
            "permissions": payload.get("permissions", []),
            "iat": datetime.utcnow()
        }
        
        new_access_token = JWTManager.create_access_token(new_token_data)
        
        logger.info(f"Access token refreshed for user: {payload['username']}")
        
        return new_access_token
    
    @staticmethod
    def logout(token: str) -> None:
        """
        Logout a user by blacklisting their token.
        
        Args:
            token: JWT token to revoke
        """
        try:
            payload = JWTManager.decode_token(token)
            exp = datetime.fromtimestamp(payload.get("exp", 0))
            TokenBlacklist.add_token(token, exp)
            
            logger.info(f"User logged out: {payload.get('username')}")
        except Exception as e:
            logger.warning(f"Error during logout: {e}")
    
    @staticmethod
    def validate_credentials(
        username: str,
        password: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate credentials format.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        is_valid, error = PasswordManager.validate_password_policy(password)
        if not is_valid:
            return False, error
        
        return True, None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return PasswordManager.hash_password(password)


class TokenManager:
    """Manage token operations."""
    
    @staticmethod
    def extract_token_from_header(auth_header: Optional[str]) -> Optional[str]:
        """
        Extract JWT token from Authorization header.
        
        Args:
            auth_header: Authorization header value
            
        Returns:
            Token string or None
        """
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
    
    @staticmethod
    def get_token_info(token: str) -> Dict[str, Any]:
        """
        Get information about a token.
        
        Args:
            token: JWT token
            
        Returns:
            Token information
        """
        try:
            payload = JWTManager.decode_token(token)
            return {
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", []),
                "expires_at": datetime.fromtimestamp(payload.get("exp", 0)),
                "issued_at": datetime.fromtimestamp(payload.get("iat", 0))
            }
        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return {}
