"""Test settings. These tests check the security rules only, so they don't need
a running PostgreSQL or Redis (nothing connects until a request reaches the DB)."""
import os
import sys

from cryptography.fernet import Fernet

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@127.0.0.1:1/test")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:1/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only-1234567890")
os.environ.setdefault("MASTER_ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-webhook-secret")
