"""
TensorMarketData - Main FastAPI Application
A headless B2B data marketplace for AI agents.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.supabase import supabase, check_health
from app.api.v1 import endpoints_router, submission_router, auth_router
from app.api.v1.payments import router as payments_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.email import router as email_router

# Create templates directory path
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan - startup and shutdown events.
    """
    yield


# Create FastAPI application
app = FastAPI(
    title="TensorMarketData",
    description="Headless B2B Data Marketplace for AI Agents",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serve home page"""
    with open(os.path.join(TEMPLATES_DIR, "index.html"), "r") as f:
        return f.read()


@app.get("/health")
async def health_check():
    """Health check for Railway"""
    return {"status": "healthy", "app": "TensorMarketData"}


# HTML Routes
@app.get("/index", response_class=HTMLResponse)
async def home():
    """Home page"""
    with open(os.path.join(TEMPLATES_DIR, "index.html"), "r") as f:
        return f.read()


@app.get("/docs", response_class=HTMLResponse)
async def docs():
    """Documentation page"""
    with open(os.path.join(TEMPLATES_DIR, "docs.html"), "r") as f:
        return f.read()


@app.get("/docs/api", response_class=HTMLResponse)
async def docs_api():
    """API documentation page"""
    with open(os.path.join(TEMPLATES_DIR, "docs.html"), "r") as f:
        return f.read()


@app.get("/docs/agent-integration", response_class=HTMLResponse)
async def docs_agent_integration():
    """Agent integration guide"""
    with open(os.path.join(TEMPLATES_DIR, "docs.html"), "r") as f:
        return f.read()


@app.get("/pricing", response_class=HTMLResponse)
async def pricing():
    """Pricing page"""
    with open(os.path.join(TEMPLATES_DIR, "pricing.html"), "r") as f:
        return f.read()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Dashboard page"""
    with open(os.path.join(TEMPLATES_DIR, "dashboard.html"), "r") as f:
        return f.read()


@app.get("/explorer", response_class=HTMLResponse)
async def explorer():
    """API Explorer page"""
    with open(os.path.join(TEMPLATES_DIR, "explorer.html"), "r") as f:
        return f.read()


@app.get("/contact", response_class=HTMLResponse)
async def contact():
    """Contact sales page"""
    with open(os.path.join(TEMPLATES_DIR, "contact.html"), "r") as f:
        return f.read()


@app.get("/signup", response_class=HTMLResponse)
async def signup():
    """Sign up page"""
    with open(os.path.join(TEMPLATES_DIR, "signup.html"), "r") as f:
        return f.read()


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login page"""
    with open(os.path.join(TEMPLATES_DIR, "login.html"), "r") as f:
        return f.read()


@app.get("/submit", response_class=HTMLResponse)
async def submit():
    """Data submission page"""
    with open(os.path.join(TEMPLATES_DIR, "submit.html"), "r") as f:
        return f.read()


@app.get("/providers", response_class=HTMLResponse)
async def providers():
    """Data provider dashboard"""
    with open(os.path.join(TEMPLATES_DIR, "providers.html"), "r") as f:
        return f.read()


@app.get("/bot", response_class=HTMLResponse)
async def bot_profile():
    """Telegram bot profile page"""
    with open(os.path.join(TEMPLATES_DIR, "bot.html"), "r") as f:
        return f.read()


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler for unhandled errors.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred",
            "code": "INTERNAL_ERROR",
        },
    )


# Include API routes
app.include_router(endpoints_router, prefix="/v1")
app.include_router(submission_router, prefix="/v1")
app.include_router(auth_router, prefix="/v1")
app.include_router(payments_router, prefix="/v1")
app.include_router(webhooks_router, prefix="/v1")
app.include_router(email_router, prefix="/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
