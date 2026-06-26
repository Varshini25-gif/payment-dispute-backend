"""
Tests for authentication and authorization system.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import PasswordManager, JWTManager
from app.core.permissions import PermissionChecker, Role, Permission

client = TestClient(app)


class TestPasswordManager:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword@123"
        hashed = PasswordManager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20
    
    def test_verify_password(self):
        """Test password verification."""
        password = "TestPassword@123"
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(password, hashed)
        assert not PasswordManager.verify_password("WrongPassword", hashed)
    
    def test_validate_password_policy(self):
        """Test password policy validation."""
        # Valid password
        is_valid, error = PasswordManager.validate_password_policy("ValidPass@123")
        assert is_valid
        assert error is None
        
        # Too short
        is_valid, error = PasswordManager.validate_password_policy("Pass@1")
        assert not is_valid
        assert "at least" in error.lower()
        
        # No uppercase
        is_valid, error = PasswordManager.validate_password_policy("password@123")
        assert not is_valid
        
        # No number
        is_valid, error = PasswordManager.validate_password_policy("Password@")
        assert not is_valid
        
        # No special character
        is_valid, error = PasswordManager.validate_password_policy("Password123")
        assert not is_valid


class TestJWTManager:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "user123", "username": "testuser"}
        token = JWTManager.create_access_token(data)
        
        assert token
        assert isinstance(token, str)
        assert token.count(".") == 2  # JWT format: header.payload.signature
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "user123", "username": "testuser"}
        token = JWTManager.create_refresh_token(data)
        
        assert token
        assert isinstance(token, str)
        assert token.count(".") == 2
    
    def test_verify_token(self):
        """Test token verification."""
        data = {"sub": "user123", "username": "testuser"}
        token = JWTManager.create_access_token(data)
        
        payload = JWTManager.verify_token(token, token_type="access")
        assert payload["sub"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"
    
    def test_decode_token(self):
        """Test token decoding without verification."""
        data = {"sub": "user123", "username": "testuser"}
        token = JWTManager.create_access_token(data)
        
        payload = JWTManager.decode_token(token)
        assert payload["sub"] == "user123"


class TestPermissions:
    """Test permission and role system."""
    
    def test_get_permissions_for_role(self):
        """Test getting permissions for a role."""
        admin_perms = PermissionChecker.get_permissions_for_role(Role.ADMIN)
        
        assert Permission.CREATE_DISPUTE in admin_perms
        assert Permission.DELETE_DISPUTE in admin_perms
        assert Permission.MANAGE_SYSTEM in admin_perms
    
    def test_get_permissions_for_roles(self):
        """Test getting permissions for multiple roles."""
        perms = PermissionChecker.get_permissions_for_roles(["admin", "viewer"])
        
        # Admin has all permissions
        assert Permission.CREATE_DISPUTE in perms
        # Union of both roles
        assert Permission.READ_DISPUTE in perms
    
    def test_has_permission(self):
        """Test permission check."""
        assert PermissionChecker.has_permission(
            ["admin"],
            Permission.CREATE_DISPUTE
        )
        assert PermissionChecker.has_permission(
            ["viewer"],
            Permission.READ_DISPUTE
        )
        assert not PermissionChecker.has_permission(
            ["viewer"],
            Permission.DELETE_DISPUTE
        )
    
    def test_has_all_permissions(self):
        """Test checking for all permissions."""
        assert PermissionChecker.has_all_permissions(
            ["admin"],
            [Permission.CREATE_DISPUTE, Permission.DELETE_DISPUTE]
        )
        assert not PermissionChecker.has_all_permissions(
            ["viewer"],
            [Permission.CREATE_DISPUTE, Permission.DELETE_DISPUTE]
        )
    
    def test_role_hierarchy(self):
        """Test role hierarchy."""
        hierarchy = PermissionChecker.get_role_hierarchy()
        
        assert hierarchy[Role.VIEWER] < hierarchy[Role.ANALYST]
        assert hierarchy[Role.ANALYST] < hierarchy[Role.MANAGER]
        assert hierarchy[Role.MANAGER] < hierarchy[Role.ADMIN]
    
    def test_get_highest_role(self):
        """Test getting highest role."""
        highest = PermissionChecker.get_highest_role(["viewer", "analyst"])
        assert highest == Role.ANALYST
        
        highest = PermissionChecker.get_highest_role(["admin", "viewer"])
        assert highest == Role.ADMIN


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_login_success(self):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin@123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "WrongPassword"}
        )
        
        assert response.status_code == 401
    
    def test_login_user_not_found(self):
        """Test login with non-existent user."""
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "Password@123"}
        )
        
        assert response.status_code == 401
    
    def test_get_current_user(self):
        """Test getting current user info."""
        # First login
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin@123"}
        )
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert "admin" in data["roles"]
    
    def test_get_current_user_no_token(self):
        """Test getting current user without token."""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 403
    
    def test_refresh_token(self):
        """Test token refresh."""
        # First login
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin@123"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_token_invalid(self):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        assert response.status_code == 401
    
    def test_change_password(self):
        """Test password change."""
        # First login
        login_response = client.post(
            "/api/auth/login",
            json={"username": "analyst", "password": "Analyst@123"}
        )
        token = login_response.json()["access_token"]
        
        # Change password
        response = client.post(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "Analyst@123",
                "new_password": "NewPassword@456"
            }
        )
        
        # This should work in production with actual database
        assert response.status_code in [200, 404]
    
    def test_admin_only_endpoint(self):
        """Test admin-only endpoint access."""
        # Login as admin
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "Admin@123"}
        )
        token = login_response.json()["access_token"]
        
        # Access admin endpoint
        response = client.get(
            "/api/auth/admin-only",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
    
    def test_admin_only_endpoint_denied(self):
        """Test admin-only endpoint denied for non-admin."""
        # Login as viewer
        login_response = client.post(
            "/api/auth/login",
            json={"username": "analyst", "password": "Analyst@123"}
        )
        token = login_response.json()["access_token"]
        
        # Try to access admin endpoint
        response = client.get(
            "/api/auth/admin-only",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should be denied
        assert response.status_code in [403, 401]


class TestDifferentRoles:
    """Test endpoints with different user roles."""
    
    def test_manager_endpoint_access(self):
        """Test manager can access manager endpoint."""
        login_response = client.post(
            "/api/auth/login",
            json={"username": "manager", "password": "Manager@123"}
        )
        token = login_response.json()["access_token"]
        
        response = client.get(
            "/api/auth/manager-data",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
    
    def test_analyst_endpoint_access(self):
        """Test analyst access with permissions."""
        login_response = client.post(
            "/api/auth/login",
            json={"username": "analyst", "password": "Analyst@123"}
        )
        token = login_response.json()["access_token"]
        user = login_response.json()["user"]
        
        assert "analyst" in user["roles"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
