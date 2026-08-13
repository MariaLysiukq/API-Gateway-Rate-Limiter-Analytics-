from fastapi import APIRouter, Request, Depends, HTTPException, Response, status
import redis.asyncio as aioredis

from src.db.redis import get_redis
from src.services.auth import verify_api_key
from src.services.proxy import ProxyService
from src.services.rate_limiter.sliding_window import RedisSlidingWindowRateLimiter
from src.db.models import APIKey

router = APIRouter()
proxy_service = ProxyService()


@router.api_route(
    "/proxy/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    summary="Proxy requests with Rate Limiting",
)
async def proxy_endpoint(
    path: str,
    request: Request,
    api_key: APIKey = Depends(verify_api_key),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Ендпоінт, що перевіряє API key, перевіряє ліміт запитів у Redis,
    і у разі успіху проксіює запит далі.
    """
    rate_limiter = RedisSlidingWindowRateLimiter(redis)

    is_allowed, current_count = await rate_limiter.is_allowed(
        key=str(api_key.id),
        limit=api_key.rate_limit,
        window_seconds=60,
    )

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Allowed: {api_key.rate_limit} requests/min.",
            headers={"Retry-After": "60"},
        )

    status_code, headers, content = await proxy_service.forward_request(request, path)

    response_headers = dict(headers)
    response_headers["X-RateLimit-Limit"] = str(api_key.rate_limit)
    response_headers["X-RateLimit-Remaining"] = str(max(0, api_key.rate_limit - current_count))

    return Response(
        content=content,
        status_code=status_code,
        headers=response_headers,
    )
