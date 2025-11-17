from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from app.config import settings
from structlog import get_logger
from pybreaker import CircuitBreaker

logger = get_logger()
security = HTTPBearer()
breaker = CircuitBreaker(fail_max=3, reset_timeout=60)

@breaker
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.USER_MANAGEMENT_URL}/auth/verify",
            headers={"Authorization": f"Bearer {credentials.credentials}"}
        )
        if response.status_code != 200:
            await logger.error("Token verification failed", status_code=response.status_code)
            raise HTTPException(status_code=401, detail="Invalid token")
        return response.json()
