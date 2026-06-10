"""Simple in-memory rate limiting (M14). Replace with Redis when REDIS_URL set."""

import time
from collections import defaultdict

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

_buckets: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if settings.rate_limit_per_minute <= 0:
            return await call_next(request)
        client = request.headers.get("authorization", request.client.host if request.client else "anon")
        now = time.time()
        window = 60.0
        hits = [t for t in _buckets[client] if now - t < window]
        if len(hits) >= settings.rate_limit_per_minute:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        hits.append(now)
        _buckets[client] = hits
        return await call_next(request)
