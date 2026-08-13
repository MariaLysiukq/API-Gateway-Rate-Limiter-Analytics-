import time
from typing import Tuple
import redis.asyncio as aioredis
from src.services.rate_limiter.base import BaseRateLimiter


class RedisSlidingWindowRateLimiter(BaseRateLimiter):
    """Sliding Window with Redis ZSET and Lua script."""

    LUA_SCRIPT = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local limit = tonumber(ARGV[3])
    
    local clear_before = now - window
    
    -- Delete all records that fall outside the time window
    redis.call('ZREMRANGEBYSCORE', key, '-inf', clear_before)
    
    -- Count the current number of requests within the window
    local current_requests = redis.call('ZCARD', key)
    
    if current_requests < limit then
        -- Add the current request (score = timestamp, member = timestamp)
        redis.call('ZADD', key, now, now)
        -- Update the key’s TTL so it doesn’t linger in memory indefinitely
        redis.call('EXPIRE', key, window)
        return {1, current_requests + 1}
    else
        return {0, current_requests}
    end
    """

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        # Regicter script in Redis for speed optimisation
        self.script = self.redis.register_script(self.LUA_SCRIPT)

    async def is_allowed(
        self, key: str, limit: int, window_seconds: int = 60
    ) -> Tuple[bool, int]:
        now = time.time()
        redis_key = f"rate_limit:{key}"

        # Calls Lua-script
        result = await self.script(
            keys=[redis_key],
            args=[now, window_seconds, limit],
        )

        is_allowed = bool(result[0])
        current_count = int(result[1])

        return is_allowed, current_count
