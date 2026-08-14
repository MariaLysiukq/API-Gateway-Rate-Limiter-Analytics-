import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Import the global redis_client we defined earlier
from src.db.redis import redis_client

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100):
        super().__init__(app)
        self.max_requests = max_requests

    async def dispatch(self, request: Request, call_next):
        # 1. Identify the client (using IP address for now)
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        # 2. Get the current minute (e.g., total seconds divided by 60)
        current_minute = int(time.time() // 60)
        
        # 3. Create a unique Redis key for this IP and minute bucket
        redis_key = f"rate_limit:{client_ip}:{current_minute}"
        
        try:
            # 4. Increment the counter (Redis INCR is atomic and lightning fast)
            request_count = await redis_client.incr(redis_key)
            
            # 5. If this is the first request in this minute, set an expiration
            # We set it to 60 seconds so Redis cleans up old buckets automatically
            if request_count == 1:
                await redis_client.expire(redis_key, 60)
                
            # 6. Check if they exceeded the limit
            if request_count > self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too Many Requests", 
                        "message": f"Rate limit of {self.max_requests} per minute exceeded."
                    }
                )
        except Exception as e:
            # If Redis goes down, we probably shouldn't crash the whole API.
            # Log the error and let the request pass through (fail-open).
            print(f"Redis Rate Limiter Error: {e}")
            
        # 7. If under the limit (or Redis failed), process the request normally
        response = await call_next(request)
        return response
