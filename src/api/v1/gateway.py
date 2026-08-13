import time
from fastapi import APIRouter, Request, Depends, HTTPException, Response, status, BackgroundTasks
import redis.asyncio as aioredis

from src.db.redis import get_redis
from src.services.auth import verify_api_key
from src.services.proxy import ProxyService
from src.services.rate_limiter.sliding_window import RedisSlidingWindowRateLimiter
from src.api.v1.analytics import record_request_analytics_task
from src.db.models import APIKey

router = APIRouter()
proxy_service = ProxyService()


@router.api_route(
    "/proxy/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    summary="Proxy requests with Rate Limiting and Analytics",
)
async def proxy_endpoint(
    path: str,
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: APIKey = Depends(verify_api_key),
    redis: aioredis.Redis = Depends(get_redis),
):
    start_time = time.perf_counter()

    rate_limiter = RedisSlidingWindowRateLimiter(redis)
    is_allowed, current_count = await rate_limiter.is_allowed(
        key=str(api_key.id),
        limit=api_key.rate_limit,
        window_seconds=60,
    )

    if not is_allowed:
        latency_ms = (time.perf_counter() - start_time) * 1000
        background_tasks.add_task(
            record_request_analytics_task,
            api_key_id=str(api_key.id),
            path=path,
            method=request.method,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            latency_ms=latency_ms,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Allowed: {api_key.rate_limit} requests/min.",
            headers={"Retry-After": "60"},
        )

    status_code, headers, content = await proxy_service.forward_request(request, path)
    latency_ms = (time.perf_counter() - start_time) * 1000

    background_tasks.add_task(
        record_request_analytics_task,
        api_key_id=str(api_key.id),
        path=path,
        method=request.method,
        status_code=status_code,
        latency_ms=latency_ms,
    )

    response_headers = dict(headers)
    response_headers["X-RateLimit-Limit"] = str(api_key.rate_limit)
    response_headers["X-RateLimit-Remaining"] = str(max(0, api_key.rate_limit - current_count))

    return Response(
        content=content,
        status_code=status_code,
        headers=response_headers,
    )
