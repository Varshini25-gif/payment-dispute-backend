"""
Security utilities for JWT token management, password hashing, and encryption.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


class SecretManager:
    """Manage encrypted secrets and sensitive data."""
    
    _cipher = None
    
    @classmethod
    def _get_cipher(cls) -> Fernet:
        """Get or create a Fernet cipher instance."""
        if cls._cipher is None:
            # Get or generate encryption key
            key_env = os.getenv("ENCRYPTION_KEY")
            if key_env:
                key = key_env.encode()
            else:
                # Generate a new key for development (NOT for production)
                key = Fernet.generate_key()
                logger.warning("Generated new encryption key for development. Set ENCRYPTION_KEY environment variable for persistence.")
            
            cls._cipher = Fernet(key)
        return cls._cipher
    
    @classmethod
    def encrypt(cls, value: str) -> str:
        """Encrypt a sensitive value."""
        cipher = cls._get_cipher()
        encrypted = cipher.encrypt(value.encode())
        return encrypted.decode()
    
    @classmethod
    def decrypt(cls, encrypted_value: str) -> str:
        """Decrypt an encrypted value."""
        cipher = cls._get_cipher()
        try:
            decrypted = cipher.decrypt(encrypted_value.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt value: {e}")
            raise ValueError("Decryption failed")


class PasswordManager:
    """Handle password hashing and verification."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def validate_password_policy(password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password against security policy.
        Returns: (is_valid, error_message)
        """
        if len(password) < settings.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters"
        
        if settings.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if settings.REQUIRE_NUMBER and not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        if settings.REQUIRE_SPECIAL_CHAR and not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password):
            return False, "Password must contain at least one special character"
        
        return True, None
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(length)


class JWTManager:
    """Handle JWT token creation, validation, and decoding."""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Payload data to encode
            expires_delta: Token expiration time delta
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                settings.SECRET_KEY,
                algorithm=settings.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise ValueError("Token creation failed")
    
    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            data: Payload data to encode
            expires_delta: Token expiration time delta
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                settings.SECRET_KEY,
                algorithm=settings.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise ValueError("Refresh token creation failed")
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Decoded token payload
            
        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Verify token type
            token_type_claim = payload.get("type")
            if token_type_claim != token_type:
                raise JWTError("Invalid token type")
            
            return payload
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode a JWT token without verification (for inspection only).
        
        Args:
            token: JWT token to decode
            
        Returns:
            Decoded token payload
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                options={"verify_signature": False}
            )
            return payload
        except JWTError as e:
            logger.error(f"Failed to decode token: {e}")
            raise


class TokenBlacklist:
    """Manage token blacklist for logout functionality."""
    
    _blacklist: set = set()
    
    @classmethod
    def add_token(cls, token: str, exp: datetime) -> None:
        """Add a token to the blacklist."""
        cls._blacklist.add((token, exp))
    
    @classmethod
    def is_blacklisted(cls, token: str) -> bool:
        """Check if a token is blacklisted."""
        # Clean up expired tokens from blacklist
        now = datetime.utcnow()
        cls._blacklist = {(t, exp) for t, exp in cls._blacklist if exp > now}
        
        return any(t == token for t, _ in cls._blacklist)
    
    @classmethod
    def clear_expired(cls) -> None:
        """Remove expired tokens from blacklist."""
        now = datetime.utcnow()
        cls._blacklist = {(t, exp) for t, exp in cls._blacklist if exp > now}
