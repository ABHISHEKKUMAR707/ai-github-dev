from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis
from config.settings import settings

redis_client = redis.from_url(settings.redis_url)

# Increased limits
RATE_LIMIT_REQUESTS = 100    # was 10, now 100
RATE_LIMIT_WINDOW   = 60     # per 60 seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for these routes
        skip_paths = [
            "/health",
            "/auth/github/login",
            "/auth/github/callback",
            "/agent/status"    # status polling should never be limited
        ]

        for path in skip_paths:
            if request.url.path.startswith(path):
                return await call_next(request)

        client_ip = request.client.host
        key       = f"rate_limit:{client_ip}"

        try:
            current = redis_client.get(key)
            if current is None:
                redis_client.setex(key, RATE_LIMIT_WINDOW, 1)
            elif int(current) >= RATE_LIMIT_REQUESTS:
                ttl = redis_client.ttl(key)
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {ttl} seconds."
                )
            else:
                redis_client.incr(key)
        except HTTPException:
            raise
        except Exception:
            pass

        return await call_next(request)
