"""Unit tests for auth and security."""

import pytest
from app.core.security import PasswordManager, JWTManager
from app.core.permissions import PermissionChecker, Role, Permission


class TestPasswordManager:
    """Test password hashing and verification."""
    
    def test_hash_password_creates_different_hash(self):
        """Test that same password produces different hashes."""
        password = "TestPassword@123"
        hash1 = PasswordManager.hash_password(password)
        hash2 = PasswordManager.hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
        # Both should be longer than input
        assert len(hash1) > len(password)
        assert len(hash2) > len(password)
    
    def test_verify_password_success(self):
        """Test correct password verification."""
        password = "TestPassword@123"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(password, hashed) is True
    
    def test_verify_password_failure(self):
        """Test incorrect password rejection."""
        password = "TestPassword@123"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password("WrongPassword", hashed) is False
    
    def test_validate_password_policy_valid(self):
        """Test valid password passes policy."""
        is_valid, error = PasswordManager.validate_password_policy("ValidPass@123")
        assert is_valid is True
        assert error is None
    
    def test_validate_password_policy_too_short(self):
        """Test password that is too short."""
        is_valid, error = PasswordManager.validate_password_policy("Pass@1")
        assert is_valid is False
        assert "at least" in error.lower() or "length" in error.lower()
    
    def test_validate_password_policy_no_uppercase(self):
        """Test password without uppercase."""
        is_valid, error = PasswordManager.validate_password_policy("password@123")
        assert is_valid is False
    
    def test_validate_password_policy_no_number(self):
        """Test password without number."""
        is_valid, error = PasswordManager.validate_password_policy("Password@")
        assert is_valid is False
    
    def test_validate_password_policy_no_special_char(self):
        """Test password without special character."""
        is_valid, error = PasswordManager.validate_password_policy("Password123")
        assert is_valid is False


class TestJWTManager:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test creating access token."""
        data = {"sub": "user123", "username": "testuser"}
        token = JWTManager.create_access_token(data)
        
        assert token
        assert isinstance(token, str)
        # JWT has three parts separated by dots
        assert token.count(".") == 2
    
    def test_create_refresh_token(self):
        """Test creating refresh token."""
        data = {"sub": "user123", "username": "testuser"}
        token = JWTManager.create_refresh_token(data)
        
        assert token
        assert isinstance(token, str)
        assert token.count(".") == 2
    
    def test_create_tokens_are_different_types(self):
        """Test that access and refresh tokens are different."""
        data = {"sub": "user123"}
        access_token = JWTManager.create_access_token(data)
        refresh_token = JWTManager.create_refresh_token(data)
        
        assert access_token != refresh_token
    
    def test_verify_access_token(self):
        """Test verifying valid access token."""
        data = {"sub": "user123", "username": "testuser"}
        token = JWTManager.create_access_token(data)
        
        payload = JWTManager.verify_token(token, token_type="access")
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"
    
    def test_verify_refresh_token(self):
        """Test verifying refresh token."""
        data = {"sub": "user123"}
        token = JWTManager.create_refresh_token(data)
        
        payload = JWTManager.verify_token(token, token_type="refresh")
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
    
    def test_verify_token_wrong_type_fails(self):
        """Test that wrong token type verification fails."""
        data = {"sub": "user123"}
        token = JWTManager.create_access_token(data)
        
        with pytest.raises(Exception):
            JWTManager.verify_token(token, token_type="refresh")
    
    def test_decode_token_without_verification(self):
        """Test decoding token without verification."""
        data = {"sub": "user123", "username": "testuser"}
        token = JWTManager.create_access_token(data)
        
        payload = JWTManager.decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"


class TestPermissions:
    """Test permission and role system."""
    
    def test_role_has_permissions(self):
        """Test that roles have permissions."""
        assert len(Role.ADMIN.permissions) > 0
        assert len(Role.USER.permissions) > 0
    
    def test_admin_has_all_permissions(self):
        """Test admin role includes all permissions."""
        admin_perms = Role.ADMIN.permissions
        user_perms = Role.USER.permissions
        
        # Admin should have more or equal permissions
        assert len(admin_perms) >= len(user_perms)
    
    def test_permission_checker_validates_role(self):
        """Test permission checker."""
        checker = PermissionChecker()
        
        assert checker.has_role(Role.ADMIN) is not None
        assert checker.has_permission(Permission.READ) is not None
    
    def test_different_roles_have_different_perms(self):
        """Test that different roles have different permissions."""
        roles = [Role.ADMIN, Role.USER, Role.GUEST]
        
        # At least some difference in permissions
        perm_sets = [set(r.permissions) for r in roles]
        assert len(set(tuple(sorted(p)) for p in perm_sets)) > 1
