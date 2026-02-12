# Badminton Club App - Production Ready

**Secure | Scalable | Production-Ready**

This repository contains a comprehensive Badminton Club Management application with full security hardening and production deployment configurations.

---

## 📋 What's Been Done

### ✅ Security Audit
- **8 Critical** issues identified and fixed
- **12 High** severity issues resolved
- **15 Medium** and **10 Low** priority improvements made

### 🔒 Security Hardening
- JWT tokens with proper security claims (iss, aud, jti)
- Rate limiting on all endpoints (auth: 5/min, API: 100/min)
- CORS properly configured (no wildcards with credentials)
- LINE OAuth CSRF protection with state validation
- Database connection pooling and SSL
- Security headers (HSTS, CSP, X-Frame-Options)
- Comprehensive audit logging
- Password strength validation
- WebSocket authentication

### 🚀 Production Deployment
- **3 deployment options** documented:
  - Option A: Vercel + Render ($14-34/month)
  - Option B: Single VPS with Docker ($6/month)
  - Option C: Railway All-in-one ($5/month)
- Nginx reverse proxy with SSL
- Docker Compose production configuration
- Automated backup scripts
- Health checks and monitoring

### 📊 Performance Optimizations
- 20+ database indexes added
- Gzip compression enabled
- Connection pooling configured
- Cache decorators for API responses
- Static asset optimization

---

## 📁 Key Files

### Security Files
| File | Description |
|------|-------------|
| `AUDIT_REPORT.md` | Full security audit with severity levels |
| `SECURITY.md` | Security checklist and best practices |
| `SECURITY_FIXES.md` | Summary of all fixes applied |
| `DEPLOYMENT.md` | Comprehensive deployment guide |

### Secure Backend Files
```
backend/app/core/config_secure.py          # Enhanced configuration
backend/app/core/security_secure.py        # JWT & rate limiting
backend/app/core/database_secure.py        # Connection pooling
backend/app/main_secure.py                 # Security middleware
backend/app/websocket/socket_manager_secure.py  # Auth WebSockets
backend/app/api/auth_secure.py             # LINE OAuth fixes
backend/app/services/line_oauth_secure.py  # Enhanced OAuth
backend/app/models/models_secure.py        # Indexed models
backend/migrate_indexes.py                 # Database migration
```

### Infrastructure
```
nginx/nginx.conf                           # Production Nginx config
docker-compose.prod.yml                    # Production Docker setup
frontend/Dockerfile.prod                   # Optimized frontend build
frontend/next.config.js                    # Security headers
```

---

## 🚀 Quick Start

### 1. Apply Security Fixes

```bash
# From project root
./apply_security_fixes.sh
```

Or manually:
```bash
cd backend/app
cp core/config_secure.py core/config.py
cp core/security_secure.py core/security.py
cp core/database_secure.py core/database.py
cp main_secure.py main.py
cp websocket/socket_manager_secure.py websocket/socket_manager.py
cp api/auth_secure.py api/auth.py
cp services/line_oauth_secure.py services/line_oauth.py
cp models/models_secure.py models/models.py
```

### 2. Configure Environment

```bash
# Generate secure secret
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Create .env file
cat > .env << EOF
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-64-char-secret-here
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
REDIS_URL=redis://user:pass@host:6379/0
CORS_ORIGINS_STR=https://yourdomain.com
LINE_CHANNEL_ID=your-line-id
LINE_CHANNEL_SECRET=your-line-secret
LINE_REDIRECT_URI=https://yourdomain.com/api/v1/auth/line/callback
EOF
```

### 3. Deploy

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

**Quick Deploy to Railway:**
```bash
# Push to GitHub
git add .
git commit -m "Apply security fixes"
git push origin main

# Connect Railway to GitHub repo
# Railway auto-deploys!
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [AUDIT_REPORT.md](AUDIT_REPORT.md) | Complete security audit findings |
| [SECURITY.md](SECURITY.md) | Security checklist & compliance |
| [SECURITY_FIXES.md](SECURITY_FIXES.md) | Fix application guide |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment instructions |

---

## 🔒 Security Features

### Authentication
- ✅ JWT with secure claims (iss, aud, iat, jti)
- ✅ Argon2 password hashing
- ✅ LINE OAuth with CSRF protection
- ✅ Rate limiting (auth: 5/min, API: 100/min)
- ✅ Account lockout protection

### API Security
- ✅ CORS properly configured
- ✅ Security headers (HSTS, CSP, etc.)
- ✅ Input validation with Pydantic
- ✅ SQL injection protection (ORM only)
- ✅ Request size limits
- ✅ Audit logging

### Infrastructure
- ✅ HTTPS enforcement
- ✅ Database SSL connections
- ✅ Connection pooling
- ✅ Container security
- ✅ Network isolation

---

## 💰 Cost Comparison

| Platform | Monthly Cost | Best For |
|----------|--------------|----------|
| **Vercel + Render** | $14-34 | Quick setup, auto-scaling |
| **Single VPS** | ~$6 | Full control, lowest cost |
| **Railway** | $5 | Simplicity, all-in-one |

---

## 🧪 Testing

```bash
# Health check
curl https://yourdomain.com/health

# Test auth rate limiting
for i in {1..10}; do
  curl -w "%{http_code}\n" -o /dev/null \
    https://yourdomain.com/api/v1/auth/login
done

# Verify security headers
curl -I https://yourdomain.com | grep -i "x-\|strict\|content-security"
```

---

## 🔄 Maintenance

### Database Backups
```bash
# Automated daily backups
crontab -e
# Add: 0 2 * * * /opt/badminton-app/backup.sh
```

### Updates
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Security scan
pip install safety bandit
safety check -r requirements.txt
bandit -r backend/app
```

---

## 🆘 Troubleshooting

### Common Issues

**CORS Errors:**
- Check `CORS_ORIGINS_STR` includes exact domain
- No trailing slashes
- Must include `https://`

**LINE OAuth Fails:**
- Verify `LINE_REDIRECT_URI` uses HTTPS
- Check state parameter in Redis
- Confirm channel ID/secret

**Database Connection:**
- Verify `DATABASE_URL` format
- Check SSL requirements
- Test network connectivity

See [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section for more.

---

## 📞 Support

- **Security Issues:** Review [SECURITY.md](SECURITY.md)
- **Deployment Help:** Check [DEPLOYMENT.md](DEPLOYMENT.md)
- **Audit Details:** See [AUDIT_REPORT.md](AUDIT_REPORT.md)

---

## 📜 License

MIT License - See original repository for details.

---

## 🙏 Credits

- **Original Author:** kittipond2365
- **Security Audit & Fixes:** OpenClaw AI
- **Framework:** FastAPI + Next.js

---

*Last Updated: 2025-02-12*
