from fastapi import FastAPI
from src.core.config import settings
from src.api.v1.gateway import router as gateway_router
from src.api.v1.analytics import router as analytics_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(gateway_router, prefix="/api/v1", tags=["Gateway"])
app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
    }


from fastapi import FastAPI
from src.middleware.rate_limit import RateLimitMiddleware

app = FastAPI(title="API Gateway")

# Register the rate limiting middleware (defaults to 100 requests/minute)
app.add_middleware(RateLimitMiddleware, max_requests=100)

@app.get("/")
async def root():
    return {"message": "API Gateway is running!"}
