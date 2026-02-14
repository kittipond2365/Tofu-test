.PHONY: test-api test-e2e test-all

test-api:
	cd backend && PYTHONPATH=. ENV=testing REDIS_URL=redis://localhost:6379/0 python scripts/reset_test_db.py
	cd backend && PYTHONPATH=. ENV=testing REDIS_URL=redis://localhost:6379/0 pytest tests/ -v

test-e2e:
	cd frontend && npx playwright test

test-all: test-api test-e2e
	@echo "✅ All tests complete"
