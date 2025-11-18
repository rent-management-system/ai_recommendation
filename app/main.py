from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import recommendation
from app.core.logging import setup_logging
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis
from app.config import settings
from sqlalchemy import text
from app.database import AsyncSessionFactory

app = FastAPI(title="AI Recommendation Microservice")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.huggingface.co",
        "https://*.vercel.app",
        "https://*.hf.space",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(recommendation.router)

@app.on_event("startup")
async def startup_event():
    setup_logging()
    # Initialize rate limiter only if Redis is available; skip gracefully on failure
    try:
        if settings.REDIS_URL:
            redis = Redis.from_url(settings.REDIS_URL)
            await FastAPILimiter.init(redis)
    except Exception as e:
        # Running without rate limiter
        pass


@app.get("/health", tags=["health"])
async def health():
    details = {"status": "ok"}
    # Check DB connectivity
    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        details["database"] = "up"
    except Exception as e:
        details["status"] = "degraded"
        details["database"] = f"down: {str(e)}"
    # Config presence checks (no secrets exposed)
    details["config"] = {
        "db_url_set": bool(settings.DATABASE_URL),
        "redis_url_set": bool(settings.REDIS_URL),
        "gebeta_key_set": settings.GEBETA_API_KEY not in (None, "", "your_gebeta_key"),
        "gemini_key_set": settings.GEMINI_API_KEY not in (None, "", "your_gemini_key"),
    }
    # Approved properties count
    try:
        async with AsyncSessionFactory() as session:
            result = await session.execute(text("SELECT COUNT(1) FROM properties WHERE status = 'APPROVED'"))
            count = result.scalar() or 0
        details["approved_properties_count"] = int(count)
    except Exception as e:
        details["approved_properties_count"] = f"error: {str(e)}"
    return details
