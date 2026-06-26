# Authentication & Authorization System

## Overview

This document describes the JWT-based authentication and role-based access control (RBAC) system implemented for the Payment Dispute Backend API.

## Table of Contents

1. [Architecture](#architecture)
2. [JWT Implementation](#jwt-implementation)
3. [Roles & Permissions](#roles--permissions)
4. [Security Features](#security-features)
5. [API Authentication](#api-authentication)
6. [Usage Examples](#usage-examples)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Architecture

### Components

1. **app/core/security.py** - Core security utilities
   - JWT token creation/validation
   - Password hashing and verification
   - Secret encryption/decryption
   - Token blacklist management

2. **app/core/auth.py** - Authentication service
   - User authentication
   - Token generation and refresh
   - Logout handling
   - Credential validation

3. **app/core/permissions.py** - Authorization system
   - Role definitions
   - Permission mappings
   - Access control checks
   - Resource ownership validation

4. **app/api/dependencies/auth_guard.py** - API protection
   - Authentication middleware
   - Permission/role enforcement
   - Rate limiting
   - Endpoint security configuration

5. **app/api/routes/auth.py** - Authentication endpoints
   - Login endpoint
   - Token refresh endpoint
   - Logout endpoint
   - Password change endpoint

---

## JWT Implementation

### Token Structure

**Access Token Payload:**
```json
{
  "sub": "user_id",
  "username": "username",
  "roles": ["role1", "role2"],
  "permissions": ["perm1", "perm2"],
  "iat": 1234567890,
  "exp": 1234568890,
  "type": "access"
}
```

**Refresh Token Payload:**
```json
{
  "sub": "user_id",
  "username": "username",
  "roles": ["role1", "role2"],
  "permissions": ["perm1", "perm2"],
  "iat": 1234567890,
  "exp": 1234654290,
  "type": "refresh"
}
```

### Token Expiration

- **Access Token**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh Token**: 7 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)

### Secret Key Management

```python
# Generate a secure secret key (run once, store in .env)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# For encryption of sensitive data
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Roles & Permissions

### Available Roles

| Role | Level | Description |
|------|-------|-------------|
| **ADMIN** | 5 | Full system access |
| **MANAGER** | 4 | Management and oversight |
| **ANALYST** | 3 | Create and analyze disputes |
| **VIEWER** | 2 | Read-only access |
| **SYSTEM** | 5 | Automated system tasks |

### Permission Mappings

#### Admin Permissions
- All permissions granted

#### Manager Permissions
- `create_dispute`, `read_dispute`, `update_dispute`
- `view_sla`, `manage_sla`
- `view_routing`, `manage_routing`
- `publish_confluence`, `view_confluence`
- `view_audit_log`
- `access_api`

#### Analyst Permissions
- `create_dispute`, `read_dispute`, `update_dispute`
- `view_sla`, `view_routing`
- `view_confluence`
- `access_api`

#### Viewer Permissions
- `read_dispute`, `view_sla`, `view_routing`
- `view_confluence`
- `access_api`

#### System Permissions
- All permissions granted (for automated tasks)

---

## Security Features

### 1. Password Security

**Password Policy Requirements:**
```python
MIN_PASSWORD_LENGTH = 8
REQUIRE_SPECIAL_CHAR = True  # At least one of: !@#$%^&*()-_=+[]{}|;:,.<>?
REQUIRE_NUMBER = True         # At least one digit
REQUIRE_UPPERCASE = True      # At least one uppercase letter
```

**Password Hashing:**
- Algorithm: bcrypt with 12 rounds
- Never store plain text passwords
- Always verify using constant-time comparison

**Example Usage:**
```python
from app.core.security import PasswordManager

# Hash a password
hashed = PasswordManager.hash_password("MySecure@Pass123")

# Verify a password
is_valid = PasswordManager.verify_password("MySecure@Pass123", hashed)

# Validate password policy
is_valid, error = PasswordManager.validate_password_policy("Password123")
```

### 2. Secret Management

**Encrypt Sensitive Data:**
```python
from app.core.security import SecretManager

# Encrypt a secret
encrypted = SecretManager.encrypt("sensitive_data")

# Decrypt a secret
decrypted = SecretManager.decrypt(encrypted)
```

### 3. Token Blacklist

Tokens can be blacklisted for logout:
```python
from app.core.security import TokenBlacklist

# Add token to blacklist on logout
TokenBlacklist.add_token(token, expiration_time)

# Check if token is blacklisted
is_blacklisted = TokenBlacklist.is_blacklisted(token)
```

### 4. CORS Protection

CORS middleware configured in `app/main.py`:
```python
CORSMiddleware(
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
)
```

### 5. Rate Limiting

Rate limiting can be applied to endpoints:
```python
@router.get("/api/endpoint")
async def endpoint(
    current_user: CurrentUser = Depends(
        check_rate_limit(max_requests=100, window_seconds=60)
    )
):
    pass
```

---

## API Authentication

### Authentication Header Format

```
Authorization: Bearer <access_token>
```

### Login Endpoint

**Request:**
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "Admin@123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "user_id": "1",
    "username": "admin",
    "roles": ["admin"]
  }
}
```

### Refresh Token Endpoint

**Request:**
```bash
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Get Current User

**Request:**
```bash
GET /api/auth/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "user_id": "1",
  "username": "admin",
  "roles": ["admin"],
  "permissions": ["create_dispute", "read_dispute", "update_dispute", ...]
}
```

### Change Password

**Request:**
```bash
POST /api/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "Admin@123",
  "new_password": "NewSecure@Pass123"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully"
}
```

### Logout

**Request:**
```bash
POST /api/auth/logout
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

---

## Usage Examples

### 1. Protecting an Endpoint

**Basic Authentication Required:**
```python
from fastapi import Depends, APIRouter
from app.api.dependencies import get_current_user, CurrentUser

router = APIRouter()

@router.get("/protected")
async def protected_endpoint(current_user: CurrentUser = Depends(get_current_user)):
    return {"message": f"Hello, {current_user.username}"}
```

### 2. Requiring Specific Permission

```python
from app.api.dependencies import require_permission
from app.core.permissions import Permission

@router.post("/disputes")
async def create_dispute(
    current_user: CurrentUser = Depends(
        require_permission(Permission.CREATE_DISPUTE)
    )
):
    return {"message": "Dispute created"}
```

### 3. Requiring Specific Role

```python
from app.api.dependencies import require_role
from app.core.permissions import Role

@router.delete("/disputes/{dispute_id}")
async def delete_dispute(
    dispute_id: int,
    current_user: CurrentUser = Depends(require_role(Role.ADMIN))
):
    return {"message": "Dispute deleted"}
```

### 4. Checking Multiple Permissions

```python
@router.patch("/disputes/{dispute_id}")
async def update_dispute(
    dispute_id: int,
    current_user: CurrentUser = Depends(
        require_all_permissions(
            Permission.UPDATE_DISPUTE,
            Permission.MANAGE_ROUTING
        )
    )
):
    return {"message": "Dispute updated"}
```

### 5. Optional Authentication

```python
from app.api.dependencies import get_optional_user

@router.get("/public-data")
async def get_public_data(
    current_user: Optional[CurrentUser] = Depends(get_optional_user)
):
    if current_user:
        return {"data": "personalized", "user": current_user.username}
    return {"data": "public"}
```

### 6. In-Endpoint Permission Check

```python
from app.core.permissions import PermissionChecker, Permission

@router.get("/my-data")
async def get_my_data(current_user: CurrentUser = Depends(get_current_user)):
    if not PermissionChecker.has_permission(current_user.roles, Permission.READ_DISPUTE):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {"data": "sensitive"}
```

---

## Best Practices

### 1. Secret Key Management

- **Never commit secrets to version control**
- Store `SECRET_KEY` and `ENCRYPTION_KEY` in `.env` (not `.env.example`)
- Generate unique keys for each environment (development, staging, production)
- Rotate keys periodically in production

```bash
# Generate keys
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())" >> .env
```

### 2. HTTPS Only

- Always use HTTPS in production (never HTTP)
- Set `ENVIRONMENT` to `production` and configure proper security headers
- Use secure cookies (`secure=True`, `httponly=True`, `samesite='Lax'`)

### 3. Token Handling

- **Client-side:**
  - Store access token in memory or secure storage
  - Never log or expose tokens
  - Clear tokens on logout
  - Refresh token before expiration

- **Server-side:**
  - Validate token signature and expiration
  - Verify token type claims
  - Implement token blacklist for logout
  - Use short expiration times for access tokens

### 4. Password Management

- Enforce strong password policies
- Implement password expiration (90 days recommended)
- Prevent password reuse
- Implement lockout after failed attempts
- Never send passwords in logs or error messages

### 5. Audit Logging

- Log authentication attempts (success and failures)
- Log authorization denials
- Log token generation and refresh
- Include user, timestamp, and resource information
- Review logs regularly for suspicious activity

### 6. Rate Limiting

```python
@router.post("/auth/login")
async def login(
    request: LoginRequest,
    current_user: CurrentUser = Depends(
        check_rate_limit(max_requests=5, window_seconds=300)  # 5 attempts per 5 min
    )
):
    pass
```

### 7. Resource Ownership

```python
from app.core.permissions import ResourceOwnershipChecker

@router.put("/disputes/{dispute_id}")
async def update_dispute(
    dispute_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    dispute = get_dispute(dispute_id)
    
    if not ResourceOwnershipChecker.can_edit_resource(
        current_user.user_id,
        dispute.owner_id,
        current_user.roles
    ):
        raise HTTPException(status_code=403, detail="Cannot edit this resource")
    
    return update_dispute_in_db(dispute_id, ...)
```

---

## Troubleshooting

### 1. "Invalid or expired token"

**Causes:**
- Token has expired
- Secret key doesn't match (different environment)
- Token was tampered with

**Solutions:**
- Refresh the token using refresh endpoint
- Verify `SECRET_KEY` is the same across environments
- Check token format: `Bearer <token>`

### 2. "Permission denied"

**Causes:**
- User role doesn't have required permission
- User's permissions weren't synced from database

**Solutions:**
- Check user's roles and permissions in token payload
- Verify role-permission mapping in `permissions.py`
- Re-authenticate to get updated permissions

### 3. "Token verification failed"

**Causes:**
- Malformed token
- Invalid algorithm or key
- Token format incorrect

**Solutions:**
- Verify token format: `Authorization: Bearer <token>`
- Check `ALGORITHM` setting matches token
- Ensure valid JWT structure

### 4. "User not found"

**Causes:**
- Username doesn't exist
- User was deleted from database

**Solutions:**
- Create user first
- Verify username spelling
- Check database connection

### 5. Password validation errors

**Message:** "Password must contain at least one uppercase letter"

**Solutions:**
- Ensure password meets policy requirements:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one number
  - At least one special character

---

## Demo Credentials

For testing purposes, the following demo users are available:

| Username | Password | Role |
|----------|----------|------|
| admin | Admin@123 | Admin |
| manager | Manager@123 | Manager |
| analyst | Analyst@123 | Analyst |

**Important:** Replace with actual database integration in production!

---

## Security Checklist

- [ ] SECRET_KEY is unique and strong (32+ characters)
- [ ] ENCRYPTION_KEY is set for sensitive data
- [ ] .env file is in .gitignore (not committed)
- [ ] HTTPS is enabled in production
- [ ] CORS origins are restricted to known domains
- [ ] Password policy is enforced
- [ ] Token expiration times are reasonable
- [ ] Rate limiting is implemented
- [ ] Audit logging is enabled
- [ ] Token blacklist cleanup is scheduled
- [ ] Periodic security key rotation planned
- [ ] Failed authentication attempts are logged
- [ ] JWT validation is strict

---

## References

- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Cryptography.io - Fernet](https://cryptography.io/en/latest/fernet/)
