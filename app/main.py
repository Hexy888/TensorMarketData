"""
TensorMarketData - Main FastAPI Application
Human-Verified B2B Prospect Leads Service
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi as get_openapi_schema
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.supabase import supabase, check_health
from app.api.v1 import endpoints_router, submission_router, auth_router
# from app.api.v1.billing import router as billing_router
# from app.api.v1.payments import router as payments_router
from app.api.v1.webhooks import router as webhooks_router
# from app.api.v1.email import router as email_router  # Disabled - needs supabase fix
from app.api.v1.leads import router as leads_router
from app.api.v1.orders import router as orders_router
from app.api.v1.checkout import router as checkout_router
from app.api.v1.onboarding import router as onboarding_router
# from app.api.v1.agents import router as agents_router

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
    description="Human-Verified B2B Prospect Leads for Outbound Sales",
    version="0.2.0",
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

# Agent Discovery Routes - defined early for testing
# Nova - testing route registration

# Seed endpoint for testing
@app.post("/v1/admin/seed")
async def seed_data():
    """Seed sample companies (for testing)"""
    from app.core.supabase import supabase
    
    companies = [
        {"name": "Stripe", "domain": "stripe.com", "industry": "FinTech", "description": "Payment processing platform"},
        {"name": "Twilio", "domain": "twilio.com", "industry": "Cloud Communications", "description": "Cloud communications platform"},
        {"name": "Shopify", "domain": "shopify.com", "industry": "E-commerce", "description": "E-commerce platform"},
        {"name": "Slack", "domain": "slack.com", "industry": "Enterprise Software", "description": "Business messaging platform"},
        {"name": "Zoom", "domain": "zoom.us", "industry": "Video Communications", "description": "Video conferencing"},
        {"name": "Datadog", "domain": "datadoghq.com", "industry": "Monitoring", "description": "Cloud monitoring platform"},
        {"name": "Snowflake", "domain": "snowflake.com", "industry": "Data Cloud", "description": "Data cloud platform"},
        {"name": "Cloudflare", "domain": "cloudflare.com", "industry": "Security", "description": "Web infrastructure company"},
        {"name": "Notion", "domain": "notion.so", "industry": "Productivity", "description": "All-in-one workspace"},
        {"name": "Figma", "domain": "figma.com", "industry": "Design Tools", "description": "Design and prototyping"},
    ]
    
    added = 0
    for c in companies:
        try:
            await supabase.query("suppliers", method="POST", data={
                "name": c["name"],
                "contact_json": {"email": f"info@{c['domain']}", "phone": None, "linkedin": None},
                "verification_score": 0.9,
            })
            added += 1
        except Exception as e:
            print(f"Error adding {c['name']}: {e}")
    
    return {"added": added, "message": f"Added {added} companies"}


# SEO: Root-level robots.txt and sitemap.xml (using APIRouter)
from fastapi import APIRouter

seo_router = APIRouter()

@seo_router.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    """Robots.txt for SEO"""
    return "User-agent: *\nAllow: /\nSitemap: https://tensormarketdata.com/static/sitemap.xml"

@seo_router.get("/sitemap.xml", response_class=PlainTextResponse)  
async def sitemap():
    """XML sitemap for SEO"""
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://tensormarketdata.com/</loc></url></urlset>'

@seo_router.get("/test-seo-route")
async def test_seo():
    """Test SEO route"""
    return {"status": "ok"}


# Note: /robots.txt and /sitemap.xml at root level aren't working on Render
# Using /static/robots.txt and /static/sitemap.xml instead


# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serve home page"""
    with open(os.path.join(TEMPLATES_DIR, "index.html"), "r") as f:
        return f.read()


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "version": "0.2.0"}


