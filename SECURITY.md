# Security Documentation

## Overview

This document describes the security measures implemented in the Quality Control System and provides guidance for secure deployment and operation.

## Security Features

### 1. Authentication & Authorization

#### User Authentication
- **Login System**: Secure login with username and password
- **Password Hashing**: PBKDF2-HMAC-SHA256 with 100,000 iterations and unique salt per user
- **Session Management**: Filesystem-based sessions with signing
- **Role-Based Access Control**: Users have roles (user, admin) with different permissions

#### User Management
- Users are stored in the `пользователи` (users) table with Cyrillic naming
- Passwords are never stored in plaintext
- Last login timestamps are tracked

#### Protected Routes
All application routes except `/login` require authentication:
- UI routes redirect to login page
- API routes return 401 Unauthorized

Admin-only routes (require `admin` role):
- `/manage-controllers` - Controller management
- `/add-controller` - Add new controller
- Other administrative functions

### 2. Session Security

#### Session Configuration
```python
SESSION_COOKIE_SECURE = True  # HTTPS only (production)
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_USE_SIGNER = True  # Sign session cookies
```

#### Environment Variables
```bash
SESSION_COOKIE_SECURE=True  # Enable in production with HTTPS
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax  # Options: Lax, Strict, None
```

### 3. Secret Key Management

#### Environment-Based Configuration
The `SECRET_KEY` must be set via environment variable:

```bash
# Generate a secure key
python -c "import secrets; print(secrets.token_hex(32))"

# Set in environment
export SECRET_KEY='your-generated-key-here'
```

⚠️ **Warning**: Never commit SECRET_KEY to version control!

#### Development vs Production
- Development: Auto-generated key (with warning)
- Production: Must set SECRET_KEY in environment or `.env` file

### 4. CORS Configuration

#### Allowlist-Based CORS
Only specified origins are allowed:

```bash
# Environment variable (comma-separated)
CORS_ORIGINS=http://localhost:5004,http://127.0.0.1:5004,https://yourdomain.com
```

#### Default Configuration
```python
CORS_ORIGINS = ['http://localhost:5004', 'http://127.0.0.1:5004']
CORS_ALLOW_CREDENTIALS = True
CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
CORS_ALLOWED_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With']
```

### 5. Input Validation

#### Pydantic Models
All API inputs are validated using Pydantic models:

- **LoginRequest**: Username and password validation
- **ShiftCreateRequest**: Shift creation with date/number validation
- **ControlDataRequest**: Quality control data with range checks
- **ControllerRequest**: Controller management
- **RouteCardSearchRequest**: Route card number format validation
- **QRScanRequest**: QR code data validation
- **StatisticsQueryRequest**: Date range validation

#### Validation Features
- Type checking
- Range validation (min/max values)
- String length limits
- Pattern matching (regex)
- Custom validators
- Sanitization

#### Example Validation
```python
class ControlDataRequest(BaseModel):
    номер_маршрутной_карты: str = Field(..., pattern=r'^\d{6}$')
    всего_отлито: int = Field(..., gt=0, le=100000)
    всего_принято: int = Field(..., ge=0, le=100000)
    # ...
```

#### SQL Injection Prevention
- Parameterized queries used throughout
- Table/column names validated against whitelist
- No dynamic SQL generation with user input

### 6. XSS Protection

#### Template Rendering
- Flask's Jinja2 auto-escaping enabled by default
- All user inputs are escaped in templates
- No `|safe` filter used on untrusted data

#### Input Sanitization
```python
from utils.input_validators import sanitize_string

clean_input = sanitize_string(user_input)
```

### 7. Path Traversal Protection

#### Static File Serving
The `/static/<path:filename>` route includes protections:

- Path validation (no `..` or leading `/`)
- File extension whitelist
- Proper error handling

```python
allowed_extensions = {'.css', '.js', '.png', '.jpg', '.jpeg', 
                      '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf'}
```

### 8. Error Handling

#### Production Error Messages
- Generic error messages shown to users
- Detailed errors logged server-side only
- No stack traces in responses (production)
- Structured logging with context

#### Error Handlers
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found
- 500 Internal Server Error
- Generic exception handler

## Configuration Guide

### Environment Variables

Create a `.env` file (see `.env.example`):

```bash
# Required for production
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=SecurePassword123!@#

# Session security
SESSION_COOKIE_SECURE=True  # Enable with HTTPS
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# CORS
CORS_ORIGINS=https://yourdomain.com

# Application
FLASK_ENV=production
DEBUG=False
```

### Initial Setup

1. **Generate Secret Key**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Set Environment Variables**
   ```bash
   export SECRET_KEY='your-generated-key'
   export ADMIN_USERNAME='admin'
   export ADMIN_PASSWORD='YourSecurePassword123!@#'
   ```

3. **Initialize Database**
   ```bash
   python main.py
   ```
   This creates the users table and default admin user.

4. **Change Default Password**
   Log in with default credentials and change password immediately.

### Production Deployment Checklist

- [ ] Set SECRET_KEY from environment
- [ ] Set ADMIN_USERNAME and ADMIN_PASSWORD
- [ ] Enable SESSION_COOKIE_SECURE (requires HTTPS)
- [ ] Configure CORS_ORIGINS with actual domain
- [ ] Set FLASK_ENV=production
- [ ] Set DEBUG=False
- [ ] Configure HTTPS/TLS
- [ ] Set up log rotation
- [ ] Review firewall rules
- [ ] Enable rate limiting (reverse proxy)
- [ ] Set up monitoring/alerting

## User Management

### Creating Users

#### Via Environment (Admin User)
```bash
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=SecurePassword123!@#
```

#### Via Database (Additional Users)
```python
from utils.auth import create_user
import sqlite3

conn = sqlite3.connect('data/quality_control.db')
create_user(conn, 'username', 'password', role='user')
conn.close()
```

### Password Requirements

Passwords must meet the following criteria:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

### Roles

- **admin**: Full access including user/controller management
- **user**: Standard access to quality control functions

## Logging

### Security Events Logged

- User login attempts (success/failure)
- User logout
- Authentication failures
- Authorization failures (403)
- Input validation errors
- Path traversal attempts
- File access errors
- All exceptions

### Log Files

- `logs/application.log` - Application logs
- Structured JSON logging for important events

### Log Levels

- **INFO**: Normal operations, user actions
- **WARNING**: Validation errors, suspicious activity
- **ERROR**: Application errors, failures
- **DEBUG**: Detailed stack traces (not in production)

## Best Practices

### For Administrators

1. **Use strong passwords** for all users
2. **Change default credentials** immediately
3. **Regularly review logs** for suspicious activity
4. **Keep dependencies updated** (`pip install -U -r requirements.txt`)
5. **Use HTTPS** in production
6. **Backup database** regularly
7. **Limit CORS origins** to known domains
8. **Use rate limiting** at reverse proxy level

### For Developers

1. **Never commit secrets** to version control
2. **Use `.env` files** for local development
3. **Always validate inputs** using Pydantic models
4. **Use parameterized queries** for SQL
5. **Sanitize all user inputs** before display
6. **Test security features** regularly
7. **Review code** for security issues
8. **Keep dependencies updated**

## Security Incident Response

If you discover a security issue:

1. **Do not disclose publicly** until patched
2. **Document the issue** with reproduction steps
3. **Assess impact** and affected versions
4. **Develop and test fix**
5. **Deploy patch** as soon as possible
6. **Notify users** if necessary
7. **Review logs** for exploitation attempts

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [Python Security](https://python.readthedocs.io/en/stable/library/security_warnings.html)

## Contact

For security concerns, contact the development team.
