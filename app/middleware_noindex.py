from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

SENSITIVE_PREFIXES = ("/openapi.json", "/docs", "/redoc")

class NoIndexMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        resp = await call_next(request)
        if request.url.path.startswith(SENSITIVE_PREFIXES):
            resp.headers["X-Robots-Tag"] = "noindex, nofollow"
        return resp
