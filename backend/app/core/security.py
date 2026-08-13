import time
from typing import Optional
from fastapi import Request, HTTPException, status, Security
from fastapi.security import APIKeyHeader
from app.core.config import settings
from app.core.logging import logger

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Simple in-memory rate limiting dictionary (IP -> list of timestamps)
_rate_limit_store = {}


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    """
    Authentication & Authorization dependency.
    If API_KEY_REQUIRED is enabled in settings, verifies that request contains valid X-API-Key.
    """
    if settings.API_KEY_REQUIRED:
        if not api_key or api_key != settings.API_KEY:
            logger.warning(f"Unauthorized API access attempt with key: '{api_key}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key header 'X-API-Key'."
            )
    return api_key


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware protecting API routes from abuse.
    Tracks requests per IP within 60-second window.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Clean old requests older than 60s
    timestamps = _rate_limit_store.get(client_ip, [])
    timestamps = [t for t in timestamps if now - t < 60]
    _rate_limit_store[client_ip] = timestamps

    if len(timestamps) >= settings.RATE_LIMIT_PER_MINUTE:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit of {settings.RATE_LIMIT_PER_MINUTE} requests/minute exceeded."
        )

    timestamps.append(now)
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
    response.headers["X-RateLimit-Remaining"] = str(max(0, settings.RATE_LIMIT_PER_MINUTE - len(timestamps)))
    return response
