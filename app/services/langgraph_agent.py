from langgraph.graph import StateGraph, END
from app.services.gebeta import get_matrix
from app.services.rag import retrieve_relevant_properties, setup_vector_store
from app.services.gemini import generate_reason
from app.services.search import search_properties
from app.models.tenant_profile import RecommendationLog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.config import settings
from structlog import get_logger
from typing import Dict, List, Any
from pydantic import BaseModel
import json
import pandas as pd
from langchain_core.runnables import RunnableLambda # Added import

logger = get_logger()

# Define the AgentState Pydantic model
class AgentState(BaseModel):
    tenant_preference_id: int
    user_id: str
    job_school_location: str
    salary: float
    house_type: str
    family_size: int
    preferred_amenities: List[str]
    language: str
    # db: AsyncSession # Removed from state
    coords: Dict[str, float] = None
    properties: List[Dict[str, Any]] = []
    transport_costs: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []

    class Config:
        arbitrary_types_allowed = True # Still needed for other arbitrary types if any

async def geocode_step(state: AgentState, config: Dict[str, Any]):
    db: AsyncSession = config["configurable"]["db"]
    state.coords = {"lat": 9.0, "lon": 38.7} # Fallback coordinates, geocoding skipped due to free plan limitations
    logger.warning("Geocoding skipped, using fallback coordinates", location=state.job_school_location, coords=state.coords)
    return state

async def search_step(state: AgentState, config: Dict[str, Any]): # Added config
    db: AsyncSession = config["configurable"]["db"] # Access db from config
    try:
        results = await search_properties(
            location=state.job_school_location,
            min_price=0.2 * state.salary,
            max_price=0.3 * state.salary,
            house_type=state.house_type,
            bedrooms=state.family_size,
            preferred_amenities=state.preferred_amenities,
            user_lat=state.coords["lat"],
            user_lon=state.coords["lon"],
            status="APPROVED"
        )
        # Keep only APPROVED properties
        results = [p for p in results if str(p.get("status", "")).upper() == "APPROVED"]
        # Fallback 1: Broaden filters if fewer than 3 results
        if len(results) < 3:
            try:
                broader = await search_properties(
                    location=state.job_school_location,
                    min_price=0.1 * state.salary,
                    max_price=0.5 * state.salary,
                    house_type=None,
                    bedrooms=None,
                    preferred_amenities=None,
                    user_lat=state.coords["lat"],
                    user_lon=state.coords["lon"],
                    status="APPROVED"
                )
                broader = [p for p in broader if str(p.get("status", "")).upper() == "APPROVED"]
                # Combine while preserving uniqueness by id
                seen = {p.get("id") for p in results}
                for p in broader:
                    if p.get("id") not in seen:
                        results.append(p)
                        seen.add(p.get("id"))
            except Exception as ee:
                logger.warning("Broader search failed", user_id=state.user_id, error=str(ee))

        # Fallback 2: DB-level fallback if still fewer than 3
        if len(results) < 3:
            try:
                min_p = 0.1 * state.salary
                max_p = 0.6 * state.salary
                # Try to fetch APPROVED properties from DB near the location (ILIKE) and within price band
                sql = text(
                    """
                    SELECT id, title, location, price, house_type, bedrooms, amenities, lat, lon, status
                    FROM properties
                    WHERE status = 'APPROVED'
                      AND price BETWEEN :min_price AND :max_price
                      AND (location ILIKE :loc OR :loc = '')
                    ORDER BY random()
                    LIMIT 10
                    """
                )
                loc_pattern = f"%{state.job_school_location}%" if state.job_school_location else ""
                result = await db.execute(sql, {"min_price": min_p, "max_price": max_p, "loc": loc_pattern})
                rows = result.fetchall()
                cols = result.keys()
                db_props = [dict(zip(cols, row)) for row in rows]
                # Merge unique by id
                seen = {p.get("id") for p in results}
                for p in db_props:
                    if p.get("id") not in seen:
                        results.append(p)
                        seen.add(p.get("id"))
            except Exception as ee:
                logger.warning("DB fallback search failed", user_id=state.user_id, error=str(ee))

        state.properties = results[:10] or []
        logger.debug(
            "Search properties results",
            user_id=state.user_id,
            results_type=type(results),
            results_len=len(results),
            state_properties_len=len(state.properties)
        )
    except Exception as e:
        state.properties = []
        logger.warning("Search failed, returning empty properties", user_id=state.user_id, error=str(e))
    return state

async def transport_cost_step(state: AgentState, config: Dict[str, Any]): # Added config
    db: AsyncSession = config["configurable"]["db"] # Access db from config
    if not state.properties:
        state.transport_costs = []
        logger.debug("No properties found, skipping transport cost calculation", user_id=state.user_id)
        return state
    with open("train_data/transport_price_data.json", "r") as f:
        transport_data = pd.DataFrame(json.load(f))
    destinations = [(p["lat"], p["lon"]) for p in state.properties if p.get("lat") and p.get("lon")]
    state.transport_costs = []
    if destinations:
        try:
            distances = await get_matrix(state.coords["lat"], state.coords["lon"], destinations)
            logger.debug("Get matrix results", user_id=state.user_id, distances_type=type(distances), distances_len=len(distances) if distances else 0)
            for prop, distance in zip(state.properties, distances):
                distance_km = distance["distance"] / 1000
                route = f"{state.job_school_location} to {prop['location']}"
                matching_routes = transport_data[
                    (transport_data["source"].str.contains(state.job_school_location, case=False)) &
                    (transport_data["destination"].str.contains(prop["location"], case=False))
                ]
                fare = matching_routes["price"].iloc[0] if not matching_routes.empty else 10.0
                monthly_cost = fare * 2 * 20  # Round-trip, 20 days/month
                state.transport_costs.append({"property_id": prop["id"], "cost": monthly_cost, "distance_km": distance_km})
            logger.debug("Transport costs calculated", user_id=state.user_id, state_transport_costs_len=len(state.transport_costs))
        except Exception as e:
            logger.warning("Matrix API failed, using fallback fares", user_id=state.user_id, error=str(e))
            for prop in state.properties:
                state.transport_costs.append({"property_id": prop["id"], "cost": 50.0, "distance_km": 5.0})
    return state

