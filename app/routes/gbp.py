import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.db import get_session
from app.routes.auth_helpers import require_user_or_redirect
from app.tenant_models import GBPCredential, AuditLog, Business
from app.services.gbp_client import (
    build_auth_url,
    exchange_code_for_tokens,
    refresh_access_token,
    encrypt_refresh_token,
    list_accounts,
    list_locations,
)

templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/app/gbp")

def audit(session: Session, business_id: int, action: str, detail: str = ""):
    session.add(AuditLog(business_id=business_id, action=action, detail=detail, created_at=datetime.utcnow()))
    session.commit()

def ensure_access_token(session: Session, business: Business) -> str:
    cred = session.exec(select(GBPCredential).where(GBPCredential.business_id == business.id)).first()
    if not cred:
        return ""
    
    # Refresh if needed
    from app.services.gbp_client import decrypt_refresh_token
    refresh_tok = decrypt_refresh_token(cred.refresh_token_enc)
    if not refresh_tok:
        return ""
    
    tok = refresh_access_token(refresh_tok)
    cred.access_token = tok.get("access_token", cred.access_token)
    expires_in = int(tok.get("expires_in", 3600))
    cred.token_expiry_utc = datetime.utcnow() + timedelta(seconds=expires_in)
    cred.updated_at = datetime.utcnow()
    session.add(cred)
    session.commit()
    return cred.access_token

@router.get("/connect")
def connect(request: Request, session: Session = Depends(get_session)):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    state = secrets.token_urlsafe(24)
    url = build_auth_url(state=state)
    resp = RedirectResponse(url, status_code=302)
    resp.set_cookie("gbp_oauth_state", state, httponly=True, samesite="lax")
    return resp

@router.get("/callback", response_class=HTMLResponse)
def callback(request: Request, code: str | None = None, state: str | None = None, session: Session = Depends(get_session)):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    expected = request.cookies.get("gbp_oauth_state", "")
    if not state or not expected or state != expected:
        audit(session, biz.id, "gbp_oauth_failed", "state_mismatch")
        return templates.TemplateResponse(
            "app/gbp_status.html",
            {"request": request, "brand": "TensorMarketData", "ok": False, "message": "OAuth state mismatch. Try again."},
        )
    
    if not code:
        audit(session, biz.id, "gbp_oauth_failed", "missing_code")
        return templates.TemplateResponse(
            "app/gbp_status.html",
            {"request": request, "brand": "TensorMarketData", "ok": False, "message": "Missing OAuth code. Try again."},
        )
    
    tokens = exchange_code_for_tokens(code)
    access_token = tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token", "")
    scope = tokens.get("scope", "")
    
    if not refresh_token:
        audit(session, biz.id, "gbp_oauth_failed", "missing_refresh_token")
        return templates.TemplateResponse(
            "app/gbp_status.html",
            {"request": request, "brand": "TensorMarketData", "ok": False, "message": "No refresh token. Reconnect and try again."},
        )
    
    cred = session.exec(select(GBPCredential).where(GBPCredential.business_id == biz.id)).first()
    if not cred:
        cred = GBPCredential(business_id=biz.id)
    
    cred.access_token = access_token
    cred.refresh_token_enc = encrypt_refresh_token(refresh_token)
    cred.scopes = scope
    cred.updated_at = datetime.utcnow()
    session.add(cred)
    session.commit()
    
    biz.gbp_connected = True
    session.add(biz)
    session.commit()
    audit(session, biz.id, "gbp_oauth_connected", f"scopes={scope}")
    
    return RedirectResponse("/app/gbp/pick-location", status_code=303)

@router.get("/pick-location", response_class=HTMLResponse)
def pick_location(request: Request, session: Session = Depends(get_session)):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    token = ensure_access_token(session, biz)
    if not token:
        return RedirectResponse("/app/settings?gbp=missing_token", status_code=303)
    
    accounts = list_accounts(token)
    return templates.TemplateResponse(
        "app/gbp_pick_account.html",
        {"request": request, "brand": "TensorMarketData", "accounts": accounts, "business": biz},
    )

@router.post("/pick-account")
def pick_account(request: Request, account_name: str = Form(...), session: Session = Depends(get_session)):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    biz.gbp_account_name = account_name
    session.add(biz)
    session.commit()
    audit(session, biz.id, "gbp_account_selected", account_name)
    return RedirectResponse("/app/gbp/pick-location-2", status_code=303)

@router.get("/pick-location-2", response_class=HTMLResponse)
def pick_location_2(request: Request, session: Session = Depends(get_session)):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    token = ensure_access_token(session, biz)
    if not token or not biz.gbp_account_name:
        return RedirectResponse("/app/gbp/pick-location", status_code=303)
    
    locations = list_locations(token, biz.gbp_account_name)
    return templates.TemplateResponse(
        "app/gbp_pick_location.html",
        {"request": request, "brand": "TensorMarketData", "locations": locations, "business": biz},
    )

@router.post("/pick-location")
def pick_location_post(
    request: Request,
    location_name: str = Form(...),
    location_title: str = Form(""),
    session: Session = Depends(get_session),
):
    user, biz, redirect = require_user_or_redirect(request, session)
    if redirect:
        return redirect
    
    biz.gbp_location_name = location_name
    biz.gbp_location_title = location_title
    biz.gbp_connected = True
    session.add(biz)
    session.commit()
    audit(session, biz.id, "gbp_location_selected", f"{location_name} | {location_title}")
    
    # Send confirmation email
    from app.services.client_onboarding import send_gbp_connected_email
    send_gbp_connected_email(biz)
    
    return RedirectResponse("/app/settings?gbp=connected", status_code=303)
