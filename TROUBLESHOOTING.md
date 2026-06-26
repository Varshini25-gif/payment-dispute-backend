# Authentication & Security Troubleshooting Guide

## Common Issues and Solutions

### 🔴 Issue: "ImportError: No module named 'jose'"

**Error Message:**
```
ImportError: No module named 'jose'
or
ModuleNotFoundError: No module named 'cryptography'
```

**Cause:** Required security packages not installed

**Solution:**
```bash
# Install all security dependencies
pip install -r requirements.txt

# Or install individually
pip install PyJWT python-jose cryptography passlib
```

**Verification:**
```bash
python -c "import jwt; import jose; import passlib; print('All modules OK')"
```

---

### 🔴 Issue: "JWT could not be verified"

**Error Message:**
```
JWTError: Signature verification failed
or
JWTError: Invalid token
```

**Causes:**
1. Token tampered with or modified
2. SECRET_KEY doesn't match (different environment)
3. Wrong algorithm configuration
4. Token expired

**Solutions:**

**1. Verify SECRET_KEY is consistent:**
```python
from app.core.config import settings
print(settings.SECRET_KEY)
print(settings.ALGORITHM)
```

**2. Check token format:**
```bash
# Correct format
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

# Wrong formats
Authorization: eyJhbGciOiJIUzI1NiIs...  # Missing "Bearer "
Authorization: bearer eyJhbGciOiJIUzI1NiIs...  # Wrong case (should be Bearer)
```

**3. Use fresh token:**
```bash
# Get new token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@123"}'

# Use the returned access_token
```

**4. Check token expiration:**
```python
from app.core.security import JWTManager

token = "your-token-here"
try:
    payload = JWTManager.verify_token(token)
    print("Token valid")
except Exception as e:
    print(f"Token error: {e}")
```

---

### 🔴 Issue: "401 Unauthorized - Invalid or expired token"

**Error Message:**
```json
{
  "detail": "Invalid or expired token",
  "headers": {"WWW-Authenticate": "Bearer"}
}
```

**Causes:**
1. Token expired (30 minutes default)
2. Token missing from header
3. Token format incorrect
4. Token was blacklisted (logout)

**Solutions:**

**1. Check if token expired:**
```bash
# Visit https://jwt.io in browser
# Paste your token to see expiration (exp claim)
```

**2. Refresh token if expired:**
```bash
curl -X POST "http://localhost:8000/api/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your-refresh-token-here"}'
```

**3. Verify header format:**
```bash
# Correct
-H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."

# Wrong
-H "Authorization: eyJhbGciOiJIUzI1NiIs..."
-H "Authorization: Token eyJhbGciOiJIUzI1NiIs..."
-H "Authorization: Basic eyJhbGciOiJIUzI1NiIs..."
```

**4. Check if token was blacklisted:**
```python
from app.core.security import TokenBlacklist

token = "your-token"
if TokenBlacklist.is_blacklisted(token):
    print("Token is blacklisted, get new one")
```

---

### 🔴 Issue: "403 Forbidden - User does not have permission"

**Error Message:**
```json
{
  "detail": "User does not have permission: create_dispute"
}
```

**Causes:**
1. User role doesn't have required permission
2. Wrong endpoint for user's role
3. Permissions not synced from database

**Solutions:**

**1. Check user permissions:**
```bash
# Get current user info
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer <token>"

# Response shows roles and permissions
```

**2. Check role permissions mapping:**
```python
from app.core.permissions import PermissionChecker, Role, Permission

# Get permissions for role
admin_perms = PermissionChecker.get_permissions_for_role(Role.ADMIN)
print(admin_perms)

# Check if role has permission
has_perm = PermissionChecker.has_permission(
    ["admin"],
    Permission.CREATE_DISPUTE
)
print(has_perm)
```

**3. Use correct role:**
```
Admin endpoint:      POST /api/auth/admin-only          (admin role)
Manager endpoint:    GET /api/auth/manager-data         (manager role)
Public endpoint:     GET /api/health                    (no auth)
```

