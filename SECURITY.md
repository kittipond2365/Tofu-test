# Badminton Club App - Security Guide

**Version:** 1.1.0  
**Last Updated:** 2025-02-12  
**Classification:** Internal Use

---

## Quick Security Checklist

Use this checklist before deploying to production:

### 🔴 Critical (Must Fix)

- [ ] **SECRET_KEY** is at least 32 characters and randomly generated
- [ ] **DEBUG** is set to `false` in production
- [ ] **HTTPS only** - All traffic uses TLS 1.2+
- [ ] **CORS** does NOT use wildcard (`*`) when credentials are enabled
- [ ] **LINE OAuth** state parameter is validated on callback
- [ ] **Rate limiting** is enabled on all endpoints
- [ ] **Database** connection pooling is configured
- [ ] **JWT tokens** include issuer (`iss`) and audience (`aud`) claims
- [ ] **Passwords** require minimum 8 chars with uppercase, lowercase, number, special char
- [ ] **WebSocket** connections require authentication

### 🟠 High Priority

- [ ] **Security headers** are set (HSTS, CSP, X-Frame-Options, etc.)
- [ ] **Audit logging** is enabled for sensitive operations
- [ ] **Input validation** on all API endpoints
- [ ] **SQL injection** protection verified (use ORM, no raw SQL)
- [ ] **XSS protection** - No user input rendered without escaping
- [ ] **CSRF tokens** for state-changing operations
- [ ] **Session timeout** after period of inactivity
- [ ] **Account lockout** after failed login attempts
- [ ] **Sensitive data** encrypted at rest
- [ ] **API keys** not committed to version control

### 🟡 Medium Priority

- [ ] **Request size limits** configured
- [ ] **Timeout settings** on all external API calls
- [ ] **Dependency scanning** for known vulnerabilities
- [ ] **Security headers** tested with securityheaders.com
- [ ] **CORS preflight** caching configured
- [ ] **Database indexes** on frequently queried fields
- [ ] **Backup encryption** for database backups
- [ ] **Log sanitization** - No passwords/tokens in logs
- [ ] **Error messages** don't expose internal details
- [ ] **Health checks** don't expose sensitive info

### 🟢 Low Priority

- [ ] **Content Security Policy** implemented
- [ ] **Subresource Integrity** for external scripts
- [ ] **Feature Policy** / Permissions Policy set
- [ ] **Referrer Policy** configured
- [ ] **DNSSEC** enabled for domain
- [ ] **Security.txt** file present
- [ ] ** robots.txt** configured
- [ ] **Favicon** exists (prevents 404 errors)
- [ ] **Unused dependencies** removed
- [ ] **Dead code** eliminated

---

## Security Architecture

### Authentication Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│  LINE OAuth  │────▶│  Backend    │
│  (Next.js)  │     │   (LINE API) │     │  (FastAPI)  │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │   Redis     │
                                         │ (State Store)│
                                         └─────────────┘
```

### Authorization Model

| Role | Permissions |
|------|-------------|
| `admin` | Full access to club management, user management, settings |
| `organizer` | Create sessions, manage matches, view stats |
| `member` | Join sessions, view own stats, update profile |

---

## Threat Model

### Identified Threats

| Threat | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Account takeover via weak passwords | Medium | High | Strong password policy, rate limiting |
| JWT token theft | Low | High | Short expiry, secure cookies, HTTPS |
| CSRF attacks | Low | Medium | State validation, CSRF tokens |
| SQL Injection | Low | Critical | ORM usage, parameterized queries |
| XSS attacks | Medium | High | Input sanitization, CSP headers |
| DDoS attacks | Medium | Medium | Rate limiting, CDN |
| Data breach | Low | Critical | Encryption, access controls, audit logs |

---

## Secure Configuration

### Environment Variables

```bash
# Critical - Must be set correctly
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=$(openssl rand -base64 64)  # Generate strong key

# CORS - Be specific, never use wildcard with credentials
CORS_ORIGINS_STR=https://yourdomain.com

# Database - Use SSL in production
DATABASE_URL=postgresql+asyncpg://...?ssl=require