# Legacy routes - redirect to home
@app.get("/index")
@app.get("/docs")
@app.get("/docs/api")
@app.get("/docs/agent-integration")
@app.get("/version-test")
@app.get("/dashboard")
@app.get("/explorer")
@app.get("/signup")
@app.get("/login")
@app.get("/submit")
@app.get("/quickstart")
@app.get("/coverage")
@app.get("/changelog")
@app.get("/status")
@app.get("/support")
@app.get("/console")
@app.get("/providers")
@app.get("/bot")
@app.get("/v1/nova-test")
@app.get("/test-deploy-abc123")
async def redirect_to_home():
    """Redirect legacy routes to home"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/", status_code=301)

@app.get("/pricing", response_class=HTMLResponse)
async def pricing():
    """Pricing page - uses template file"""
    with open(os.path.join(TEMPLATES_DIR, "pricing.html"), "r") as f:
        return f.read()


@app.get("/how-it-works", response_class=HTMLResponse)
async def how_it_works():
    """How it works page"""
    with open(os.path.join(TEMPLATES_DIR, "how-it-works.html"), "r") as f:
        return f.read()


@app.get("/contact", response_class=HTMLResponse)
async def contact():
    """Contact page"""
    with open(os.path.join(TEMPLATES_DIR, "contact.html"), "r") as f:
        return f.read()

@app.get("/blog", response_class=HTMLResponse)
async def blog_index():
    """Blog index page"""
    with open(os.path.join(TEMPLATES_DIR, "blog/index.html"), "r") as f:
        return f.read()

@app.get("/blog/response-time-matters", response_class=HTMLResponse)
async def blog_post_response_time():
    """Blog post: Why Response Time Matters"""
    with open(os.path.join(TEMPLATES_DIR, "blog/response-time-matters.html"), "r") as f:
        return f.read()

@app.get("/thank-you", response_class=HTMLResponse)
async def thank_you(request: Request):
    """Thank you page after checkout"""
    with open(os.path.join(TEMPLATES_DIR, "thank-you.html"), "r") as f:
        return f.read()


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding(request: Request):
    """Onboarding form page"""
    with open(os.path.join(TEMPLATES_DIR, "onboarding.html"), "r") as f:
        return f.read()


@app.get("/access", response_class=HTMLResponse)
async def access(request: Request):
    """Access checklist page"""
    with open(os.path.join(TEMPLATES_DIR, "access.html"), "r") as f:
        return f.read()


@app.get("/get-started", response_class=HTMLResponse)
async def get_started():
    """Get started page - paid order form"""
    with open(os.path.join(TEMPLATES_DIR, "get-started.html"), "r") as f:
        return f.read()


@app.get("/sample", response_class=HTMLResponse)
async def sample():
    """Sample request page"""
    with open(os.path.join(TEMPLATES_DIR, "sample.html"), "r") as f:
        return f.read()


@app.get("/sample-confirmed", response_class=HTMLResponse)
async def sample_confirmed():
    """Sample request confirmed page"""
    with open(os.path.join(TEMPLATES_DIR, "sample-confirmed.html"), "r") as f:
        return f.read()


@app.get("/order-confirmed", response_class=HTMLResponse)
async def order_confirmed():
    """Order confirmed page"""
    with open(os.path.join(TEMPLATES_DIR, "order-confirmed.html"), "r") as f:
        return f.read()


@app.get("/faq", response_class=HTMLResponse)
async def faq():
    """FAQ page"""
    with open(os.path.join(TEMPLATES_DIR, "faq.html"), "r") as f:
        return f.read()


@app.get("/terms", response_class=HTMLResponse)
async def terms():
    """Terms page"""
    with open(os.path.join(TEMPLATES_DIR, "terms.html"), "r") as f:
        return f.read()


@app.get("/privacy", response_class=HTMLResponse)
async def privacy():
    """Privacy page"""
    with open(os.path.join(TEMPLATES_DIR, "privacy.html"), "r") as f:
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


@app.get("/quickstart", response_class=HTMLResponse)
async def quickstart():
    """Quickstart guide - copy/paste snippets for agents"""
    with open(os.path.join(TEMPLATES_DIR, "quickstart.html"), "r") as f:
        return f.read()


@app.get("/coverage", response_class=HTMLResponse)
async def coverage():
    """Data coverage page"""
    with open(os.path.join(TEMPLATES_DIR, "coverage.html"), "r") as f:
        return f.read()


@app.get("/changelog", response_class=HTMLResponse)
async def changelog():
    """Changelog page"""
    with open(os.path.join(TEMPLATES_DIR, "changelog.html"), "r") as f:
        return f.read()


@app.get("/status", response_class=HTMLResponse)
async def status_page():
    """Status page - operational transparency"""
    with open(os.path.join(TEMPLATES_DIR, "status.html"), "r") as f:
        return f.read()


@app.get("/support", response_class=HTMLResponse)
async def support_page():
    """Support page"""
    with open(os.path.join(TEMPLATES_DIR, "support.html"), "r") as f:
        return f.read()


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login page - magic link auth"""
    # Use the auth_model router's HTML
    from app.api.v1.auth_model import login_page as auth_login
    return auth_login()


