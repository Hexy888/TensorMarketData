# GBP OAuth Routes

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.db import get_session
from app.models.reputation import Client, ClientLocation
from app.integrations.google_oauth import build_auth_redirect, read_state, exchange_code_for_tokens
from app.integrations.gbp_client import GBPClient

templates = Jinja2Templates(directory="templates")
router = APIRouter()


def get_client_from_session(request: Request, session: Session) -> Client:
    """Get client from session. MVP: requires session middleware."""
    # This is a placeholder - implement based on your auth system
    # For now, we'll use a simpler approach with query param
    return None


def require_client(request: Request, session: Session = Depends(get_session)) -> Client:
    """Get current client - implement session-based auth."""
    # Placeholder - replace with actual session logic
    raise HTTPException(401, "not logged in")


@router.get("/app/connect/google", response_class=HTMLResponse)
def connect_google(request: Request, session: Session = Depends(get_session)):
    """Show connect Google page."""
    client = None
    try:
        client = require_client(request, session)
    except:
        pass
    return templates.TemplateResponse("app/connect_google.html", {"request": request, "client": client})


@router.post("/app/connect/google/start")
def connect_google_start(client_id: int = 0):
    """Start OAuth flow."""
    if not client_id:
        raise HTTPException(400, "client_id required")
    url = build_auth_redirect(client_id=client_id)
    return RedirectResponse(url=url, status_code=302)


@router.get("/app/oauth/google/callback")
def google_callback(request: Request, code: str = "", state: str = "", session: Session = Depends(get_session)):
    """Handle OAuth callback."""
    if not code or not state:
        raise HTTPException(400, "missing code/state")
    
    payload = read_state(state)
    cid = int(payload["client_id"])
    
    c = session.get(Client, cid)
    if not c:
        raise HTTPException(404, "client not found")
    
    tokens = exchange_code_for_tokens(code)
    refresh_token = tokens.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(400, "no refresh_token returned")
    
    c.gbp_refresh_token = refresh_token
    session.add(c)
    session.commit()
    
    return RedirectResponse(url="/app/connect/google/choose", status_code=302)


@router.get("/app/connect/google/choose", response_class=HTMLResponse)
def choose_location(request: Request, session: Session = Depends(get_session)):
    """Show location picker."""
    # For MVP, require client_id as query param
    client_id = request.query_params.get("client_id")
    if not client_id:
        raise HTTPException(400, "client_id required")
    
    c = session.get(Client, int(client_id))
    if not c or not c.gbp_refresh_token:
        raise HTTPException(400, "google not connected")
    
    gbp = GBPClient(refresh_token=c.gbp_refresh_token)
    accounts = gbp.list_accounts()
    
    locations = []
    acct = None
    if accounts:
        acct = accounts[0].get("name")
        if acct:
            locations = gbp.list_locations(acct)
    
    return templates.TemplateResponse(
        "app/choose_location.html",
        {"request": request, "client": c, "accounts": accounts, "default_account": acct, "locations": locations}
    )


@router.post("/app/connect/google/select")
async def select_location(request: Request, session: Session = Depends(get_session)):
    """Save selected location."""
    form = await request.form()
    
    client_id = form.get("client_id")
    if not client_id:
        raise HTTPException(400, "client_id required")
    
    cid = int(client_id)
    c = session.get(Client, cid)
    if not c or not c.gbp_refresh_token:
        raise HTTPException(400, "google not connected")
    
    account_name = (form.get("account_name") or "").strip()
    location_name = (form.get("location_name") or "").strip()
    display_name = (form.get("display_name") or "").strip()
    
    if not account_name or not location_name:
        raise HTTPException(400, "missing selection")
    
    # Upsert location
    existing = session.exec(
        select(ClientLocation).where(ClientLocation.client_id == cid)
    ).first()
    
    if not existing:
        existing = ClientLocation(client_id=cid)
    
    existing.gbp_account_name = account_name
    existing.gbp_location_name = location_name
    existing.display_name = display_name
    existing.status = "active"
    
    session.add(existing)
    session.commit()
    
    return RedirectResponse(url="/app/reviews", status_code=303)