# LINE OAuth - Must use HTTPS
LINE_REDIRECT_URI=https://yourdomain.com/api/v1/auth/line/callback
```

### Password Policy

```python
# Minimum requirements:
- Length: 8+ characters
- Uppercase: 1+ (A-Z)
- Lowercase: 1+ (a-z)
- Numbers: 1+ (0-9)
- Special: 1+ (!@#$%^&*)

# Example valid password: MyP@ssw0rd
# Example invalid password: password123
```

### JWT Configuration

```python
# Security claims required:
{
  "sub": "user-id",
  "exp": 1234567890,
  "iat": 1234567890,
  "iss": "badminton-app",      # Issuer
  "aud": "badminton-api",      # Audience
  "jti": "unique-token-id",    # Token ID for revocation
  "type": "access"
}
```

---

## API Security

### Rate Limits

| Endpoint | Requests | Window |
|----------|----------|--------|
| `/auth/*` | 5 | 5 minutes |
| All other endpoints | 100 | 1 minute |
| WebSocket | 10 connections | per IP |

### Response Headers

```http
# Required security headers:
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; ...
```

### Error Responses

```json
// Safe error (production)
{
  "detail": "Invalid credentials",
  "error_code": "AUTH_001"
}

// Unsafe error (NEVER use in production)
{
  "detail": "PostgreSQL error: relation 'users' does not exist at /app/db.py:45"
}
```

---

## Data Protection

### Encryption at Rest

| Data Type | Encryption | Notes |
|-----------|------------|-------|
| Passwords | Argon2 | Industry standard |
| JWT Secrets | AES-256 | Environment variable |
| Database | SSL/TLS | In transit |
| Backups | GPG/AES | Encrypt before upload |

### Sensitive Fields

```python
# Fields that should never be logged:
SENSITIVE_FIELDS = [
    'password',
    'hashed_password',
    'token',
    'refresh_token',
    'secret_key',
    'line_channel_secret',
    'smtp_password',
    'web_push_vapid_private_key'
]
```

### Data Retention

| Data Type | Retention Period | Action After |
|-----------|------------------|--------------|
| Access logs | 90 days | Archive |
| Audit logs | 1 year | Archive |
| Session data | 7 days | Delete |
| Failed login attempts | 30 days | Delete |
| User accounts (deleted) | 30 days | Anonymize |

---

## Incident Response

### Security Incident Levels

**Level 1 (Critical):** Data breach, account takeover, system compromise
- Immediate: Isolate affected systems
- Within 1 hour: Notify team lead
- Within 24 hours: Assess impact, notify affected users

**Level 2 (High):** Unauthorized access attempt, vulnerability discovered
- Within 4 hours: Investigate
- Within 24 hours: Patch or mitigate

**Level 3 (Medium):** Suspicious activity, policy violation
- Within 24 hours: Review and document
- Within 1 week: Implement preventive measures

### Response Playbook

1. **Contain**
   - Revoke compromised tokens
   - Block suspicious IPs
   - Disable affected accounts

2. **Investigate**
   - Review audit logs
   - Analyze access patterns
   - Determine attack vector

3. **Recover**
   - Patch vulnerabilities
   - Reset passwords if needed
   - Restore from clean backup

4. **Document**
   - Timeline of events
   - Actions taken
   - Lessons learned

---

## Security Testing

### Automated Scans

```bash
# Dependency vulnerabilities
pip install safety
safety check -r requirements.txt

# Python security linter
pip install bandit
bandit -r backend/app

# Container scanning
docker run --rm -v $(pwd):/app aquasec/trivy filesystem /app
```

### Manual Testing

```bash
# Test CORS
curl -H "Origin: https://evil.com" \
     -H "Access-Control-Request-Method: POST" \
     -I https://your-api.com/api/v1/clubs

# Test rate limiting
for i in {1..10}; do
  curl -w "%{http_code}\n" -o /dev/null -s \
    https://your-api.com/api/v1/auth/login
done

# Test security headers
curl -I https://your-api.com | grep -i "x-\|strict\|content-security"
```

### Penetration Testing Checklist

- [ ] Authentication bypass
- [ ] Session management flaws
- [ ] SQL injection
- [ ] XSS (reflected, stored, DOM)
- [ ] CSRF
- [ ] IDOR (Insecure Direct Object Reference)
- [ ] Security misconfigurations
- [ ] Sensitive data exposure
- [ ] Broken access control
- [ ] API security

---

## Compliance

### GDPR (EU Users)

**Required Actions:**
- [ ] Privacy policy posted
- [ ] Cookie consent implemented
- [ ] Data processing agreement signed
- [ ] Right to erasure implemented
- [ ] Data portability feature
- [ ] Breach notification procedure

### PDPA (Thailand)

**Required Actions:**
- [ ] นโยบายความเป็นส่วนตัว (Thai privacy policy)
- [ ] ความยินยอมในการเก็บข้อมูล (Consent management)
- [ ] สิทธิของเจ้าของข้อมูล (User rights)
- [ ] การแจ้งเหตุละเมิด (Breach notification)

---

## Security Contacts

| Role | Contact | Response Time |
|------|---------|---------------|
| Security Lead | security@yourdomain.com | 24 hours |
| Emergency | +66-XXX-XXX-XXXX | 4 hours |
| LINE Support | https://developers.line.me | Business hours |

---

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [LINE Login Security](https://developers.line.biz/en/docs/line-login/security/)
- [Security Headers](https://securityheaders.com/)
- [SSL Labs Test](https://www.ssllabs.com/ssltest/)

---

*This document should be reviewed quarterly and updated as threats evolve.*
