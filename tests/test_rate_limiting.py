import asyncio
import hashlib

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.middleware.rate_limit import RateLimitMiddleware
from src.services.auth import AuthService
from src.services.rate_limiter.sliding_window import RedisSlidingWindowRateLimiter


def test_sliding_window_allows_up_to_limit_then_blocks(fake_redis):
    async def scenario():
        limiter = RedisSlidingWindowRateLimiter(fake_redis)
        results = [await limiter.is_allowed("key-1", limit=3) for _ in range(4)]
        return results

    results = asyncio.run(scenario())

    assert [allowed for allowed, _ in results] == [True, True, True, False]
    assert results[2][1] == 3


def test_sliding_window_counts_requests_with_identical_timestamps(fake_redis, monkeypatch):
    import src.services.rate_limiter.sliding_window as sliding_window

    monkeypatch.setattr(sliding_window.time, "time", lambda: 1_700_000_000.0)

    async def scenario():
        limiter = RedisSlidingWindowRateLimiter(fake_redis)
        await limiter.is_allowed("key-2", limit=10)
        return await limiter.is_allowed("key-2", limit=10)

    allowed, count = asyncio.run(scenario())

    assert allowed is True
    assert count == 2


def test_sliding_window_keys_are_independent(fake_redis):
    async def scenario():
        limiter = RedisSlidingWindowRateLimiter(fake_redis)
        await limiter.is_allowed("a", limit=1)
        return await limiter.is_allowed("b", limit=1)

    allowed, _ = asyncio.run(scenario())

    assert allowed is True


def test_ip_middleware_returns_429_after_limit(patch_middleware_redis):
    small_app = FastAPI()
    small_app.add_middleware(RateLimitMiddleware, max_requests=2)

    @small_app.get("/ping")
    async def ping():
        return {"ok": True}

    client = TestClient(small_app)
    codes = [client.get("/ping").status_code for _ in range(3)]

    assert codes == [200, 200, 429]


def test_api_key_hash_is_sha256():
    assert AuthService.hash_key("secret") == hashlib.sha256(b"secret").hexdigest()
