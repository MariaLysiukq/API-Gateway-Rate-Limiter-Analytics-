from fastapi import FastAPI

from src.api.v1.analytics import router as analytics_router
from src.api.v1.gateway import router as gateway_router
from src.core.config import settings
from src.middleware.rate_limit import RateLimitMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Global per-IP fixed-window limit (defaults to 100 requests/minute).
# Per-API-key sliding-window limits are applied in the /proxy endpoint.
app.add_middleware(RateLimitMiddleware, max_requests=100)

app.include_router(gateway_router, prefix="/api/v1", tags=["Gateway"])
app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics"])


@app.get("/", tags=["Health"])
async def root():
    return {"message": "API Gateway is running!"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
    }
