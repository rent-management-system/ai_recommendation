from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.langgraph_agent import run_recommendation_agent
from app.services.rag import save_tenant_profile
from app.dependencies.auth import get_current_user
from app.config import settings
from structlog import get_logger
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.models.tenant_profile import RecommendationLog
from sqlalchemy import select

logger = get_logger()
router = APIRouter(prefix="/api/v1", tags=["recommendation"])

@router.post("/recommendations", response_model=dict, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def get_recommendations(request: RecommendationRequest, user: dict = Depends(get_current_user)):
    if user["role"] != "Tenant":
        raise HTTPException(status_code=403, detail="Only Tenants can get recommendations")
    try:
        tenant_id = await save_tenant_profile(user["id"], request)
        recommendations = await run_recommendation_agent(
            tenant_id=tenant_id,
            user_id=user["id"],
            job_school_location=request.job_school_location,
            salary=request.salary,
            house_type=request.house_type,
            family_size=request.family_size,
            preferred_amenities=request.preferred_amenities,
            language=request.language
        )
        await logger.info("Recommendations generated", user_id=user["id"], tenant_id=tenant_id, count=len(recommendations))
        return {
            "recommendations": recommendations,
            "total_budget_suggestion": request.salary * 0.3
        }
    except Exception as e:
        await logger.error("Recommendation failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail="Recommendation failed")

@router.get("/recommendations/{tenant_id}", response_model=List[RecommendationResponse])
async def get_saved_recommendations(tenant_id: int, user: dict = Depends(get_current_user)):
    if user["role"] != "Tenant":
        raise HTTPException(status_code=403, detail="Only Tenants can view recommendations")
    engine = create_async_engine(settings.DATABASE_URL)
    async with AsyncSession(engine) as db:
        result = await db.execute(
            select(RecommendationLog).where(RecommendationLog.tenant_id == tenant_id)
        )
        logs = result.scalars().all()
        return [log.recommendation for log in logs]

@router.post("/recommendations/feedback", response_model=dict)
async def feedback(request: dict, user: dict = Depends(get_current_user)):
    if user["role"] != "Tenant":
        raise HTTPException(status_code=403, detail="Only Tenants can provide feedback")
    if "tenant_id" not in request or "property_id" not in request or "liked" not in request:
        raise HTTPException(status_code=422, detail="Missing required fields")
    engine = create_async_engine(settings.DATABASE_URL)
    async with AsyncSession(engine) as db:
        log = RecommendationLog(tenant_id=request["tenant_id"], feedback=request)
        db.add(log)
        await db.commit()
        return {"message": "Feedback recorded"}
