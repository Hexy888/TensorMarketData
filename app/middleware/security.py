import time
from collections import defaultdict, deque
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        resp: Response = await call_next(request)
        
        # Basic hardened headers
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS only if behind HTTPS (Render is HTTPS in prod)
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP-lite
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        return resp

class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting per IP."""
    
    def __init__(self, app, window_seconds=60, max_requests=120, burst_max=25):
        super().__init__(app)
        self.window = window_seconds
        self.max_requests = max_requests
        self.burst_max = burst_max
        self.buckets = defaultdict(deque)
    
    def _ip(self, request: Request) -> str:
        xff = request.headers.get("x-forwarded-for", "")
        if xff:
            return xff.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        ip = self._ip(request)
        now = time.time()
        q = self.buckets[ip]
        
        # purge old
        while q and (now - q[0] > self.window):
            q.popleft()
        
        # Burst protection
        if len(q) >= self.burst_max and (now - q[0] < 5):
            return JSONResponse({"ok": False, "error": "rate_limited_burst"}, status_code=429)
        
        # Window protection
        if len(q) >= self.max_requests:
            return JSONResponse({"ok": False, "error": "rate_limited"}, status_code=429)
        
        q.append(now)
        return await call_next(request)
