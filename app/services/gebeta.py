import json
from typing import Optional, List, Tuple, Dict, Any

import httpx
from structlog import get_logger
from pybreaker import CircuitBreaker

from app.config import settings
from app.utils.retry import retry_api

logger = get_logger(__name__)
breaker = CircuitBreaker(fail_max=3, reset_timeout=60)

API_BASE = "https://mapapi.gebeta.app"
ONM_PATH = "/api/route/onm/"

class AuthError(Exception):
    """Raised when the remote API returns an auth / billing error (401/403)."""

    def __init__(self, message: str, status_code: int = 403):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@retry_api(tries=3, delay=1, backoff=2)
@breaker
async def get_matrix(
    lat: float,
    lon: float,
    destinations: List[Tuple[float, float]],
) -> Optional[List[Dict[str, float]]]:
    """
    Calls the ONM endpoint and returns list of {"distance": float} dicts.
    Raises AuthError for 401/403 (no retries). Raises RequestError for network transient errors.
    """
    url = f"{API_BASE}{ONM_PATH}"
    # Sanitize coordinates
    def valid_pair(a: float, b: float) -> bool:
        try:
            return -90.0 <= float(a) <= 90.0 and -180.0 <= float(b) <= 180.0
        except Exception:
            return False
    try:
        o_lat = round(float(lat), 6)
        o_lon = round(float(lon), 6)
    except Exception:
        raise ValueError("Origin coordinates invalid")
    # Enforce waypoint limit per provider docs (<= 10)
    max_waypoints = 10
    dest_list = []
    for d in destinations[:max_waypoints]:
        if isinstance(d, (list, tuple)) and len(d) == 2 and valid_pair(d[0], d[1]):
            dest_list.append({"lat": round(float(d[0]), 6), "lon": round(float(d[1]), 6)})
    if not dest_list:
        raise ValueError("No valid destination coordinates for ONM")
    # Prepare two format variants for 'json' param
    # Variant A (provider docs style): "[{lat,lon},{lat,lon}]" with lat,lon order
    doc_style = "[" + ",".join(["{" + f"{p['lat']},{p['lon']}" + "}" for p in dest_list]) + "]"
    # Variant B (JSON objects, our previous style)
    json_style = json.dumps(dest_list)

    base_params = {"origin": f"{o_lat},{o_lon}", "apiKey": settings.GEBETA_API_KEY}

    try:
        async with httpx.AsyncClient() as client:
            # Try doc-style first
            params_a = {**base_params, "json": doc_style}
            resp = await client.get(url, params=params_a, timeout=15.0, follow_redirects=True)
            status = resp.status_code
            text = resp.text

            if status in (401, 403):
                # try to extract provider message
                try:
                    j = resp.json()
                    provider_msg = (j.get("error") or {}).get("message") or j.get("message") or json.dumps(j)
                except Exception:
                    provider_msg = text or f"HTTP {status}"
                logger.error("ONM auth error", status_code=status, text=provider_msg)
                raise AuthError(message=f"ONM auth error: {provider_msg}", status_code=status)

            if status == 422 or status == 400:
                # Fallback to JSON object style
                params_b = {**base_params, "json": json_style}
                resp = await client.get(url, params=params_b, timeout=15.0, follow_redirects=True)
                status = resp.status_code
                text = resp.text
            if status != 200:
                logger.error("ONM API failed", status_code=status, text=text)
                raise ValueError(f"ONM API failed with status {status}")

            onm_response = resp.json()
            if "directions" not in onm_response or not isinstance(onm_response["directions"], list):
                logger.error("ONM API response missing 'directions'", response=onm_response)
                raise ValueError("ONM API response invalid")

            distances: List[Dict[str, float]] = []
            for direction in onm_response["directions"]:
                dist = direction.get("totalDistance") or direction.get("distance") or 0
                try:
                    dist = float(dist)
                except Exception:
                    dist = 0.0
                distances.append({"distance": dist})

            return distances

    except httpx.RequestError as exc:
        logger.exception("HTTPX request error during ONM call", exc_info=exc)
        raise
    except AuthError:
        raise
    except Exception:
        logger.exception("Unexpected error in get_matrix")
        raise