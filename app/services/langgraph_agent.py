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
    # Try to infer coordinates from local transport data if available
    inferred = None
    try:
        with open("train_data/transport_price_data.json", "r") as f:
            transport_data = pd.DataFrame(json.load(f))
        loc = (state.job_school_location or "").strip()
        if loc and not transport_data.empty:
            mask = (
                transport_data["source"].astype(str).str.contains(loc, case=False, na=False) |
                transport_data["destination"].astype(str).str.contains(loc, case=False, na=False)
            )
            matches = transport_data[mask]
            candidates = []
            for _, row in matches.iterrows():
                # Prefer exact side matches if possible
                if isinstance(row.get("source"), str) and loc.lower() in row.get("source").lower():
                    if pd.notna(row.get("source_lat")) and pd.notna(row.get("source_lon")):
                        candidates.append((float(row.get("source_lat")), float(row.get("source_lon"))))
                if isinstance(row.get("destination"), str) and loc.lower() in row.get("destination").lower():
                    if pd.notna(row.get("dest_lat")) and pd.notna(row.get("dest_lon")):
                        candidates.append((float(row.get("dest_lat")), float(row.get("dest_lon"))))
            if not candidates:
                # Fall back to any lat/lon from matches
                for _, row in matches.iterrows():
                    if pd.notna(row.get("source_lat")) and pd.notna(row.get("source_lon")):
                        candidates.append((float(row.get("source_lat")), float(row.get("source_lon"))))
                    if pd.notna(row.get("dest_lat")) and pd.notna(row.get("dest_lon")):
                        candidates.append((float(row.get("dest_lat")), float(row.get("dest_lon"))))
            if candidates:
                avg_lat = sum(c[0] for c in candidates) / len(candidates)
                avg_lon = sum(c[1] for c in candidates) / len(candidates)
                inferred = {"lat": avg_lat, "lon": avg_lon}
    except Exception as e:
        logger.warning("Local geocode inference failed, will use fallback", error=str(e))

    if inferred:
        state.coords = inferred
        logger.debug("Geocoding inferred from transport data", location=state.job_school_location, coords=state.coords)
    else:
        state.coords = {"lat": 9.0, "lon": 38.7} # Fallback coordinates
        logger.warning("Geocoding skipped, using fallback coordinates", location=state.job_school_location, coords=state.coords)
    return state

