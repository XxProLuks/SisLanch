"""
LANCH - Rate Limiting Middleware
Protects against brute-force attacks and API abuse
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.LOGIN_RATE_LIMIT}/minute"],
    storage_uri="memory://",  # Use in-memory storage (for production, use Redis)
    strategy="fixed-window"
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors
    """
    client_ip = get_remote_address(request)
    
    logger.warning(
        f"Rate limit exceeded for IP {client_ip} on {request.url.path}",
        extra={"ip": client_ip, "path": request.url.path}
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Muitas tentativas. Por favor, aguarde alguns minutos e tente novamente.",
            "retry_after": exc.detail
        },
        headers={"Retry-After": str(settings.RATE_LIMIT_PERIOD)}
    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track and log rate limit hits
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except RateLimitExceeded as exc:
            return await rate_limit_exceeded_handler(request, exc)
