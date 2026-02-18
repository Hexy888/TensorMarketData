# Onboarding Flow Routes

from __future__ import annotations
import os
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.db import get_session
from app.models.reputation import Client, ClientLocation
from app.models.onboarding import OnboardingState
from app.services.email_sender import send_email_smtp

templates = Jinja2Templates(directory="templates")
router = APIRouter()

BASE_URL = os.getenv("BASE_URL", "https://tensormarketdata.com").rstrip("/")


def get_client_id_from_session(request: Request) -> int:
    """Get client_id from session."""
    # Check multiple sources for client_id
    if hasattr(request.state, "client_id"):
        return int(request.state.client_id)
    if hasattr(request.session, "client_id"):
        return int(request.session.get("client_id", 0))
    # Try query param for MVP
    cid = request.query_params.get("client_id")
    if cid:
        return int(cid)
    raise HTTPException(401, "not logged in")


def ensure_onboarding_row(session: Session, client_id: int) -> OnboardingState:
    row = session.exec(
        select(OnboardingState).where(OnboardingState.client_id == client_id)
    ).first()
    
    if not row:
        row = OnboardingState(client_id=client_id)
        session.add(row)
        session.commit()
        session.refresh(row)
    return row


@router.get("/app/onboarding", response_class=HTMLResponse)
def onboarding_page(request: Request, session: Session = Depends(get_session)):
    """Show onboarding checklist."""
    try:
        cid = get_client_id_from_session(request)
    except:
        return HTMLResponse("<h3>Please log in first</h3><p><a href='/login'>Login</a></p>")
    
    client = session.get(Client, cid)
    if not client:
        raise HTTPException(404, "client not found")
    
    ob = ensure_onboarding_row(session, cid)
    
    # Update status from DB
    ob.connected_google = bool(client.gbp_refresh_token)
    loc = session.exec(
        select(ClientLocation).where(ClientLocation.client_id == cid)
    ).first()
    ob.selected_location = bool(loc and loc.gbp_location_name)
    ob.updated_at = datetime.utcnow()
    session.add(ob)
    session.commit()
    
    return templates.TemplateResponse(
        "app/onboarding.html",
        {
            "request": request,
            "client": client,
            "ob": ob,
            "has_location": bool(loc and loc.gbp_location_name),
        }
    )


@router.post("/app/onboarding/go_live")
def go_live(
    request: Request,
    go_live: str = Form(default="off"),
    session: Session = Depends(get_session),
):
    """Toggle go live status."""
    cid = get_client_id_from_session(request)
    client = session.get(Client, cid)
    if not client:
        raise HTTPException(404, "client not found")
    
    ob = ensure_onboarding_row(session, cid)
    
    # Gates
    if not client.gbp_refresh_token:
        raise HTTPException(400, "Connect Google first.")
    
    loc = session.exec(
        select(ClientLocation).where(ClientLocation.client_id == cid)
    ).first()
    if not loc or not loc.gbp_location_name:
        raise HTTPException(400, "Select a location first.")
    
    ob.go_live = (go_live == "on")
    ob.updated_at = datetime.utcnow()
    session.add(ob)
    
    # Set client active if go live on
    if ob.go_live:
        client.status = "active"
        session.add(client)
    
    session.commit()
    return RedirectResponse(url="/app/onboarding", status_code=303)


# -------------------------
# Magic Link Login
# -------------------------

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """Login page."""
    html = """<!doctype html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Login</title></head>
<body style="font-family:system-ui;margin:40px;background:#0b1220;color:#e8eefc;">
<h3>Login</h3>
<form method="post" action="/login">
<input name="email" placeholder="you@business.com" style="padding:10px;width:320px;max-width:90%;border-radius:12px;border:1px solid #444;background:#1a1f2e;color:#e8eefc;"/>
<button style="padding:10px 14px;background:#4f7cff;color:white;border:none;border-radius:12px;cursor:pointer;">Send link</button>
</form></body></html>"""
    return HTMLResponse(html)


@router.post("/login")
def login_send(email: str = Form(default=""), session: Session = Depends(get_session)):
    """Send magic link."""
    email = (email or "").strip().lower()
    if not email:
        raise HTTPException(400, "missing email")
    
    client = session.exec(select(Client).where(Client.email == email)).first()
    if not client:
        # Don't leak existence
        return RedirectResponse(url="/login", status_code=303)
    
    ob = ensure_onboarding_row(session, client.id)
    token = secrets.token_urlsafe(32)
    exp = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
    
    m = ob.meta or {}
    m["login_token"] = token
    m["login_token_exp"] = exp
    ob.meta = m
    ob.updated_at = datetime.utcnow()
    session.add(ob)
    session.commit()
    
    link = f"{BASE_URL}/app/login/callback?t={token}&e={email}"
    body = f"Login link (30 minutes): {link}"
    
    try:
        send_email_smtp(to_email=email, subject="Your login link", body_text=body)
    except:
        pass  # Don't leak SMTP errors
    
    return RedirectResponse(url="/login?sent=1", status_code=303)


@router.get("/app/login/callback")
def login_callback(
    request: Request,
    t: str = "",
    e: str = "",
    session: Session = Depends(get_session),
):
    """Handle magic link callback."""
    email = (e or "").strip().lower()
    if not t or not email:
        raise HTTPException(400, "bad link")
    
    client = session.exec(select(Client).where(Client.email == email)).first()
    if not client:
        raise HTTPException(401, "invalid")
    
    ob = ensure_onboarding_row(session, client.id)
    meta = ob.meta or {}
    
    if meta.get("login_token") != t:
        raise HTTPException(401, "invalid")
    
    # Expiry check
    exp_s = meta.get("login_token_exp")
    try:
        exp_dt = datetime.fromisoformat(exp_s)
        if datetime.utcnow() > exp_dt:
            raise HTTPException(401, "expired")
    except Exception:
        raise HTTPException(401, "expired")
    
    # Success - set session (simplified for MVP)
    # In production, use proper session middleware
    # For now, redirect with client_id
    return RedirectResponse(url=f"/app/onboarding?client_id={client.id}", status_code=302)
