"""Minimal in-memory rate limiter (per-process). Good enough for a student demo/local run;
a production deployment would use a shared store (e.g. Redis) behind an API gateway."""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.time()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= self.max_requests:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests - please slow down")
        hits.append(now)


auth_limiter = RateLimiter(max_requests=10, window_seconds=60)


async def limit_auth_routes(request: Request, call_next):
    if request.url.path in ("/register", "/login"):
        client = request.client.host if request.client else "unknown"
        auth_limiter.check(client)
    return await call_next(request)
