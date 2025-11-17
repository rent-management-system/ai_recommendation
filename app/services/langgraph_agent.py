from langgraph.graph import StateGraph, END
from app.services.gebeta import geocode, get_matrix
from app.services.rag import retrieve_relevant_properties, setup_vector_store
from app.services.gemini import generate_reason
from app.services.search import search_properties
from app.models.tenant_profile import RecommendationLog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from structlog import get_logger
from typing import Dict, List
import json
import pandas as pd

logger = get_logger()

async def geocode_step(state: Dict):
    try:
        state["coords"] = await geocode(state["job_school_location"])
    except Exception:
        state["coords"] = {"lat": 9.0, "lon": 38.7}  # Fallback for Addis Ababa
        await logger.warning("Geocoding failed, using fallback", location=state["job_school_location"])
    return state

async def search_step(state: Dict):
    try:
        results = await search_properties(
            location=state["job_school_location"],
            min_price=0.2 * state["salary"],
            max_price=0.3 * state["salary"],
            house_type=state["house_type"],
            bedrooms=state["family_size"],
            preferred_amenities=state["preferred_amenities"],
            user_lat=state["coords"]["lat"],
            user_lon=state["coords"]["lon"]
        )
        state["properties"] = results[:10] or []
    except Exception:
        state["properties"] = []
        await logger.warning("Search failed, returning empty properties")
    return state

async def transport_cost_step(state: Dict):
    if not state["properties"]:
        state["transport_costs"] = []
        return state
    with open("train_data/transport_price_data.json", "r") as f:
        transport_data = pd.DataFrame(json.load(f))
    destinations = [(p["lat"], p["lon"]) for p in state["properties"] if p.get("lat") and p.get("lon")]
    state["transport_costs"] = []
    if destinations:
        try:
            distances = await get_matrix(state["coords"]["lat"], state["coords"]["lon"], destinations)
            for prop, distance in zip(state["properties"], distances):
                distance_km = distance["distance"] / 1000
                route = f"{state['job_school_location']} to {prop['location']}"
                matching_routes = transport_data[
                    (transport_data["source"].str.contains(state["job_school_location"], case=False)) &
                    (transport_data["destination"].str.contains(prop["location"], case=False))
                ]
                fare = matching_routes["price"].iloc[0] if not matching_routes.empty else 10.0
                monthly_cost = fare * 2 * 20  # Round-trip, 20 days/month
                state["transport_costs"].append({"property_id": prop["id"], "cost": monthly_cost, "distance_km": distance_km})
        except Exception:
            await logger.warning("Matrix API failed, using fallback fares")
            for prop in state["properties"]:
                state["transport_costs"].append({"property_id": prop["id"], "cost": 50.0, "distance_km": 5.0})
    return state

async def rank_step(state: Dict):
    if not state["properties"]:
        state["recommendations"] = []
        return state
    # Adjust weights based on feedback (example: increase proximity if preferred)
    feedback_weights = {"proximity": 0.4, "affordability": 0.3, "family_fit": 0.3}
    db: AsyncSession = state["db"]
    feedback_logs = await db.execute(
        select(RecommendationLog.feedback).where(RecommendationLog.tenant_preference_id == state["tenant_preference_id"])
    )
    feedbacks = feedback_logs.scalars().all()
    liked_count = sum(1 for f in feedbacks if f and f.get("liked", False))
    if liked_count > 0:
        feedback_weights["proximity"] += 0.1
        feedback_weights["affordability"] -= 0.05
        feedback_weights["family_fit"] -= 0.05
    ranked = sorted(state["properties"], key=lambda p: (
        next((tc["distance_km"] for tc in state["transport_costs"] if tc["property_id"] == p["id"]), 5.0) * feedback_weights["proximity"] +
        (p["price"] / state["salary"]) * feedback_weights["affordability"] +
        (abs(p["bedrooms"] - state["family_size"]) * feedback_weights["family_fit"])
    ))[:3]
    state["recommendations"] = ranked
    return state

async def reason_step(state: Dict):
    if not state["recommendations"]:
        state["recommendations"] = []
        return state
    state["recommendations"] = [
        {
            **prop,
            "transport_cost": next((tc["cost"] for tc in state["transport_costs"] if tc["property_id"] == prop["id"]), 50.0),
            "affordability_score": 1 - (prop["price"] / (state["salary"] * 0.3)),
            "reason": await generate_reason(state, prop, next((tc["cost"] for tc in state["transport_costs"] if tc["property_id"] == prop["id"]), 50.0), state["language"]),
            "map_url": f"https://api.gebeta.app/tiles/{prop['lat']}/{prop['lon']}/15"
        }
        for prop in state["recommendations"]
    ]
    db: AsyncSession = state["db"]
    log = RecommendationLog(
        tenant_preference_id=state["tenant_preference_id"],
        recommendation=state["recommendations"],
        feedback=None
    )
    db.add(log)
    await db.commit()
    return state

async def run_recommendation_agent(
    tenant_preference_id: int, user_id: str, job_school_location: str, salary: float,
    house_type: str, family_size: int, preferred_amenities: List[str], language: str,
    db: AsyncSession
) -> List[dict]:
    state = {
        "tenant_preference_id": tenant_preference_id,
        "user_id": user_id,
        "job_school_location": job_school_location,
        "salary": salary,
        "house_type": house_type,
        "family_size": family_size,
        "preferred_amenities": preferred_amenities,
        "language": language,
        "db": db
    }
    graph = StateGraph()
    graph.add_node("geocode", geocode_step)
    graph.add_node("search", search_step)
    graph.add_node("transport_cost", transport_cost_step)
    graph.add_node("rank", rank_step)
    graph.add_node("reason", reason_step)
    graph.add_edge("geocode", "search")
    graph.add_edge("search", "transport_cost")
    graph.add_edge("transport_cost", "rank")
    graph.add_edge("rank", "reason")
    graph.add_edge("reason", END)
    graph.set_entry_point("geocode")
    result = await graph.invoke(state)
    return result["recommendations"]
