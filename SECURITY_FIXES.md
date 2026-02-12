# Security Fixes & Production Deployment

This document summarizes the security fixes and improvements made to the Badminton Club App.

---

## Changes Overview

### 🔴 Critical Security Fixes

| Issue | File | Fix |
|-------|------|-----|
| Weak default SECRET_KEY | `config_secure.py` | Production validation requires 32+ char random key |
| CORS wildcard with credentials | `config_secure.py` | Validation prevents unsafe CORS configuration |
| No rate limiting | `security_secure.py` | Implemented rate limiter with configurable limits |
| LINE OAuth CSRF | `auth_secure.py` | State parameter stored in Redis and validated |
| No HTTPS enforcement | `main_secure.py` | HSTS headers and HTTPS redirects |
| DB connection pooling | `database_secure.py` | Configured pool_size, max_overflow, timeouts |
| JWT missing claims | `security_secure.py` | Added iss, aud, iat, jti claims |
| WebSocket no auth | `socket_manager_secure.py` | Token validation on connect |

### 🟠 High Priority Fixes

| Issue | File | Fix |
|-------|------|-----|
| Password strength | `auth_secure.py` | Configurable policy (upper, lower, number, special) |
| Input validation | `auth_secure.py` | Pydantic validators for email, phone |
| Security headers | `main_secure.py` | Added HSTS, CSP, X-Frame-Options, etc. |
| Audit logging | `security_secure.py` | Structured audit logs for all auth events |
| Health check | `main_secure.py` | Actually checks database connectivity |
| Error handling | `main_secure.py` | Generic errors in production, detailed in dev |
| Database indexes | `models_secure.py` | Added 20+ indexes for performance |
| LINE OAuth timeouts | `line_oauth_secure.py` | Added timeouts and better error handling |

### 🟡 Medium Priority Improvements

| Issue | File | Fix |
|-------|------|-----|
| Request logging | `main_secure.py` | Structured logging with timing |
| Gzip compression | `main_secure.py` | Added for responses > 1KB |
| Trusted host validation | `main_secure.py` | Validates Host header in production |
| Cache error handling | `cache.py` | Improved error handling |
| Type hints | All files | Added comprehensive type annotations |

---

## File Mapping

### New Secure Files (do not modify directly)

```
backend/app/core/config_secure.py              → Enhanced configuration
backend/app/core/security_secure.py            → JWT & rate limiting
backend/app/core/database_secure.py            → Connection pooling
backend/app/main_secure.py                     → Security middleware
backend/app/websocket/socket_manager_secure.py → Auth WebSockets
backend/app/api/auth_secure.py                 → Secure auth endpoints
backend/app/services/line_oauth_secure.py      → Enhanced OAuth
backend/app/models/models_secure.py            → Indexed models
backend/migrate_indexes.py                     → Index migration script
```

### Configuration Files

```
nginx/nginx.conf                               → Production Nginx config
frontend/Dockerfile.prod                       → Optimized frontend build
frontend/next.config.js                        → Security headers & standalone
```

### Documentation

```
AUDIT_REPORT.md                                → Full security audit
DEPLOYMENT.md                                  → Deployment guide
SECURITY.md                                    → Security checklist & guide
SECURITY_FIXES.md                              → This file
```

---

## Quick Start for Production

### 1. Apply Security Fixes

```bash
cd ~/.openclaw/workspace/projects/badminton_app_local/backend/app

# Backup originals
mkdir -p backups
cp core/config.py core/security.py core/database.py main.py backups/ 2>/dev/null || true

# Apply fixes
cp core/config_secure.py core/config.py
cp core/security_secure.py core/security.py
cp core/database_secure.py core/database.py
cp main_secure.py main.py
cp websocket/socket_manager_secure.py websocket/socket_manager.py
cp api/auth_secure.py api/auth.py
cp services/line_oauth_secure.py services/line_oauth.py
cp models/models_secure.py models/models.py
```

### 2. Generate Secure Secrets

```bash
# Generate strong secret key
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Example output:
# X7k9mP2qRsTuVwXyZaBcDeFgHiJkLmNoPqRsTuVwXyZaBcDeFgHiJkLmN
```

### 3. Set Environment Variables

```bash
# Critical - DO NOT SKIP
export ENVIRONMENT=production
export DEBUG=false
export SECRET_KEY=<your-64-char-generated-secret>
export CORS_ORIGINS_STR=https://yourdomain.com
export LINE_REDIRECT_URI=https://yourdomain.com/api/v1/auth/line/callback

# Database (use your provider's URL)
export DATABASE_URL=postgresql+asyncpg://user:pass@host/db?ssl=require
export REDIS_URL=redis://user:pass@host:6379/0

# LINE OAuth
export LINE_CHANNEL_ID=your-line-channel-id
export LINE_CHANNEL_SECRET=your-line-channel-secret
```

### 4. Run Database Migrations

```bash
cd backend

# Run Alembic migrations
alembic upgrade head

# Add performance indexes
python migrate_indexes.py --all
```

### 5. Deploy

Choose one deployment option:

**Option A: Vercel + Render**
```bash
# See DEPLOYMENT.md for detailed steps
# Quick summary:
# 1. Deploy backend to Render
# 2. Deploy frontend to Vercel
# 3. Configure environment variables
# 4. Update CORS origins
```

**Option B: Single VPS**
```bash
# See DEPLOYMENT.md for detailed steps
docker-compose -f docker-compose.prod.yml up -d --build
```

**Option C: Railway**
```bash
# See DEPLOYMENT.md for detailed steps
# Railway auto-deploys on git push
```

---

## Verification Checklist

After deployment, verify:

### Security
- [ ] HTTPS enforced (no HTTP access)
- [ ] Security headers present (`X-Frame-Options`, `HSTS`, etc.)
- [ ] CORS only allows your domain
- [ ] Rate limiting active (test with rapid requests)
- [ ] No debug info in error messages

### Functionality
- [ ] `/health` endpoint returns healthy
- [ ] LINE OAuth flow works end-to-end
- [ ] Registration/login work
- [ ] WebSocket connections authenticate
- [ ] Database queries are fast (< 100ms)

### Performance
- [ ] Response times < 200ms for API calls
- [ ] Static assets cached
- [ ] Gzip compression enabled
- [ ] Database indexes created

---

## Rollback Plan

If issues occur:

```bash
# 1. Stop services
docker-compose -f docker-compose.prod.yml down

# 2. Restore original files (if backed up)
cd backend/app
cp backups/config.py core/config.py
cp backups/security.py core/security.py
# ... restore other files

# 3. Restart with original code
docker-compose -f docker-compose.prod.yml up -d

# 4. Check logs for errors
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Support

For issues or questions:

1. Check `DEPLOYMENT.md` for troubleshooting
2. Review `AUDIT_REPORT.md` for security details
3. Consult `SECURITY.md` for best practices

---

*Last updated: 2025-02-12*
