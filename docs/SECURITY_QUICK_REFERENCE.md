# Authentication & Security - Quick Reference

## 🔐 Security Files Created

```
app/core/
├── security.py              # JWT, password hashing, encryption
├── auth.py                  # Authentication service
└── permissions.py           # Role-based access control

app/api/
├── dependencies/
│   └── auth_guard.py        # Auth middleware & guards
└── routes/
    └── auth.py              # Login, refresh, logout endpoints

docs/
├── AUTHENTICATION.md        # Complete auth documentation
└── SECURITY_SETUP.md        # Setup & configuration guide

.env.example                 # Environment variables template
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate & Configure Secrets
```bash
# Generate SECRET_KEY
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"

# Copy .env from template
cp .env.example .env

# Edit .env and paste the generated keys
```

### 3. Run Application
```bash
python -m uvicorn app.main:app --reload
```

## 🔑 Available Roles

| Role | Permissions |
|------|-------------|
| **ADMIN** | All |
| **MANAGER** | Create, Read, Update disputes; Manage SLA & Routing |
| **ANALYST** | Create, Read, Update disputes; View SLA & Routing |
| **VIEWER** | Read disputes; View SLA & Routing |
| **SYSTEM** | All (automated tasks) |

## 🛡️ Permission Names

- `create_dispute`, `read_dispute`, `update_dispute`, `delete_dispute`
- `view_sla`, `manage_sla`
- `view_routing`, `manage_routing`
- `publish_confluence`, `view_confluence`
- `manage_users`, `view_audit_log`, `manage_system`, `manage_roles`
- `access_api`

## 📝 API Endpoints

### Authentication
```
POST   /api/auth/login              Login
POST   /api/auth/refresh             Refresh token
GET    /api/auth/me                  Get current user
POST   /api/auth/change-password     Change password
POST   /api/auth/logout              Logout
GET    /api/auth/token-info          Get token info
GET    /api/auth/admin-only          Admin-only example
GET    /api/auth/manager-data        Manager example
```

## 💻 Usage Examples

### Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@123"}'
```

### Get Current User
```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer <token>"
```

### Protected Endpoint
```python
from fastapi import Depends
from app.api.dependencies import get_current_user, CurrentUser

@router.get("/data")
async def get_data(current_user: CurrentUser = Depends(get_current_user)):
    return {"user": current_user.username}
```

### Permission Check
```python
from app.api.dependencies import require_permission
from app.core.permissions import Permission

@router.post("/disputes")
async def create_dispute(
    current_user = Depends(require_permission(Permission.CREATE_DISPUTE))
):
    pass
```

### Role Check
```python
from app.api.dependencies import require_role
from app.core.permissions import Role

@router.delete("/disputes/{id}")
async def delete_dispute(
    current_user = Depends(require_role(Role.ADMIN))
):
    pass
```

### Rate Limiting
```python
from app.api.dependencies import check_rate_limit

@router.post("/sensitive")
async def sensitive_endpoint(
    current_user = Depends(check_rate_limit(max_requests=5, window_seconds=60))
):
    pass
```

## 🔐 Password Requirements

- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one number (0-9)
- At least one special character (!@#$%^&*-_=+)

Valid: `MyPassword123!`, `Secure@Pass2024`
Invalid: `password`, `Password123`

## 🧪 Demo Users

```
Username: admin    | Password: Admin@123
Username: manager  | Password: Manager@123
Username: analyst  | Password: Analyst@123
```

## 📋 Configuration

Key `.env` variables:
```env
# Security
SECRET_KEY=<generate-and-paste>
ENCRYPTION_KEY=<generate-and-paste>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOW_ORIGINS=["http://localhost:3000"]
ALLOW_CREDENTIALS=True

# Password Policy
MIN_PASSWORD_LENGTH=8
REQUIRE_SPECIAL_CHAR=True
REQUIRE_NUMBER=True
REQUIRE_UPPERCASE=True
```

## ⚠️ Important: Development vs Production

### Development
```env
ENVIRONMENT=development
SECRET_KEY=dev-key-change-in-production
ALLOW_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

### Production
```env
ENVIRONMENT=production
SECRET_KEY=<generate-strong-unique-key>
ALLOW_ORIGINS=["https://yourdomain.com"]
```

## 🐛 Troubleshooting

| Error | Solution |
|-------|----------|
| Invalid token | Regenerate using /api/auth/login |
| Permission denied | Check user roles/permissions |
| CORS error | Update ALLOW_ORIGINS in .env |
| Secret key not found | Generate and add to .env |
| Password validation failed | Meet password policy requirements |

## 📚 Documentation

- **AUTHENTICATION.md** - Full authentication guide with examples
- **SECURITY_SETUP.md** - Step-by-step setup instructions
- **.env.example** - All available configuration options

## 🔄 Token Flow

```
1. User logs in → POST /api/auth/login
2. Receive access_token & refresh_token
3. Send access_token in Authorization header → GET /api/auth/me
4. Token expires after 30 minutes
5. Use refresh_token → POST /api/auth/refresh
6. Receive new access_token
7. On logout → POST /api/auth/logout (blacklist token)
```

## 🛡️ Security Checklist

- [ ] SECRET_KEY is unique and strong (32+ chars)
- [ ] ENCRYPTION_KEY is generated
- [ ] .env is in .gitignore
- [ ] HTTPS enabled in production
- [ ] CORS origins restricted
- [ ] Audit logging enabled
- [ ] Rate limiting configured
- [ ] Demo users replaced with database

## 📞 Core Classes & Functions

**Security:**
- `PasswordManager.hash_password(pwd)`
- `PasswordManager.verify_password(pwd, hash)`
- `JWTManager.create_access_token(data)`
- `SecretManager.encrypt(value)`

**Auth:**
- `AuthService.authenticate_user(user, pwd, hash)`
- `AuthService.create_tokens(user_id, username, roles, perms)`
- `AuthService.refresh_access_token(refresh_token)`

**Permissions:**
- `PermissionChecker.has_permission(roles, permission)`
- `PermissionChecker.get_permissions_for_roles(roles)`
- `PermissionChecker.get_highest_role(roles)`

**Dependencies:**
- `get_current_user()` - Authenticated user
- `get_optional_user()` - Optional user
- `require_permission(perm)` - Permission guard
- `require_role(role)` - Role guard
- `check_rate_limit(req, sec)` - Rate limit

---

**Need Help?** See AUTHENTICATION.md or SECURITY_SETUP.md
