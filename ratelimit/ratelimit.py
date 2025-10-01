from starlette.types import ASGIApp, Receive, Scope, Send
from fastapi import Request, HTTPException
from ratelimit.ratelimitutility import RateLimitUtility

class RateLimitMiddleware:
    def __init__(self, app: ASGIApp, max_requests: int, window_seconds: int):
        self.app = app
        self.rate_limiter = RateLimitUtility(max_requests, window_seconds)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            identifier = request.client.host
            if not self.rate_limiter.allow_request(identifier):
                raise HTTPException(status_code=429, detail="Too Many Requests")
        await self.app(scope, receive, send)
