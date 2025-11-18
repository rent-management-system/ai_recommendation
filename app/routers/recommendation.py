from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.schemas.property_search import PropertySearchRequest, PropertySearchResponse
from app.services.langgraph_agent import run_recommendation_agent
from app.services.rag import save_tenant_preference
from app.config import settings
from app.services.property_search import generate_sql_query, execute_sql_query
from app.dependencies.auth import get_current_user
from app.database import get_session
from structlog import get_logger
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant_profile import RecommendationLog
from sqlalchemy import select

logger = get_logger()
router = APIRouter(prefix="/api/v1", tags=["recommendation"])

@router.post("/recommendations", response_model=dict, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def get_recommendations(request: RecommendationRequest, user_coroutine: dict = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    user = await user_coroutine # Await the user coroutine
    if user["role"].lower() != "tenant":
        raise HTTPException(status_code=403, detail="Only Tenants can get recommendations")
    try:
        # Always save tenant preference; read-only applies to base tables (e.g., properties), not logs/preferences
        tenant_preference_id = await save_tenant_preference(user["user_id"], request, db)
        recommendations = await run_recommendation_agent(
            tenant_preference_id=tenant_preference_id,
            user_id=user["user_id"],
            job_school_location=request.job_school_location,
            salary=request.salary,
            house_type=request.house_type,
            family_size=request.family_size,
            preferred_amenities=request.preferred_amenities,
            language=request.language,
            db=db
        )
        logger.info("Recommendations generated", user_id=user["user_id"], tenant_preference_id=tenant_preference_id, count=len(recommendations))
        return {
            "recommendations": recommendations,
            "total_budget_suggestion": request.salary * 0.3
        }
    except Exception as e:
        logger.error("Recommendation failed", user_id=user["user_id"], error=str(e))
        raise HTTPException(status_code=500, detail="Recommendation failed")

@router.get("/recommendations/{tenant_preference_id}", response_model=List[RecommendationResponse])
async def get_saved_recommendations(tenant_preference_id: int, user_coroutine: dict = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    user = await user_coroutine # Await the user coroutine
    if user["role"].lower() != "tenant":
        raise HTTPException(status_code=403, detail="Only Tenants can view recommendations")
    result = await db.execute(
        select(RecommendationLog).where(RecommendationLog.tenant_preference_id == tenant_preference_id)
    )
    logs = result.scalars().all()
    return [log.recommendation for log in logs]

@router.post("/recommendations/feedback", response_model=dict)
async def feedback(request: dict, user_coroutine: dict = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    user = await user_coroutine # Await the user coroutine
    if user["role"].lower() != "tenant":
        raise HTTPException(status_code=403, detail="Only Tenants can provide feedback")
    # Feedback is allowed; it writes to logs, not base property data
    if "tenant_preference_id" not in request or "property_id" not in request or "liked" not in request:
        raise HTTPException(status_code=422, detail="Missing required fields")
    log = RecommendationLog(tenant_preference_id=request["tenant_preference_id"], feedback=request)
    db.add(log)
    await db.commit()
    return {"message": "Feedback recorded"}

@router.post("/properties/search", response_model=PropertySearchResponse)
async def search_properties(request: PropertySearchRequest, user_coroutine: dict = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    user = await user_coroutine # Await the user coroutine
    if user["role"] not in ["Tenant", "Landlord"]: # Allow both tenants and landlords to search
        raise HTTPException(status_code=403, detail="Only Tenants and Landlords can search properties")
    try:
        sql_query = await generate_sql_query(request.query)
        properties = await execute_sql_query(sql_query, db)
        logger.info("Property search executed", user_id=user["user_id"], query=request.query, result_count=len(properties))
        return PropertySearchResponse(results=properties)
    except ValueError as ve:
        logger.error("SQL query generation failed", user_id=user["user_id"], query=request.query, error=str(ve))
        raise HTTPException(status_code=400, detail=f"Invalid search query: {ve}")
    except Exception as e:
        logger.error("Property search failed", user_id=user["user_id"], query=request.query, error=str(e))
        raise HTTPException(status_code=500, detail="Property search failed")

