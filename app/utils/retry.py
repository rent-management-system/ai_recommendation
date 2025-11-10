from functools import wraps
from structlog import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger()

def retry_api(tries: int = 3, delay: float = 1, backoff: float = 2):
    def decorator(func):
        @wraps(func)
        @retry(stop=stop_after_attempt(tries), wait=wait_exponential(multiplier=delay, exp_base=backoff))
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                await logger.warning("Retry attempt", func=func.__name__, error=str(e))
                raise
        return wrapper
    return decorator