@app.get("/console", response_class=HTMLResponse)
async def console_page():
    """Console - auth-gated API key management"""
    with open(os.path.join(TEMPLATES_DIR, "console.html"), "r") as f:
        return f.read()


# ============ ADMIN PORTAL ============

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    """Admin dashboard"""
    with open(os.path.join(TEMPLATES_DIR, "admin", "dashboard.html"), "r") as f:
        return f.read()


# ============ CLIENT PORTAL (APP) ============

@app.get("/app", response_class=HTMLResponse)
async def app_dashboard():
    """Client portal dashboard"""
    with open(os.path.join(TEMPLATES_DIR, "app", "dashboard.html"), "r") as f:
        return f.read()


@app.get("/app/dashboard", response_class=HTMLResponse)
async def app_dashboard_alt():
    """Client portal dashboard (alt)"""
    with open(os.path.join(TEMPLATES_DIR, "app", "dashboard.html"), "r") as f:
        return f.read()


@app.get("/app/reviews", response_class=HTMLResponse)
async def app_reviews():
    """Client portal reviews"""
    with open(os.path.join(TEMPLATES_DIR, "app", "dashboard.html"), "r") as f:
        return f.read()


@app.get("/app/approvals", response_class=HTMLResponse)
async def app_approvals():
    """Client portal approvals"""
    with open(os.path.join(TEMPLATES_DIR, "app", "approvals.html"), "r") as f:
        return f.read()


@app.get("/app/reports", response_class=HTMLResponse)
async def app_reports():
    """Client portal reports"""
    with open(os.path.join(TEMPLATES_DIR, "app", "dashboard.html"), "r") as f:
        return f.read()


@app.get("/app/settings", response_class=HTMLResponse)
async def app_settings():
    """Client portal settings"""
    with open(os.path.join(TEMPLATES_DIR, "app", "settings.html"), "r") as f:
        return f.read()


@app.get("/app/billing", response_class=HTMLResponse)
async def app_billing():
    """Client portal billing"""
    with open(os.path.join(TEMPLATES_DIR, "app", "billing.html"), "r") as f:
        return f.read()


@app.get("/app/orders", response_class=HTMLResponse)
async def customer_orders_page():
    """Customer orders list"""
    with open(os.path.join(TEMPLATES_DIR, "customer-orders.html"), "r") as f:
        return f.read()


@app.get("/blog/ai-agents-b2b-data-programmatic-access", response_class=HTMLResponse)
async def blog_post():
    """SEO blog post"""
    blog_path = "/app/marketing/ai-agents-b2b-data-programmatic-access.html"
    with open(blog_path, "r") as f:
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


# Legacy API endpoints - redirect to home
@app.get("/v1/nova-test")
async def redirect_legacy():
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/", status_code=301)

@app.get("/openapi.json")
async def redirect_openapi():
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/", status_code=301)


# Include all routers
app.include_router(endpoints_router, prefix="/v1")
app.include_router(submission_router, prefix="/v1")
app.include_router(auth_router, prefix="/v1")
# app.include_router(payments_router, prefix="/v1")
app.include_router(webhooks_router, prefix="/v1")
# app.include_router(email_router, prefix="/v1")  # Disabled - needs supabase fix
app.include_router(leads_router, prefix="/v1")
app.include_router(orders_router, prefix="/v1")
app.include_router(checkout_router, prefix="/v1")
app.include_router(onboarding_router, prefix="/v1")
# app.include_router(seo_router)  # SEO: robots.txt, sitemap.xml
# app.include_router(agents_router, prefix="/v1")  # Agent Discovery
# app.include_router(analytics_router, prefix="/v1")  # Analytics
# app.include_router(portal_router)  # Portal JSON endpoints
# app.include_router(auth_model_router)  # Auth: magic link + API keys
# app.include_router(auth_contracts_router)  # Endpoint contracts
# app.include_router(billing_router)  # Billing: Stripe checkout + webhook
# app.include_router(internal_router, prefix="/internal")  # Internal service routes
# app.include_router(public_router)  # Public routes


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