async def rank_step(state: AgentState, config: Dict[str, Any]): # Added config
    db: AsyncSession = config["configurable"]["db"] # Access db from config
    if not state.properties:
        state.recommendations = []
        logger.debug("No properties found, skipping ranking", user_id=state.user_id)
        return state
    # Adjust weights based on feedback (example: increase proximity if preferred)
    feedback_weights = {"proximity": 0.4, "affordability": 0.3, "family_fit": 0.3}
    feedback_logs = await db.execute(
        select(RecommendationLog.feedback).where(RecommendationLog.tenant_preference_id == state.tenant_preference_id)
    )
    feedbacks = feedback_logs.scalars().all()
    liked_count = sum(1 for f in feedbacks if f and f.get("liked", False))
    if liked_count > 0:
        feedback_weights["proximity"] += 0.1
        feedback_weights["affordability"] -= 0.05
        feedback_weights["family_fit"] -= 0.05
    ranked = sorted(state.properties, key=lambda p: (
        next((tc["distance_km"] for tc in state.transport_costs if tc["property_id"] == p["id"]), 5.0) * feedback_weights["proximity"] +
        (p["price"] / state.salary) * feedback_weights["affordability"] +
        (abs(p["bedrooms"] - state.family_size) * feedback_weights["family_fit"])
    ))[:3]
    state.recommendations = ranked
    logger.debug("Properties ranked", user_id=state.user_id, state_recommendations_len=len(state.recommendations))
    return state

async def reason_step(state: AgentState, config: Dict[str, Any]): # Added config
    db: AsyncSession = config["configurable"]["db"] # Access db from config
    if not state.recommendations:
        state.recommendations = []
        logger.debug("No recommendations to reason about", user_id=state.user_id)
        return state
    
    new_recommendations = []
    for prop in state.recommendations:
        transport_cost = next((tc["cost"] for tc in state.transport_costs if tc["property_id"] == prop["id"]), 50.0)
        reason_text = await generate_reason(state, prop, transport_cost, state.language)
        logger.debug("Generated reason for property", user_id=state.user_id, property_id=prop.get("id"), reason=reason_text)
        new_recommendations.append(
            {
                **prop,
                "transport_cost": transport_cost,
                "affordability_score": 1 - (prop["price"] / (state.salary * 0.3)),
                "reason": reason_text,
                "map_url": f"https://api.gebeta.app/tiles/{prop['lat']}/{prop['lon']}/15"
            }
        )
    state.recommendations = new_recommendations
    
    log = RecommendationLog(
        tenant_preference_id=state.tenant_preference_id,
        recommendation=state.recommendations,
        feedback=None
    )
    db.add(log)
    await db.commit()
    logger.debug("Recommendations and reasons generated and logged", user_id=state.user_id, state_recommendations_len=len(state.recommendations))
    return state

async def run_recommendation_agent(
    tenant_preference_id: int, user_id: str, job_school_location: str, salary: float,
    house_type: str, family_size: int, preferred_amenities: List[str], language: str,
    db: AsyncSession
) -> List[dict]:
    state = AgentState(
        tenant_preference_id=tenant_preference_id,
        user_id=user_id,
        job_school_location=job_school_location,
        salary=salary,
        house_type=house_type,
        family_size=family_size,
        preferred_amenities=preferred_amenities,
        language=language,
        # db=db # Removed from state initialization
    )
    graph = StateGraph(AgentState)
    graph.add_node("geocode", RunnableLambda(geocode_step)) # Wrapped with RunnableLambda
    graph.add_node("search", RunnableLambda(search_step)) # Wrapped with RunnableLambda
    graph.add_node("transport_cost", RunnableLambda(transport_cost_step)) # Wrapped with RunnableLambda
    graph.add_node("rank", RunnableLambda(rank_step)) # Wrapped with RunnableLambda
    graph.add_node("reason", RunnableLambda(reason_step)) # Wrapped with RunnableLambda
    graph.add_edge("geocode", "search")
    graph.add_edge("search", "transport_cost")
    graph.add_edge("transport_cost", "rank")
    graph.add_edge("rank", "reason")
    graph.add_edge("reason", END)
    graph.set_entry_point("geocode")
    compiled_graph = graph.compile()
    try:
        result = await compiled_graph.ainvoke(state, config={"configurable": {"db": db}})
        if result and hasattr(result, "recommendations"):
            return result.recommendations
        else:
            logger.error("Langgraph ainvoke returned no recommendations", user_id=user_id, result=result)
            return []
    except Exception as e:
        logger.error("Langgraph ainvoke failed", user_id=user_id, error=str(e))
        raise # Re-raise the exception to be caught by the FastAPI endpoint