**4. If using database, verify user roles:**
```python
from app.database.models.user import User

user = db.query(User).filter(User.username == "admin").first()
print(user.roles)  # Should be ["admin"]
```

---

### 🔴 Issue: "Secret key not found" or "SECRET_KEY is empty"

**Error Message:**
```
ValueError: SECRET_KEY not found
or
KeyError: 'SECRET_KEY'
```

**Cause:** `.env` file not loaded or SECRET_KEY not set

**Solutions:**

**1. Create and configure .env file:**
```bash
# Create from template
cp .env.example .env

# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env and add
SECRET_KEY=<paste-generated-key-here>
```

**2. Verify .env is being loaded:**
```python
from dotenv import load_dotenv
import os

load_dotenv()
secret = os.getenv("SECRET_KEY")
print(f"SECRET_KEY: {secret}")
```

**3. Check .env file exists:**
```bash
# List .env file
ls -la .env

# Check contents
cat .env | grep SECRET_KEY
```

**4. Restart application after adding .env:**
```bash
# Stop the app (Ctrl+C)
# Make sure .env is in project root
# Restart
python -m uvicorn app.main:app --reload
```

---

### 🔴 Issue: "CORS error" in Browser

**Error Message:**
```
Access to XMLHttpRequest at 'http://localhost:8000/api/auth/login' 
from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Cause:** Frontend origin not in ALLOW_ORIGINS

**Solutions:**

**1. Check ALLOW_ORIGINS in .env:**
```env
ALLOW_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

**2. Add your frontend URL:**
```env
# Development
ALLOW_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:8080"]

# Production
ALLOW_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]
```

**3. Restart application after changing .env**

**4. Verify CORS middleware is configured:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOW_METHODS,
    allow_headers=settings.ALLOW_HEADERS,
)
```

---

### 🔴 Issue: "Password validation failed"

**Error Message:**
```
Password must contain at least one uppercase letter
or
Password must contain at least one special character
```

**Cause:** Password doesn't meet policy requirements

**Password Requirements:**
- ✅ Minimum 8 characters
- ✅ At least one uppercase letter (A-Z)
- ✅ At least one lowercase letter (a-z) - implicit
- ✅ At least one number (0-9)
- ✅ At least one special character (!@#$%^&*-_=+)

**Valid Examples:**
```
MyPassword123!
Secure@Pass2024
Admin#2024Secure
Test@Password456
```

**Invalid Examples:**
```
password (no uppercase, no number, no special char)
Password (no number, no special char)
Password123 (no special char)
PASS@WORD (no number, wrong case)
```

**Solution:**
```bash
# Use a password meeting all requirements
# Minimum 8 chars, uppercase, number, special char
curl -X POST "http://localhost:8000/api/auth/change-password" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "Admin@123",
    "new_password": "NewSecure@Pass456"
  }'
```

---

### 🔴 Issue: "User not found" Login Error

**Error Message:**
```json
{
  "detail": "Invalid username or password"
}
```

**Cause:** Username doesn't exist or wrong password

**Solutions:**

**1. Use valid demo username:**
```
admin
manager
analyst
```

**2. Check username spelling:**
```bash
# Correct
curl -X POST "http://localhost:8000/api/auth/login" \
  -d '{"username": "admin", ...}'

# Wrong (demo users are lowercase)
-d '{"username": "Admin", ...}'
```

**3. Use correct password:**
```
admin password:    Admin@123
manager password:  Manager@123
analyst password:  Analyst@123
```

**4. For database users, verify they exist:**
```python
from app.database.models.user import User

user = db.query(User).filter(User.username == "admin").first()
if user:
    print("User exists")
else:
    print("User not found")
```

---

### 🔴 Issue: "Token refresh fails"

**Error Message:**
```
401 Unauthorized: Invalid refresh token
```

**Causes:**
1. Refresh token expired (7 days default)
2. Refresh token tampered with
3. Wrong refresh token format

**Solutions:**

**1. Get new tokens via login:**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@123"}'
```

**2. Check refresh token format:**
```bash
# Correct format in request
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}

# Verify token is not empty or modified
```