async def search_step(state: AgentState, config: Dict[str, Any]): # Added config
    db: AsyncSession = config["configurable"]["db"] # Access db from config
    results: List[Dict[str, Any]] = []
    # Primary DB search (narrow band, APPROVED)
    try:
        min_p = 0.2 * state.salary
        max_p = 0.3 * state.salary
        loc_pattern = f"%{state.job_school_location}%" if state.job_school_location else ""
        where_clauses = [
            "status = 'APPROVED'",
            "price BETWEEN :min_price AND :max_price",
        ]
        params = {"min_price": min_p, "max_price": max_p}
        # Optional location
        where_clauses.append("(location ILIKE :loc OR :loc = '')")
        params["loc"] = loc_pattern
        # Optional house_type
        if state.house_type:
            where_clauses.append("house_type = :house_type")
            params["house_type"] = state.house_type
        # Optional amenities containment
        if state.preferred_amenities:
            params["amenities"] = json.dumps(state.preferred_amenities)
            where_clauses.append("amenities @> CAST(:amenities AS JSONB)")
        where_sql = " AND ".join(where_clauses)
        sql_primary = text(f"""
            SELECT id, title, location, price, house_type, amenities, photos AS images, lat, lon, status
            FROM properties
            WHERE {where_sql}
            ORDER BY price ASC, updated_at DESC
            LIMIT 20
        """)
        result = await db.execute(sql_primary, params)
        rows = result.fetchall()
        cols = result.keys()
        primary = [dict(zip(cols, row)) for row in rows]
        results.extend(primary)
    except Exception as e:
        await db.rollback()
        logger.warning("Primary DB search failed; will attempt fallbacks", user_id=state.user_id, error=str(e))

    # Fallback 1: Broadened DB search (wider price, relax house_type/bedrooms/amenities)
    if len(results) < 3:
        try:
            min_p = 0.1 * state.salary
            max_p = 0.5 * state.salary
            loc_pattern = f"%{state.job_school_location}%" if state.job_school_location else ""
            sql_broaden = text(
                """
                SELECT id, title, location, price, house_type, amenities, photos AS images, lat, lon, status
                FROM properties
                WHERE status = 'APPROVED'
                  AND price BETWEEN :min_price AND :max_price
                  AND (location ILIKE :loc OR :loc = '')
                ORDER BY price ASC, updated_at DESC
                LIMIT 30
                """
            )
            result = await db.execute(sql_broaden, {"min_price": min_p, "max_price": max_p, "loc": loc_pattern})
            rows = result.fetchall()
            cols = result.keys()
            broader = [dict(zip(cols, row)) for row in rows]
            seen = {p.get("id") for p in results}
            for p in broader:
                if p.get("id") not in seen:
                    results.append(p)
                    seen.add(p.get("id"))
        except Exception as ee:
            await db.rollback()
            logger.warning("Broader search failed", user_id=state.user_id, error=str(ee))

    # Fallback 2: DB-level query
    if len(results) < 3:
        try:
            min_p = 0.1 * state.salary
            max_p = 0.6 * state.salary
            sql = text(
                """
                SELECT id, title, location, price, house_type, amenities, lat, lon, status
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
            seen = {p.get("id") for p in results}
            for p in db_props:
                if p.get("id") not in seen:
                    results.append(p)
                    seen.add(p.get("id"))
        except Exception as ee:
            await db.rollback()
            logger.warning("DB fallback search failed", user_id=state.user_id, error=str(ee))

    # Fallback 3: DB wide query ignoring location (still APPROVED). First within wide price range, then any APPROVED.
    if len(results) < 3:
        try:
            min_p = 0.1 * state.salary
            max_p = 0.7 * state.salary
            sql_wide = text(
                """
                SELECT id, title, location, price, house_type, amenities, lat, lon, status
                FROM properties
                WHERE status = 'APPROVED'
                  AND price BETWEEN :min_price AND :max_price
                ORDER BY random()
                LIMIT 20
                """
            )
            result = await db.execute(sql_wide, {"min_price": min_p, "max_price": max_p})
            rows = result.fetchall()
            cols = result.keys()
            wide_props = [dict(zip(cols, row)) for row in rows]
            seen = {p.get("id") for p in results}
            for p in wide_props:
                if p.get("id") not in seen:
                    results.append(p)
                    seen.add(p.get("id"))
        except Exception as ee:
            await db.rollback()
            logger.warning("DB wide fallback failed", user_id=state.user_id, error=str(ee))

    if len(results) < 3:
        try:
            sql_any = text(
                """
                SELECT id, title, location, price, house_type, amenities, lat, lon, status
                FROM properties
                WHERE status = 'APPROVED'
                ORDER BY random()
                LIMIT 20
                """
            )
            result = await db.execute(sql_any)
            rows = result.fetchall()
            cols = result.keys()
            any_props = [dict(zip(cols, row)) for row in rows]
            seen = {p.get("id") for p in results}
            for p in any_props:
                if p.get("id") not in seen:
                    results.append(p)
                    seen.add(p.get("id"))
        except Exception as ee:
            await db.rollback()
            logger.warning("DB any-approved fallback failed", user_id=state.user_id, error=str(ee))

    state.properties = results[:10] or []
    logger.debug(
        "Search properties results",
        user_id=state.user_id,
        results_type=type(results),
        results_len=len(results),
        state_properties_len=len(state.properties)
    )
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
            # Helper: haversine distance in km
            def haversine(lat1, lon1, lat2, lon2):
                from math import radians, sin, cos, sqrt, atan2
                R = 6371.0
                dlat = radians(lat2 - lat1)
                dlon = radians(lon2 - lon1)
                a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                return R * c

            for prop, distance in zip(state.properties, distances):
                distance_km = distance["distance"] / 1000
                route = f"{state.job_school_location} to {prop['location']}"
                matching_routes = transport_data[
                    (transport_data["source"].str.contains(state.job_school_location, case=False)) &
                    (transport_data["destination"].str.contains(prop["location"], case=False))
                ]
                # If no name match, try nearest-route matching using coordinates
                if matching_routes.empty:
                    try:
                        # Ensure numeric columns exist
                        td = transport_data.copy()
                        for col in ["source_lat", "source_lon", "dest_lat", "dest_lon"]:
                            if col not in td.columns:
                                td[col] = None
                        td = td.dropna(subset=["source_lat", "source_lon", "dest_lat", "dest_lon"])
                        if not td.empty and prop.get("lat") and prop.get("lon"):
                            # Compute distance from user to source stop + property to dest stop
                            td = td.assign(
                                user_to_source_km=td.apply(lambda r: haversine(state.coords["lat"], state.coords["lon"], float(r["source_lat"]), float(r["source_lon"])), axis=1),
                            )
                            td = td.assign(
                                prop_to_dest_km=td.apply(lambda r: haversine(prop["lat"], prop["lon"], float(r["dest_lat"]), float(r["dest_lon"])), axis=1),
                            )
                            td = td.assign(total_nearness_km=td["user_to_source_km"] + td["prop_to_dest_km"])
                            # Choose the route with minimal total nearness
                            best = td.sort_values("total_nearness_km").head(1)
                            matching_routes = best
                    except Exception as ex:
                        logger.warning("Nearest-route matching failed", user_id=state.user_id, error=str(ex))

                fare = matching_routes["price"].iloc[0] if not matching_routes.empty else 10.0
                route_source = matching_routes["source"].iloc[0] if not matching_routes.empty else state.job_school_location
                route_destination = matching_routes["destination"].iloc[0] if not matching_routes.empty else prop["location"]
                monthly_cost = fare * 2 * 20  # Round-trip, 20 days/month
                state.transport_costs.append({
                    "property_id": prop["id"],
                    "cost": monthly_cost,
                    "distance_km": distance_km,
                    "fare": float(fare),
                    "route_source": route_source,
                    "route_destination": route_destination,
                })
            logger.debug("Transport costs calculated", user_id=state.user_id, state_transport_costs_len=len(state.transport_costs))
        except Exception as e:
            logger.warning("Matrix API failed, using fallback fares", user_id=state.user_id, error=str(e))
            for prop in state.properties:
                state.transport_costs.append({
                    "property_id": prop["id"],
                    "cost": 50.0,
                    "distance_km": 5.0,
                    "fare": 10.0,
                    "route_source": state.job_school_location,
                    "route_destination": prop.get("location", ""),
                })
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
    def rank_key(p: Dict[str, Any]):
        distance_component = next((tc["distance_km"] for tc in state.transport_costs if tc["property_id"] == p.get("id")), 5.0)
        # Coerce Decimal to float where needed
        try:
            price_val = float(p.get("price", 0.0))
        except Exception:
            price_val = 0.0
        affordability_component = (price_val / float(state.salary or 1.0))
        bedrooms_val = p.get("bedrooms")
        try:
            bedrooms_val = int(bedrooms_val) if bedrooms_val is not None else int(state.family_size)
        except Exception:
            bedrooms_val = int(state.family_size)
        family_fit_component = abs(bedrooms_val - int(state.family_size))
        return (
            distance_component * feedback_weights["proximity"] +
            affordability_component * feedback_weights["affordability"] +
            family_fit_component * feedback_weights["family_fit"]
        )

    ranked = sorted(state.properties, key=rank_key)[:3]
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
        tc = next((tc for tc in state.transport_costs if tc["property_id"] == prop["id"]), None)
        transport_cost = tc["cost"] if tc else 50.0
        distance_km = tc["distance_km"] if tc else 5.0
        fare = tc.get("fare") if tc else 10.0
        route_source = tc.get("route_source") if tc else state.job_school_location
        route_destination = tc.get("route_destination") if tc else prop.get("location", "")
        # Build reasoning context
        context = {
            "distance_km": distance_km,
            "monthly_transport_cost": transport_cost,
            "single_trip_fare": fare,
            "route_source": route_source,
            "route_destination": route_destination,
            "rent_price": prop.get("price"),
            "salary": state.salary,
            "family_size": state.family_size,
            "bedrooms": prop.get("bedrooms"),
            "amenities": prop.get("amenities", []),
            "house_type": prop.get("house_type"),
        }
        reason_text = await generate_reason(state, prop, transport_cost, state.language, context)
        logger.debug("Generated reason for property", user_id=state.user_id, property_id=prop.get("id"), reason=reason_text)
        new_recommendations.append(
            {
                **prop,
                "transport_cost": transport_cost,
                "affordability_score": 1 - (float(prop.get("price", 0.0)) / float((state.salary or 1.0) * 0.3)),
                "reason": reason_text,
                "reason_details": context,
                "map_url": f"https://api.gebeta.app/tiles/{prop['lat']}/{prop['lon']}/15",
                "images": prop.get("photos") or prop.get("images") or [],
                "details": {
                    "bedrooms": prop.get("bedrooms"),
                    "house_type": prop.get("house_type"),
                    "amenities": prop.get("amenities", []),
                    "location": prop.get("location"),
                },
                "route": {
                    "source": route_source,
                    "destination": route_destination,
                    "distance_km": distance_km,
                    "fare": fare,
                    "monthly_cost": transport_cost,
                }
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
