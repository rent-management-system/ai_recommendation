from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import recommendation
from app.core.logging import setup_logging
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis
from app.config import settings

app = FastAPI(title="AI Recommendation Microservice")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://*.huggingface.co", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(recommendation.router)

@app.on_event("startup")
async def startup_event():
    setup_logging()
    redis = Redis.from_url(settings.REDIS_URL)
    await FastAPILimiter.init(redis)
