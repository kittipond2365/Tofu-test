# 🧪 Tofu Badminton - Test Suite

Automated test suite for Tofu Badminton Club Management App.

## 🔗 Repositories

- **Production:** https://github.com/kittipond2365/tofubadminton (Private)
- **Test Suite:** https://github.com/kittipond2365/Tofu-Test (This repo)

## 🎯 Purpose

This repository contains only test files and CI/CD configuration. It does NOT contain:
- Production source code
- Database credentials
- API secrets
- Sensitive configuration

## 🚀 Running Tests

### API Tests (pytest)
```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

### E2E Tests (Playwright)
```bash
cd frontend
npm install
npx playwright test
```

## 📊 Test Targets

Tests run against production environment:
- **Frontend:** https://tofubadminton.onrender.com
- **Backend:** https://tofubadminton-backend.onrender.com

## 🔐 Test Authentication

Tests use `/auth/test-login` endpoint with protection:
- Requires `ENV=testing`
- Requires `X-Test-Secret` header
- Optional IP whitelist

## 📝 License

Test files provided for testing purposes only.
