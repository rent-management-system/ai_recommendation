import httpx
from app.config import settings
from app.utils.retry import retry_api
from structlog import get_logger
from pybreaker import CircuitBreaker

logger = get_logger()
breaker = CircuitBreaker(fail_max=3, reset_timeout=60)

@retry_api(tries=3, delay=1, backoff=2)
@breaker
async def geocode(query: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.gebeta.app/geocode",
            params={"query": query},
            headers={"X-Gebeta-API-Key": settings.GEBETA_API_KEY}
        )
        if response.status_code != 200:
            await logger.error("Geocoding failed", query=query, status_code=response.status_code)
            raise ValueError("Geocoding failed")
        return response.json()[0]

@retry_api(tries=3, delay=1, backoff=2)
@breaker
async def get_matrix(lat: float, lon: float, destinations: list[tuple[float, float]]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.gebeta.app/matrix",
            params={"origins": f"{lat},{lon}", "destinations": ";".join(f"{d[0]},{d[1]}" for d in destinations)},
            headers={"X-Gebeta-API-Key": settings.GEBETA_API_KEY}
        )
        if response.status_code != 200:
            await logger.error("Matrix failed", status_code=response.status_code)
            raise ValueError("Matrix failed")
        return response.json()["distances"]
