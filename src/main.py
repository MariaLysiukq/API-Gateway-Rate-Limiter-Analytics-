from fastapi import FastAPI
from src.core.config import settings
from src.api.v1.gateway import router as gateway_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(gateway_router, prefix="/api/v1", tags=["Gateway"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
    }
