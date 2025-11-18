import httpx
from app.config import settings
from structlog import get_logger
from typing import List, Optional
from pybreaker import CircuitBreaker

logger = get_logger()
breaker = CircuitBreaker(fail_max=3, reset_timeout=60)

@breaker
async def search_properties(
    location: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    house_type: Optional[str] = None,
    bedrooms: Optional[int] = None,
    preferred_amenities: Optional[List[str]] = None,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    status: Optional[str] = None
) -> List[dict]:
    async with httpx.AsyncClient() as client:
        params = {
            "location": location,
            "min_price": min_price,
            "max_price": max_price,
            "house_type": house_type,
            "bedrooms": bedrooms,
            "amenities": preferred_amenities,
            "user_lat": user_lat,
            "user_lon": user_lon,
            "status": status
        }
        response = await client.get(f"{settings.SEARCH_FILTERS_URL}/api/v1/search", params=params)
        if response.status_code != 200:
            logger.error("Search failed", status_code=response.status_code)
            raise ValueError("Search failed")
        return response.json()["results"]
