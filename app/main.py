from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from app.db import create_db_and_tables
from app.routes import public, auth, app_portal, admin, api, webhooks
from app.routes import app_portal_settings
from app.routes import ops
from app.routes import ops_all
from app.routes import qa_api
from app.routes import app_switch
from app.routes import gbp
from app.routes import reconcile
from app.routes import digest_route
from app.routes import admin_auth
from app.routes import login_magic
from app.routes import outbound_ops
from app.routes import accounts_ops
from app.routes import admin_accounts
from app.routes import inbox_ops
from app.routes import gmail_push
from app.routes import gmail_watch_ops
from app.routes import autopilot_ops
from app.routes import admin_replies
from app.routes import deliverability_ops
from app.routes import reputation_ops
from app.routes import gbp_oauth
from app.routes import admin_alerts
from app.routes import onboarding_flow
from app.routes import seo_files
from app.routes import track
from app.routes import health
from app.routes import email_test
from app.routes import checkout_api
from app.routes import public_thankyou
from app.middleware.security import SecurityHeadersMiddleware, SimpleRateLimitMiddleware
from app.middleware_noindex import NoIndexMiddleware
from app.security_csrf import ensure_csrf_cookie

app = FastAPI(title="TensorMarketData")

# Security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SimpleRateLimitMiddleware, window_seconds=60, max_requests=180, burst_max=35)
app.add_middleware(NoIndexMiddleware)

# CSRF cookie middleware
class CSRFCookieMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        resp = await call_next(request)
        ctype = resp.headers.get("content-type", "")
        if request.method == "GET" and "text/html" in ctype:
            resp = ensure_csrf_cookie(resp)
        return resp

app.add_middleware(CSRFCookieMiddleware)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Redirect /get-started to pricing
from fastapi.responses import RedirectResponse

@app.get("/get-started")
def get_started():
    return RedirectResponse("/pricing", status_code=302)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(public.router)
app.include_router(auth.router)
app.include_router(app_portal.router)
app.include_router(app_portal_settings.router)
app.include_router(app_switch.router)
app.include_router(gbp.router)
app.include_router(reconcile.router)
app.include_router(digest_route.router)
app.include_router(login_magic.router)
app.include_router(seo_files.router)
app.include_router(admin_auth.router)
app.include_router(admin.router)
app.include_router(api.router)
app.include_router(ops.router)
app.include_router(ops_all.router)
app.include_router(qa_api.router)
app.include_router(track.router)
app.include_router(health.router)
app.include_router(email_test.router)
app.include_router(webhooks.router)
app.include_router(outbound_ops.router)
app.include_router(accounts_ops.router)
app.include_router(admin_accounts.router)
app.include_router(inbox_ops.router)
app.include_router(gmail_push.router)
app.include_router(gmail_watch_ops.router)
app.include_router(autopilot_ops.router)
app.include_router(admin_replies.router)
app.include_router(deliverability_ops.router)
app.include_router(reputation_ops.router)
app.include_router(gbp_oauth.router)
app.include_router(admin_alerts.router)
app.include_router(onboarding_flow.router)
app.include_router(checkout_api.router)
app.include_router(public_thankyou.router)
