import os

# Settings are read at import time, so test values must exist before
# any `src` module is imported. No real database or Redis is contacted.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import fakeredis  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture
def fake_redis():
    return fakeredis.FakeAsyncRedis(decode_responses=True)


@pytest.fixture
def patch_middleware_redis(monkeypatch, fake_redis):
    """Point the global rate limit middleware at an in-memory Redis."""
    import src.middleware.rate_limit as rate_limit

    monkeypatch.setattr(rate_limit, "redis_client", fake_redis)
    return fake_redis
