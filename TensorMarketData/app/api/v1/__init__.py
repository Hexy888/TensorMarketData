"""
V1 API Routes Package
"""

from app.api.v1.endpoints import router as endpoints_router
from app.api.v1.submission import router as submission_router
from app.api.v1.auth_routes import router as auth_router

__all__ = ["endpoints_router", "submission_router", "auth_router"]