**3. Set REFRESH_TOKEN_EXPIRE_DAYS if needed:**
```env
# In .env
REFRESH_TOKEN_EXPIRE_DAYS=7  # Default is 7 days
```

---

### 🔴 Issue: "Rate limit exceeded"

**Error Message:**
```json
{
  "detail": "Rate limit exceeded"
}
```

**Cause:** Too many requests in a short time window

**Solutions:**

**1. Wait for time window to pass:**
```
Default: 100 requests per 60 seconds
Contact admin if legitimate use case exceeds limit
```

**2. Configure rate limiting:**
```python
from app.api.dependencies import check_rate_limit

# Adjust limits if needed
@router.post("/endpoint")
async def endpoint(
    user = Depends(check_rate_limit(max_requests=1000, window_seconds=3600))
):
    pass
```

---

### 🔴 Issue: "Encryption key not found"

**Error Message:**
```
KeyError: 'ENCRYPTION_KEY'
or
ValueError: Invalid encryption key
```

**Solutions:**

**1. Generate encryption key:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**2. Add to .env:**
```env
ENCRYPTION_KEY=<paste-generated-key-here>
```

**3. Verify key format:**
```python
from cryptography.fernet import Fernet

key = "your-key-from-env"
try:
    Fernet(key.encode())
    print("Key is valid")
except:
    print("Key is invalid")
```

---

### 🔴 Issue: "Application won't start"

**Error Message:**
```
RuntimeError: Invalid SECRET_KEY
or
ImportError when importing app
```

**Solutions:**

**1. Check all imports:**
```bash
python -c "from app.main import app; print('OK')"
```

**2. Test security modules individually:**
```bash
python -c "from app.core.security import JWTManager; print('OK')"
python -c "from app.core.auth import AuthService; print('OK')"
python -c "from app.core.permissions import PermissionChecker; print('OK')"
```

**3. Verify configuration loads:**
```bash
python -c "from app.core.config import settings; print(settings.SECRET_KEY)"
```

**4. Check for syntax errors:**
```bash
python -m py_compile app/core/security.py
python -m py_compile app/core/auth.py
```

---

### 🟡 Issue: "Tests Fail"

**Error in test output:**
```
FAILED tests/test_auth.py::TestPasswordManager::test_hash_password
```

**Solutions:**

**1. Run tests with verbose output:**
```bash
pytest tests/test_auth.py -v -s
```

**2. Check test requirements:**
```bash
pip install pytest httpx
```

**3. Verify app can start:**
```bash
python -m uvicorn app.main:app --reload
```

**4. Check fixture setup:**
```python
# Ensure demo users exist
from app.api.routes.auth import DEMO_USERS
print(DEMO_USERS)
```

---

## 🔧 Debug Commands

**Test JWT creation:**
```bash
python -c "
from app.core.security import JWTManager
token = JWTManager.create_access_token({'sub': 'user1', 'username': 'test'})
print(f'Token: {token}')
"
```

**Test password hashing:**
```bash
python -c "
from app.core.security import PasswordManager
pwd = 'TestPassword@123'
hashed = PasswordManager.hash_password(pwd)
print(f'Hashed: {hashed}')
print(f'Valid: {PasswordManager.verify_password(pwd, hashed)}')
"
```

**Test permissions:**
```bash
python -c "
from app.core.permissions import PermissionChecker, Role, Permission
print(PermissionChecker.get_permissions_for_role(Role.ADMIN))
"
```

**Check configuration:**
```bash
python -c "
from app.core.config import settings
print(f'APP_NAME: {settings.APP_NAME}')
print(f'ALGORITHM: {settings.ALGORITHM}')
print(f'ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}')
"
```

---

## 📞 Need More Help?

1. **Documentation:** See `docs/AUTHENTICATION.md`
2. **Setup Guide:** See `docs/SECURITY_SETUP.md`
3. **Quick Reference:** See `docs/SECURITY_QUICK_REFERENCE.md`
4. **Test Examples:** See `tests/test_auth.py`
5. **Implementation:** See `IMPLEMENTATION_SUMMARY.md`

---

**Last Updated:** 2024
**Status:** Troubleshooting Guide v1.0
