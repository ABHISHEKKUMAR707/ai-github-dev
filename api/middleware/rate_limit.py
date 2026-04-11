from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import time
from config.settings import settings

redis_client = redis.from_url(settings.redis_url)

# Config
RATE_LIMIT_REQUESTS = 10     # max requests
RATE_LIMIT_WINDOW   = 60     # per 60 seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-user rate limiting using Redis.
    Tracks requests by IP address.
    In production: track by user_id from JWT.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check and auth routes
        if request.url.path in ["/health", "/auth/github/login", "/auth/github/callback"]:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host
        key       = f"rate_limit:{client_ip}"

        try:
            # Get current request count
            current = redis_client.get(key)

            if current is None:
                # First request — set counter with expiry
                redis_client.setex(key, RATE_LIMIT_WINDOW, 1)
            elif int(current) >= RATE_LIMIT_REQUESTS:
                # Limit exceeded
                ttl = redis_client.ttl(key)
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {ttl} seconds."
                )
            else:
                # Increment counter
                redis_client.incr(key)

        except HTTPException:
            raise
        except Exception:
            # If Redis fails, allow request through
            pass

        return await call_next(request)
